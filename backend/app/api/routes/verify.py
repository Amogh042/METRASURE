from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Report, ReportVerification
from datetime import datetime, timezone

router = APIRouter(prefix="/verify", tags=["Verification"])

@router.get("/{token}")
def verify_report(token: str, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.verification_token == token).first()
    if not report:
        raise HTTPException(status_code=404, detail="Invalid verification token or report not found")
        
    verification = db.query(ReportVerification).filter(ReportVerification.report_id == report.id).first()
    if verification:
        verification.scans_count += 1
        verification.last_scanned = datetime.now(timezone.utc)
        db.commit()
        
    return {
        "verified": True,
        "report_id": report.id,
        "report_number": report.report_number,
        "instrument": f"{report.instrument.manufacturer} {report.instrument.model}",
        "serial_number": report.instrument.serial_number,
        "test_date": report.test.test_date,
        "final_result": report.final_result,
        "generated_at": report.generated_at,
        "standard_version": "OIML R-76-1 (2006)",
        "report_status": "Official Prototype",
        "scans_count": verification.scans_count if verification else 1
    }
