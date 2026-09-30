from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.db.models import RoleEnum

class UserBase(BaseModel):
    username: str
    email: str
    role: RoleEnum

class UserResponse(UserBase):
    id: int
    created_at: datetime
    class Config: from_attributes = True

class InstrumentBase(BaseModel):
    instrument_id: str
    manufacturer: str
    model: str
    serial_number: str
    instrument_type: str
    accuracy_class: str
    max_capacity: float
    min_capacity: float
    verification_interval: float
    unit: str
    owner: Optional[str] = None
    location: Optional[str] = None

class InstrumentCreate(InstrumentBase): pass

class InstrumentUpdate(BaseModel):
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    instrument_type: Optional[str] = None
    accuracy_class: Optional[str] = None
    max_capacity: Optional[float] = None
    min_capacity: Optional[float] = None
    verification_interval: Optional[float] = None
    unit: Optional[str] = None
    owner: Optional[str] = None
    location: Optional[str] = None

class InstrumentResponse(InstrumentBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config: from_attributes = True

class MeasurementBase(BaseModel):
    test_module: str = "Accuracy"
    sequence: int
    test_load: float
    indicated_value: float
    unit: str
    position: Optional[str] = None
    repeat_number: Optional[int] = None

class MeasurementCreate(MeasurementBase): pass

class MeasurementResponse(MeasurementBase):
    id: int
    test_id: int
    timestamp: datetime
    class Config: from_attributes = True

class TestBase(BaseModel):
    test_number: str
    instrument_id: int
    test_type: str
    technician_id: int
    notes: Optional[str] = None

class TestCreate(BaseModel):
    instrument_id: int
    test_type: str
    notes: Optional[str] = None

class TestResponse(TestBase):
    id: int
    test_date: datetime
    status: str
    overall_result: Optional[str] = None
    created_at: datetime
    class Config: from_attributes = True

class TestResultResponse(BaseModel):
    id: int
    test_id: int
    test_module: str
    measurement_id: Optional[int] = None
    calculated_error: float
    permissible_error: float
    result: str
    explanation: Optional[str] = None
    rule_id: Optional[int] = None
    class Config: from_attributes = True

class ReportBase(BaseModel):
    report_number: str
    instrument_id: int
    test_id: int
    final_result: str
    pdf_path: Optional[str] = None
    verification_token: str

class ReportResponse(ReportBase):
    id: int
    generated_at: datetime
    class Config: from_attributes = True

class OIMLRuleBase(BaseModel):
    rule_id: str
    standard: str
    standard_version: str
    test_type: str
    accuracy_class: str
    condition: str
    formula_reference: str
    permissible_error: float
    unit: str
    effective_date: Optional[datetime] = None
    source_reference: Optional[str] = None
    notes: Optional[str] = None
    enabled: bool = True

class OIMLRuleCreate(OIMLRuleBase):
    reason: str # For audit log

class OIMLRuleUpdate(BaseModel):
    rule_id: Optional[str] = None
    standard: Optional[str] = None
    standard_version: Optional[str] = None
    test_type: Optional[str] = None
    accuracy_class: Optional[str] = None
    condition: Optional[str] = None
    formula_reference: Optional[str] = None
    permissible_error: Optional[float] = None
    unit: Optional[str] = None
    effective_date: Optional[datetime] = None
    source_reference: Optional[str] = None
    notes: Optional[str] = None
    enabled: Optional[bool] = None
    reason: str # For audit log

class OIMLRuleResponse(OIMLRuleBase):
    id: int
    class Config: from_attributes = True

class RuleAuditLogResponse(BaseModel):
    id: int
    rule_id: int
    user_id: int
    timestamp: datetime
    action: str
    previous_value: Optional[str] = None
    new_value: Optional[str] = None
    reason: str
    user: Optional[UserResponse] = None
    class Config: from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
