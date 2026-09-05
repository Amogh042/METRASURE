from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.db.models import Test, User, Measurement, Instrument, RoleEnum, OIMLRule, TestResult
from app.schemas import TestCreate, TestResponse, MeasurementCreate, MeasurementResponse, TestResultResponse
from app.api.deps import get_current_active_user, require_role
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/tests", tags=["Tests"])

@router.get("/", response_model=List[TestResponse])
def get_tests(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return db.query(Test).offset(skip).limit(limit).all()

@router.post("/", response_model=TestResponse, status_code=status.HTTP_201_CREATED)
def create_test(
    test_in: TestCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.LAB_OFFICER, RoleEnum.TECHNICIAN]))
):
    inst = db.query(Instrument).filter(Instrument.id == test_in.instrument_id).first()
    if not inst: raise HTTPException(status_code=404, detail="Instrument not found")
    
    test_number = f"T-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
    db_obj = Test(
        test_number=test_number,
        instrument_id=test_in.instrument_id,
        test_type=test_in.test_type,
        technician_id=current_user.id,
        notes=test_in.notes
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.get("/{id}", response_model=TestResponse)
def get_test(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    test = db.query(Test).filter(Test.id == id).first()
    if not test: raise HTTPException(status_code=404, detail="Test not found")
    return test

@router.get("/{id}/measurements", response_model=List[MeasurementResponse])
def get_measurements(id: int, test_module: Optional[str] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    test = db.query(Test).filter(Test.id == id).first()
    if not test: raise HTTPException(status_code=404, detail="Test not found")
    query = db.query(Measurement).filter(Measurement.test_id == id)
    if test_module:
        query = query.filter(Measurement.test_module == test_module)
    return query.order_by(Measurement.sequence).all()

@router.post("/{id}/measurements", response_model=MeasurementResponse)
def add_measurement(
    id: int, 
    meas_in: MeasurementCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.LAB_OFFICER, RoleEnum.TECHNICIAN]))
):
    test = db.query(Test).filter(Test.id == id).first()
    if not test: raise HTTPException(status_code=404, detail="Test not found")
    
    db_meas = Measurement(
        test_id=id,
        test_module=meas_in.test_module,
        sequence=meas_in.sequence,
        test_load=meas_in.test_load,
        indicated_value=meas_in.indicated_value,
        unit=meas_in.unit,
        position=meas_in.position,
        repeat_number=meas_in.repeat_number
    )
    db.add(db_meas)
    test.status = "InProgress"
    db.commit()
    db.refresh(db_meas)
    return db_meas

@router.delete("/{test_id}/measurements/{meas_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_measurement(
    test_id: int, meas_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.LAB_OFFICER, RoleEnum.TECHNICIAN]))
):
    meas = db.query(Measurement).filter(Measurement.id == meas_id, Measurement.test_id == test_id).first()
    if not meas: raise HTTPException(status_code=404, detail="Measurement not found")
    db.delete(meas)
    db.commit()
    return None

@router.post("/{id}/calculate")
def calculate_test(id: int, test_module: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    from app.engine.core import calculate, RuleEngineException
    from app.db.models import OIMLRule, TestResult
    
    test = db.query(Test).filter(Test.id == id).first()
    if not test: raise HTTPException(status_code=404, detail="Test not found")
    
    inst = db.query(Instrument).filter(Instrument.id == test.instrument_id).first()
    
    measurements = db.query(Measurement).filter(Measurement.test_id == id, Measurement.test_module == test_module).order_by(Measurement.sequence).all()
    if not measurements:
        raise HTTPException(status_code=400, detail="No measurements found for this test and module.")
        
    # Convert ORM to generic dicts for the engine
    meas_dicts = []
    for m in measurements:
        meas_dicts.append({
            "sequence": m.sequence,
            "test_load": m.test_load,
            "indicated_value": m.indicated_value,
            "unit": m.unit,
            "position": m.position,
            "repeat_number": m.repeat_number
        })
        
    # Fetch applicable rule from DB (Simplified mapping for MVP)
    rule = db.query(OIMLRule).filter(
        OIMLRule.test_type == test_module,
        OIMLRule.accuracy_class == inst.accuracy_class,
        OIMLRule.enabled == True
    ).first()
    
    try:
        engine_result = calculate(test_module, inst, meas_dicts, rule)
    except RuleEngineException as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    # IMPORTANT: Delete existing TestResults for this module
    db.query(TestResult).filter(TestResult.test_id == id, TestResult.test_module == test_module).delete()
    db.commit()

    test_results = []
    
    if test_module == "Repeatability":
        calc_vals = engine_result["calculated_values"]
        tr = TestResult(
            test_id=id,
            test_module=test_module,
            measurement_id=None,
            calculated_error=calc_vals.get("max_difference", 0.0),
            permissible_error=calc_vals.get("mpe_limit", 0.0),
            result=engine_result["pass_fail"],
            explanation=engine_result.get("explanation", ""),
            rule_id=rule.id if rule else None
        )
        test_results.append(tr)
    elif test_module == "Eccentricity":
        for pos_data in engine_result["calculated_values"].get("positions", []):
            meas = db.query(Measurement).filter(Measurement.test_id == id, Measurement.test_module == test_module, Measurement.position == pos_data["position"]).first()
            if meas:
                tr = TestResult(
                    test_id=id,
                    test_module=test_module,
                    measurement_id=meas.id,
                    calculated_error=pos_data.get("error", 0.0),
                    permissible_error=pos_data.get("mpe_limit", 0.0),
                    result="PASS" if pos_data.get("passed") else "FAIL",
                    explanation="",
                    rule_id=rule.id if rule else None
                )
                test_results.append(tr)
    else: # Accuracy, Zero, Tare
        # Get all measurements for this module, ordered by sequence
        all_meas = db.query(Measurement).filter(
            Measurement.test_id == id, 
            Measurement.test_module == test_module
        ).order_by(Measurement.sequence).all()
        
        measurements_data = engine_result["calculated_values"].get("measurements", [])
        for idx, meas_data in enumerate(measurements_data):
            # Try to match by sequence key first (Accuracy), fall back to index order (Zero/Tare)
            seq = meas_data.get("sequence")
            if seq is not None:
                meas = db.query(Measurement).filter(Measurement.test_id == id, Measurement.test_module == test_module, Measurement.sequence == seq).first()
            elif idx < len(all_meas):
                meas = all_meas[idx]
            else:
                meas = None
                
            if meas:
                tr = TestResult(
                    test_id=id,
                    test_module=test_module,
                    measurement_id=meas.id,
                    calculated_error=meas_data.get("error", 0.0),
                    permissible_error=meas_data.get("mpe_limit", 0.0),
                    result="PASS" if meas_data.get("passed") else "FAIL",
                    explanation="",
                    rule_id=rule.id if rule else None
                )
                test_results.append(tr)
                
    db.add_all(test_results)
    db.commit()
    
    return engine_result

@router.get("/{id}/results", response_model=List[TestResultResponse])
def get_test_results(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    test = db.query(Test).filter(Test.id == id).first()
    if not test: raise HTTPException(status_code=404, detail="Test not found")
    
    results = db.query(TestResult).filter(TestResult.test_id == id).all()
    
    # Auto-sync overall result
    required_modules = ["Accuracy", "Repeatability", "Eccentricity", "Zero", "Tare"]
    module_status = {m: "PENDING" for m in required_modules}
    
    for r in results:
        # If any measurement in a module fails, the module fails
        if r.result == "FAIL":
            module_status[r.test_module] = "FAIL"
        elif module_status.get(r.test_module) == "PENDING":
            module_status[r.test_module] = "PASS"
            
    any_pending = any(status == "PENDING" for status in module_status.values())
    any_fail = any(status == "FAIL" for status in module_status.values())
    
    if any_fail:
        new_status = "FAIL"
    elif not any_pending:
        new_status = "PASS"
    else:
        new_status = "PENDING"
        
    if test.overall_result != new_status:
        test.overall_result = new_status
        db.commit()
        
    return results
