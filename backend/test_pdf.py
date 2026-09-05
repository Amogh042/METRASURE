from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import Report, Test, Instrument, User, TestResult
from app.services.pdf_generator import generate_report_pdf

db = SessionLocal()
report = db.query(Report).first()
test = db.query(Test).filter(Test.id == report.test_id).first()
inst = db.query(Instrument).filter(Instrument.id == test.instrument_id).first()
tech = db.query(User).filter(User.id == test.technician_id).first()
results = db.query(TestResult).filter(TestResult.test_id == test.id).all()

path = generate_report_pdf(report, test, inst, tech, results)
print("Generated PDF at:", path)
