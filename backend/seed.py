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

def reset_database():
    print("Resetting database...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def seed_demo_data():
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
        rules = [
            OIMLRule(rule_id="R76-ACC-III-001", standard="OIML R-76-1", standard_version="2006", test_type="Accuracy", accuracy_class="III", condition="Always", formula_reference="1e", permissible_error=1.0, unit="e", source_reference="OIML R-76-1 3.5.1", notes="Standard Accuracy Test Limit"),
            OIMLRule(rule_id="R76-REP-III-001", standard="OIML R-76-1", standard_version="2006", test_type="Repeatability", accuracy_class="III", condition="Always", formula_reference="1e", permissible_error=1.0, unit="e", source_reference="OIML R-76-1 3.6.1", notes="Repeatability MPE"),
            OIMLRule(rule_id="R76-ECC-III-001", standard="OIML R-76-1", standard_version="2006", test_type="Eccentricity", accuracy_class="III", condition="Always", formula_reference="1e", permissible_error=1.0, unit="e", source_reference="OIML R-76-1 3.6.2", notes="Eccentric Loading MPE"),
            OIMLRule(rule_id="R76-ZER-III-001", standard="OIML R-76-1", standard_version="2006", test_type="Zero", accuracy_class="III", condition="Always", formula_reference="0.25e", permissible_error=0.25, unit="e", source_reference="OIML R-76-1 4.5.2", notes="Zero Indication limit"),
            OIMLRule(rule_id="R76-TAR-III-001", standard="OIML R-76-1", standard_version="2006", test_type="Tare", accuracy_class="III", condition="Always", formula_reference="1e", permissible_error=1.0, unit="e", source_reference="OIML R-76-1 4.6.1", notes="Tare Device MPE")
        ]
        db.add_all(rules)
        db.commit()

        # 3. Instruments
        print("Seeding Instruments...")
        inst1 = Instrument(instrument_id="DEMO-001", manufacturer="Mettler Toledo", model="ICS689", serial_number="SN-9821-MT", instrument_type="Non-Automatic Weighing Instrument", accuracy_class="III", max_capacity=30.0, min_capacity=0.2, verification_interval=0.01, unit="kg", owner="Global Logistics Ltd.", location="Dock 4")
        inst2 = Instrument(instrument_id="DEMO-002", manufacturer="CAS", model="DB-II", serial_number="SN-FAIL-404", instrument_type="Platform Scale", accuracy_class="III", max_capacity=150.0, min_capacity=1.0, verification_interval=0.05, unit="kg", owner="Local Produce Market", location="Warehouse B")
        
        db.add_all([inst1, inst2])
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
