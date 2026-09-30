from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.db.models import OIMLRule, RuleAuditLog, User, RoleEnum, TestResult
from app.schemas import OIMLRuleCreate, OIMLRuleUpdate, OIMLRuleResponse, RuleAuditLogResponse
from app.api.deps import get_current_active_user, require_role
from app.engine.core import RuleEngineException
from app.engine.conditions import parse_condition
import json

router = APIRouter(prefix="/rules", tags=["Rules Config"])

def validate_condition(condition: str):
    try:
        parse_condition(condition)
    except RuleEngineException as e:
        raise HTTPException(status_code=400, detail=str(e))

def get_rule_json(rule: OIMLRule):
    return json.dumps({
        "rule_id": rule.rule_id,
        "standard": rule.standard,
        "standard_version": rule.standard_version,
        "test_type": rule.test_type,
        "accuracy_class": rule.accuracy_class,
        "condition": rule.condition,
        "formula_reference": rule.formula_reference,
        "permissible_error": rule.permissible_error,
        "unit": rule.unit,
        "effective_date": str(rule.effective_date) if rule.effective_date else None,
        "source_reference": rule.source_reference,
        "notes": rule.notes,
        "enabled": rule.enabled
    })

@router.get("/", response_model=List[OIMLRuleResponse])
def get_all_rules(db: Session = Depends(get_db), current_user: User = Depends(require_role([RoleEnum.ADMIN]))):
    return db.query(OIMLRule).all()

@router.get("/{id}", response_model=OIMLRuleResponse)
def get_rule(id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role([RoleEnum.ADMIN]))):
    rule = db.query(OIMLRule).filter(OIMLRule.id == id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule

@router.get("/{id}/audit", response_model=List[RuleAuditLogResponse])
def get_rule_audit_logs(id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role([RoleEnum.ADMIN]))):
    return db.query(RuleAuditLog).filter(RuleAuditLog.rule_id == id).order_by(RuleAuditLog.timestamp.desc()).all()

@router.post("/", response_model=OIMLRuleResponse, status_code=status.HTTP_201_CREATED)
def create_rule(
    rule_in: OIMLRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN]))
):
    if db.query(OIMLRule).filter(OIMLRule.rule_id == rule_in.rule_id).first():
        raise HTTPException(status_code=400, detail="Rule ID already exists")
    validate_condition(rule_in.condition)

    rule_data = rule_in.model_dump(exclude={"reason"})
    new_rule = OIMLRule(**rule_data)
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)

    # Audit Log
    log = RuleAuditLog(
        rule_id=new_rule.id,
        user_id=current_user.id,
        action="CREATE",
        previous_value=None,
        new_value=get_rule_json(new_rule),
        reason=rule_in.reason
    )
    db.add(log)
    db.commit()

    return new_rule

@router.put("/{id}", response_model=OIMLRuleResponse)
def update_rule(
    id: int,
    rule_in: OIMLRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN]))
):
    rule = db.query(OIMLRule).filter(OIMLRule.id == id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    # If they are changing core values (not just disabling), we must ensure it hasn't been used.
    # Actually, the requirement says: "Do not allow an Admin to delete a rule that has already been used in historical tests. Use versioning/deactivation instead."
    # If they modify a rule in place, they corrupt history. We should block edits of core parameters if used.
    # Exception: toggling `enabled` or changing `notes` is fine.
    
    is_used = db.query(TestResult).filter(TestResult.rule_id == id).first() is not None
    
    update_data = rule_in.model_dump(exclude={"reason"}, exclude_unset=True)
    if "condition" in update_data:
        validate_condition(update_data["condition"])
    
    core_fields_changed = any(k not in ["enabled", "notes"] for k in update_data.keys())
    
    if is_used and core_fields_changed:
        raise HTTPException(
            status_code=400, 
            detail="This rule has been used in historical tests and cannot be modified. Deactivate it and create a new version instead."
        )

    prev_val = get_rule_json(rule)
    
    for key, value in update_data.items():
        setattr(rule, key, value)
        
    db.commit()
    db.refresh(rule)
    
    new_val = get_rule_json(rule)
    
    # Audit Log
    log = RuleAuditLog(
        rule_id=rule.id,
        user_id=current_user.id,
        action="UPDATE",
        previous_value=prev_val,
        new_value=new_val,
        reason=rule_in.reason
    )
    db.add(log)
    db.commit()
    
    return rule

@router.delete("/{id}")
def delete_rule(id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role([RoleEnum.ADMIN]))):
    rule = db.query(OIMLRule).filter(OIMLRule.id == id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
        
    is_used = db.query(TestResult).filter(TestResult.rule_id == id).first() is not None
    if is_used:
        raise HTTPException(
            status_code=400, 
            detail="Rule has been used in historical tests and cannot be deleted. Use deactivation."
        )
        
    db.delete(rule)
    db.commit()
    return {"detail": "Rule deleted"}
