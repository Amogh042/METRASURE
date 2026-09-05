import enum
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum, JSON, Boolean, Date, Text, func
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime, timezone

Base = declarative_base()

class RoleEnum(enum.Enum):
    ADMIN = "Admin"
    LAB_OFFICER = "Laboratory Officer"
    TECHNICIAN = "Technician"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Instrument(Base):
    __tablename__ = "instruments"
    id = Column(Integer, primary_key=True, index=True)
    instrument_id = Column(String, unique=True, index=True, nullable=False)
    manufacturer = Column(String, nullable=False)
    model = Column(String, nullable=False)
    serial_number = Column(String, unique=True, index=True, nullable=False)
    instrument_type = Column(String, nullable=False)
    accuracy_class = Column(String, nullable=False)
    max_capacity = Column(Float, nullable=False)
    min_capacity = Column(Float, nullable=False)
    verification_interval = Column(Float, nullable=False)
    unit = Column(String, nullable=False, default="kg")
    owner = Column(String, nullable=True)
    location = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    tests = relationship("Test", back_populates="instrument")

class Test(Base):
    __tablename__ = "tests"
    id = Column(Integer, primary_key=True, index=True)
    test_number = Column(String, unique=True, index=True, nullable=False)
    instrument_id = Column(Integer, ForeignKey("instruments.id"))
    test_type = Column(String, nullable=False)
    technician_id = Column(Integer, ForeignKey("users.id"))
    test_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(String, nullable=False, default="Pending")
    overall_result = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    instrument = relationship("Instrument", back_populates="tests")
    measurements = relationship("Measurement", back_populates="test")
    test_results = relationship("TestResult", back_populates="test")
    report = relationship("Report", back_populates="test", uselist=False)

class Measurement(Base):
    __tablename__ = "measurements"
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"))
    test_module = Column(String, nullable=False, server_default="Accuracy")
    sequence = Column(Integer, nullable=False)
    test_load = Column(Float, nullable=False)
    indicated_value = Column(Float, nullable=False)
    unit = Column(String, nullable=False, default="kg")
    position = Column(String, nullable=True)
    repeat_number = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    test = relationship("Test", back_populates="measurements")
    test_result = relationship("TestResult", back_populates="measurement", uselist=False)

class OIMLRule(Base):
    __tablename__ = "oiml_rules"
    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(String, unique=True, index=True, nullable=False)
    standard = Column(String, nullable=False)
    standard_version = Column(String, nullable=False)
    test_type = Column(String, nullable=False)
    accuracy_class = Column(String, nullable=False)
    condition = Column(String, nullable=False)
    formula_reference = Column(String, nullable=False)
    permissible_error = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    effective_date = Column(Date, nullable=True)
    source_reference = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    enabled = Column(Boolean, default=True)
    
    test_results = relationship("TestResult", back_populates="rule")
    audit_logs = relationship("RuleAuditLog", back_populates="rule", cascade="all, delete-orphan")

class RuleAuditLog(Base):
    __tablename__ = "rule_audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("oiml_rules.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    action = Column(String, nullable=False) # e.g. CREATE, UPDATE, DEACTIVATE, ACTIVATE
    previous_value = Column(Text, nullable=True) # JSON string
    new_value = Column(Text, nullable=True) # JSON string
    reason = Column(String, nullable=False)

    rule = relationship("OIMLRule", back_populates="audit_logs")
    user = relationship("User")

class TestResult(Base):
    __tablename__ = "test_results"
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"))
    test_module = Column(String, nullable=False, server_default="Accuracy")
    measurement_id = Column(Integer, ForeignKey("measurements.id"))
    calculated_error = Column(Float, nullable=False)
    permissible_error = Column(Float, nullable=False)
    result = Column(String, nullable=False) # PASS / FAIL
    explanation = Column(Text, nullable=True)
    rule_id = Column(Integer, ForeignKey("oiml_rules.id"), nullable=True)
    
    test = relationship("Test", back_populates="test_results")
    measurement = relationship("Measurement", back_populates="test_result")
    rule = relationship("OIMLRule", back_populates="test_results")

class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    report_number = Column(String, unique=True, index=True, nullable=False)
    instrument_id = Column(Integer, ForeignKey("instruments.id"))
    test_id = Column(Integer, ForeignKey("tests.id"))
    final_result = Column(String, nullable=False) # PASS / FAIL
    generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    pdf_path = Column(String, nullable=True)
    verification_token = Column(String, unique=True, index=True, nullable=False)
    
    test = relationship("Test", back_populates="report")
    instrument = relationship("Instrument")
    verification = relationship("ReportVerification", back_populates="report", uselist=False)

class ReportVerification(Base):
    __tablename__ = "report_verifications"
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"), unique=True)
    scans_count = Column(Integer, default=0)
    last_scanned = Column(DateTime, nullable=True)
    
    report = relationship("Report", back_populates="verification")
