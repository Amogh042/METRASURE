from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_
from typing import List, Optional
from datetime import datetime, timedelta

from app.db.database import get_db
from app.db.models import Test, Instrument, User, TestResult, Report
from app.api.deps import get_current_active_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats")
def get_dashboard_stats(
    days: Optional[int] = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    date_threshold = datetime.utcnow() - timedelta(days=days)

    # Overview Cards
    total_instruments = db.query(Instrument).count()
    total_tests = db.query(Test).filter(Test.test_date >= date_threshold).count()
    passed_tests = db.query(Test).filter(Test.overall_result == "PASS", Test.test_date >= date_threshold).count()
    failed_tests = db.query(Test).filter(Test.overall_result == "FAIL", Test.test_date >= date_threshold).count()
    total_reports = db.query(Report).count()

    # Recent Tests
    recent_tests_query = db.query(
        Test.id, 
        Test.test_number, 
        Test.test_date, 
        Test.overall_result,
        Instrument.manufacturer,
        Instrument.model,
        Instrument.serial_number,
        User.username.label("technician")
    ).join(Instrument, Test.instrument_id == Instrument.id)\
     .join(User, Test.technician_id == User.id)\
     .order_by(desc(Test.test_date))\
     .limit(10).all()
     
    recent_tests = [
        {
            "id": r.id,
            "test_number": r.test_number,
            "test_date": r.test_date,
            "overall_result": r.overall_result or "PENDING",
            "instrument": f"{r.manufacturer} {r.model}",
            "serial_number": r.serial_number,
            "technician": r.technician
        }
        for r in recent_tests_query
    ]

    # Failure Analysis (Chart)
    # Count of FAIL results grouped by test_module
    failed_results = db.query(
        TestResult.test_module, func.count(TestResult.id)
    ).filter(
        TestResult.result == "FAIL"
    ).group_by(TestResult.test_module).all()
    
    # Initialize all modules to 0
    failure_analysis = [
        {"name": "Accuracy", "failures": 0},
        {"name": "Repeatability", "failures": 0},
        {"name": "Eccentricity", "failures": 0},
        {"name": "Zero", "failures": 0},
        {"name": "Tare", "failures": 0}
    ]
    
    for mod, count in failed_results:
        for f in failure_analysis:
            if f["name"] == mod:
                f["failures"] = count

    # Instruments Requiring Attention
    # E.g., latest test was a FAIL, or overdue
    # We will pick instruments whose latest test is FAIL
    subquery = db.query(
        Test.instrument_id, func.max(Test.test_date).label('max_date')
    ).group_by(Test.instrument_id).subquery()
    
    attention_query = db.query(Instrument, Test.overall_result).join(
        Test, Test.instrument_id == Instrument.id
    ).join(
        subquery, (Test.instrument_id == subquery.c.instrument_id) & (Test.test_date == subquery.c.max_date)
    ).filter(
        or_(Test.overall_result == "FAIL", Test.overall_result == "PENDING")
    ).limit(5).all()
    
    attention = [
        {
            "id": inst.id,
            "instrument": f"{inst.manufacturer} {inst.model}",
            "serial_number": inst.serial_number,
            "status": result or "PENDING"
        }
        for inst, result in attention_query
    ]

    return {
        "overview": {
            "instruments_registered": total_instruments,
            "tests_completed": total_tests,
            "tests_passed": passed_tests,
            "tests_failed": failed_tests,
            "reports_generated": total_reports
        },
        "recent_tests": recent_tests,
        "failure_analysis": failure_analysis,
        "attention_required": attention
    }
