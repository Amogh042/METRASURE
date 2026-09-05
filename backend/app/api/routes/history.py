from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from typing import List, Optional
from datetime import datetime
from app.db.database import get_db
from app.db.models import Instrument, Test, User, TestResult, Report, Measurement, OIMLRule

router = APIRouter(prefix="/history", tags=["History"])

@router.get("/search")
def search_history(
    q: Optional[str] = None,
    accuracy_class: Optional[str] = None,
    result: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    test_type: Optional[str] = None,
    instrument_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(
        Test.id, Test.test_number, Test.test_date, Test.test_type, Test.overall_result,
        Instrument.id.label("inst_id"), Instrument.instrument_id, Instrument.manufacturer, Instrument.model, Instrument.serial_number, Instrument.accuracy_class,
        User.username.label("technician_name"),
        Report.id.label("report_id")
    ).join(Instrument, Test.instrument_id == Instrument.id)\
     .join(User, Test.technician_id == User.id)\
     .outerjoin(Report, Test.id == Report.test_id)
     
    if instrument_id:
        query = query.filter(Test.instrument_id == instrument_id)

    if q:
        search_str = f"%{q}%"
        query = query.filter(
            or_(
                Instrument.serial_number.ilike(search_str),
                Instrument.manufacturer.ilike(search_str),
                Instrument.model.ilike(search_str),
                Instrument.instrument_id.ilike(search_str)
            )
        )
        
    if accuracy_class:
        query = query.filter(Instrument.accuracy_class == accuracy_class)
        
    if result:
        query = query.filter(Test.overall_result == result)
        
    if test_type:
        query = query.filter(Test.test_type == test_type)
        
    if start_date:
        query = query.filter(Test.test_date >= start_date)
        
    if end_date:
        query = query.filter(Test.test_date <= end_date)
        
    query = query.order_by(desc(Test.test_date)).offset(skip).limit(limit)
    results = query.all()
    
    return [
        {
            "test_id": r.id,
            "test_number": r.test_number,
            "test_date": r.test_date,
            "test_type": r.test_type,
            "overall_result": r.overall_result,
            "instrument": {
                "id": r.inst_id,
                "instrument_id": r.instrument_id,
                "manufacturer": r.manufacturer,
                "model": r.model,
                "serial_number": r.serial_number,
                "accuracy_class": r.accuracy_class
            },
            "technician": r.technician_name,
            "report_id": r.report_id
        }
        for r in results
    ]

@router.get("/instrument/{id}/stats")
def get_instrument_history_stats(id: int, db: Session = Depends(get_db)):
    inst = db.query(Instrument).filter(Instrument.id == id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Instrument not found")
        
    tests = db.query(Test).filter(Test.instrument_id == id).order_by(desc(Test.test_date)).all()
    total_tests = len(tests)
    pass_count = sum(1 for t in tests if t.overall_result == "PASS")
    fail_count = sum(1 for t in tests if t.overall_result == "FAIL")
    
    last_test = tests[0] if tests else None
    
    return {
        "instrument": inst,
        "stats": {
            "total_tests": total_tests,
            "pass_count": pass_count,
            "fail_count": fail_count,
            "last_test_date": last_test.test_date if last_test else None,
            "last_result": last_test.overall_result if last_test else None
        }
    }

@router.get("/test/{test_id}/details")
def get_historical_test_details(test_id: int, db: Session = Depends(get_db)):
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
        
    # Get all results with rules
    results_query = db.query(TestResult, OIMLRule).outerjoin(OIMLRule, TestResult.rule_id == OIMLRule.id).filter(TestResult.test_id == test_id).all()
    
    # Get all measurements to attach them
    measurements = db.query(Measurement).filter(Measurement.test_id == test_id).all()
    meas_map = {m.id: m for m in measurements}
    
    details = []
    for res, rule in results_query:
        meas = meas_map.get(res.measurement_id) if res.measurement_id else None
        
        details.append({
            "test_module": res.test_module,
            "measurement": meas,
            "calculations": {
                "calculated_error": res.calculated_error,
                "permissible_error": res.permissible_error,
            },
            "rule_used": rule,
            "result": res.result,
            "explanation": res.explanation
        })
        
    return {
        "test": test,
        "details": details
    }

@router.get("/test/{test_id}/ai-explanation")
async def get_test_ai_explanation(test_id: int, db: Session = Depends(get_db)):
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
        
    # Get all results with rules
    results_query = db.query(TestResult).filter(TestResult.test_id == test_id).all()
    measurements = db.query(Measurement).filter(Measurement.test_id == test_id).all()
    meas_map = {m.id: m for m in measurements}
    
    details = []
    for res in results_query:
        meas = meas_map.get(res.measurement_id) if res.measurement_id else None
        details.append({
            "test_module": res.test_module,
            "measurement": meas,
            "calculations": {
                "calculated_error": res.calculated_error,
                "permissible_error": res.permissible_error,
            },
            "result": res.result
        })
        
    from app.services.ai_explainer import AIExplainer
    explainer = AIExplainer()
    explanation = await explainer.explain(test, details)
    
    if not explanation:
        return {"explanation": None, "status": "unavailable"}
        
    return {"explanation": explanation, "status": "success"}
