import asyncio
import os
import shutil
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine
from app.db.models import Base, User, RoleEnum, Instrument, Test, Measurement, TestResult, OIMLRule
from passlib.context import CryptContext
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

# OIML R-76-1 (2006) Table 6: MPEs on initial verification, as (MPE in e, condition on m = load / e) per class
TABLE_6_BANDS = {
    "I":    [(0.5, "0<=m<=50000e"), (1.0, "50000e<m<=200000e"), (1.5, "200000e<m")],
    "II":   [(0.5, "0<=m<=5000e"),  (1.0, "5000e<m<=20000e"),   (1.5, "20000e<m<=100000e")],
    "III":  [(0.5, "0<=m<=500e"),   (1.0, "500e<m<=2000e"),     (1.5, "2000e<m<=10000e")],
    "IIII": [(0.5, "0<=m<=50e"),    (1.0, "50e<m<=200e"),       (1.5, "200e<m<=1000e")],
}
BANDED_TESTS = {"Accuracy": "ACC", "Repeatability": "REP", "Eccentricity": "ECC", "Tare": "TAR"}

def build_table6_rules():
    """One rule per (test, class, Table 6 band), plus a flat 0.25e Zero rule per class."""
    rules = []
    for cls, bands in TABLE_6_BANDS.items():
        for test_type, code in BANDED_TESTS.items():
            for n, (mpe, condition) in enumerate(bands, start=1):
                rules.append(OIMLRule(
                    rule_id=f"R76-{code}-{cls}-{n:03d}", standard="OIML R-76-1", standard_version="2006",
                    test_type=test_type, accuracy_class=cls, condition=condition,
                    formula_reference=f"{mpe:g}e", permissible_error=mpe, unit="e",
                    source_reference="OIML R-76-1 (2006) Table 6",
                    notes=f"Initial verification MPE ±{mpe:g}e for {condition}",
                ))
        rules.append(OIMLRule(
            rule_id=f"R76-ZER-{cls}-001", standard="OIML R-76-1", standard_version="2006",
            test_type="Zero", accuracy_class=cls, condition="Always",
            formula_reference="0.25e", permissible_error=0.25, unit="e",
            source_reference="OIML R-76-1 (2006) 4.5.2", notes="Zero-setting accuracy ±0.25e",
        ))
    return rules

def reset_database():
    """Drops and recreates all tables. Only used by `python seed.py` (full reset)."""
    print("Resetting database...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def seed_demo_data():
    """Inserts demo data into the existing tables without dropping anything (safe to import and call on startup)."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 1. Users
        print("Seeding Users...")
        admin = User(username="admin", email="admin@metrasure.gov.in", role=RoleEnum.ADMIN, hashed_password=get_password_hash("admin123"))
        officer = User(username="officer", email="officer@metrasure.gov.in", role=RoleEnum.LAB_OFFICER, hashed_password=get_password_hash("officer123"))
        tech = User(username="tech", email="tech@metrasure.gov.in", role=RoleEnum.TECHNICIAN, hashed_password=get_password_hash("tech123"))
        
        db.add_all([admin, officer, tech])
        db.commit()

        # 2. OIML Rules
        print("Seeding OIML Rules...")
        rules = build_table6_rules()
        db.add_all(rules)
        db.commit()

        # 3. Instruments
        print("Seeding Instruments...")
        inst1 = Instrument(instrument_id="DEMO-001", manufacturer="Mettler Toledo", model="ICS689", serial_number="SN-9821-MT", instrument_type="Non-Automatic Weighing Instrument", accuracy_class="III", max_capacity=30.0, min_capacity=0.2, verification_interval=0.01, unit="kg", owner="Global Logistics Ltd.", location="Dock 4")
        inst2 = Instrument(instrument_id="DEMO-002", manufacturer="CAS", model="DB-II", serial_number="SN-FAIL-404", instrument_type="Platform Scale", accuracy_class="III", max_capacity=150.0, min_capacity=1.0, verification_interval=0.05, unit="kg", owner="Local Produce Market", location="Warehouse B")
        inst3 = Instrument(instrument_id="DEMO-003", manufacturer="Demo Precision Instruments", model="DPB-6K", serial_number="SN-II-6000", instrument_type="Precision Balance", accuracy_class="II", max_capacity=6.0, min_capacity=0.05, verification_interval=0.001, unit="kg", owner="State Legal Metrology Lab", location="Precision Room")
        
        db.add_all([inst1, inst2, inst3])
        db.commit()
        db.refresh(inst1)
        db.refresh(inst2)

        # We will not pre-fill any FAILED test for DEMO-002. 
        # The prompt says: "Create two seeded demo instruments: DEMO-001: All tests PASS, DEMO-002: At least one test FAILS. Make the failure easy to demonstrate..."
        # Wait, if I'm pre-seeding the data, the user during the live demo will *run* the test? 
        # "Select existing instrument -> Start Accuracy Test -> Enter measurements -> Calculate"
        # The user will ENTER the measurements during the demo. I don't need to pre-seed the exact failed test, I just need to give them the credentials and the instruments, and they will run it!
        # Actually, let me pre-seed some historical tests for the dashboard metrics, but leave DEMO-001 and DEMO-002 ready for testing.
        
        print("Seeding historical tests for Dashboard...")
        now = datetime.now(timezone.utc)
        
        import random
        for i in range(15):
            test = Test(
                test_number=f"T-HIST-{i+1000}",
                instrument_id=inst1.id if i % 2 == 0 else inst2.id,
                test_type="Full Calibration",
                technician_id=tech.id,
                test_date=now - timedelta(days=random.randint(1, 30)),
                overall_result="PASS" if i % 3 != 0 else "FAIL"
            )
            db.add(test)
        db.commit()
        
        print("Database successfully seeded for SIH Demo!")
    except Exception as e:
        print(f"Error seeding DB: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_database()
    seed_demo_data()
