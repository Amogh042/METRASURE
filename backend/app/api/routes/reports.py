from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.db.models import Report, User, RoleEnum, ReportVerification, Test, Instrument
from app.schemas import ReportResponse, ReportBase
from app.api.deps import get_current_active_user, require_role
import uuid
from datetime import datetime

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/", response_model=List[ReportResponse])
def get_reports(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return db.query(Report).offset(skip).limit(limit).all()

@router.get("/{id}", response_model=ReportResponse)
def get_report(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    report = db.query(Report).filter(Report.id == id).first()
    if not report: raise HTTPException(status_code=404, detail="Report not found")
    return report

@router.post("/{test_id}/generate", response_model=ReportResponse)
def generate_report(
    test_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.LAB_OFFICER, RoleEnum.TECHNICIAN]))
):
    from app.db.models import TestResult
    from app.services.pdf_generator import generate_report_pdf
    import os

    test = db.query(Test).filter(Test.id == test_id).first()
    if not test: raise HTTPException(status_code=404, detail="Test not found")
    
    inst = db.query(Instrument).filter(Instrument.id == test.instrument_id).first()
    tech = db.query(User).filter(User.id == test.technician_id).first()
    
    existing = db.query(Report).filter(Report.test_id == test_id).first()
    if existing:
        if not existing.pdf_path or not os.path.exists(existing.pdf_path):
            results = db.query(TestResult).filter(TestResult.test_id == test_id).all()
            existing.pdf_path = generate_report_pdf(existing, test, inst, tech, results)
            db.commit()
        return existing
    
    report_num = f"REP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    token = uuid.uuid4().hex
    
    db_report = Report(
        report_number=report_num,
        instrument_id=test.instrument_id,
        test_id=test_id,
        final_result=test.overall_result or "PENDING",
        verification_token=token
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    
    db_verification = ReportVerification(report_id=db_report.id)
    db.add(db_verification)
    db.commit()

    # Generate PDF
    results = db.query(TestResult).filter(TestResult.test_id == test_id).all()
    pdf_path = generate_report_pdf(db_report, test, inst, tech, results)
    
    db_report.pdf_path = pdf_path
    db.commit()
    db.refresh(db_report)
    
    return db_report

from fastapi.responses import FileResponse

@router.get("/{id}/download")
def download_report(id: int, db: Session = Depends(get_db)):
    # Making download public so it can be opened easily, or we can restrict it.
    report = db.query(Report).filter(Report.id == id).first()
    if not report or not report.pdf_path: raise HTTPException(status_code=404, detail="Report PDF not found")
    import os
    if not os.path.exists(report.pdf_path): raise HTTPException(status_code=404, detail="File missing on server")
    return FileResponse(report.pdf_path, media_type='application/pdf', filename=f"{report.report_number}.pdf")
