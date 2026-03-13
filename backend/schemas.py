from pydantic import BaseModel, UUID4, EmailStr
from datetime import date, datetime
from typing import Optional, List
from decimal import Decimal

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role: str = 'viewer'

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: UUID4
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    class Config:
        from_attributes = True

class DepartmentBase(BaseModel):
    name: str
    agency_type: Optional[str] = None
    jurisdiction: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None

class DepartmentCreate(DepartmentBase):
    pass

class Department(DepartmentBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class OfficerBase(BaseModel):
    badge_number: Optional[str] = None
    first_name: Optional[str] = None
    last_name: str
    department_id: Optional[UUID4] = None
    rank: Optional[str] = None
    hire_date: Optional[date] = None
    termination_date: Optional[date] = None
    status: str = "active"
    notes: Optional[str] = None

class OfficerCreate(OfficerBase):
    pass

class Officer(OfficerBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class IncidentTypeBase(BaseModel):
    name: str
    description: Optional[str] = None
    severity: Optional[str] = None

class IncidentType(IncidentTypeBase):
    id: UUID4
    class Config:
        from_attributes = True

class IncidentBase(BaseModel):
    incident_date: date
    incident_type_id: Optional[UUID4] = None
    officer_id: Optional[UUID4] = None
    department_id: Optional[UUID4] = None
    location_address: Optional[str] = None
    location_city: Optional[str] = None
    location_state: Optional[str] = None
    location_latitude: Optional[Decimal] = None
    location_longitude: Optional[Decimal] = None
    description: str
    civilian_name: Optional[str] = None
    civilian_age: Optional[int] = None
    civilian_race: Optional[str] = None
    civilian_gender: Optional[str] = None
    use_of_force: bool = False
    force_type: Optional[str] = None
    injury_occurred: bool = False
    injury_description: Optional[str] = None
    death_occurred: bool = False
    witnesses_present: Optional[bool] = None
    body_cam_footage: Optional[bool] = None
    dash_cam_footage: Optional[bool] = None
    status: str = "reported"
    workflow_status: str = "draft"
    is_public: bool = False

class IncidentCreate(IncidentBase):
    pass

class Incident(IncidentBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID4] = None
    reviewed_by: Optional[UUID4] = None
    review_notes: Optional[str] = None
    class Config:
        from_attributes = True

class OutcomeBase(BaseModel):
    incident_id: UUID4
    outcome_date: Optional[date] = None
    outcome_type: Optional[str] = None
    suspension_days: Optional[int] = None
    fine_amount: Optional[Decimal] = None
    details: Optional[str] = None
    appealed: bool = False
    appeal_outcome: Optional[str] = None

class OutcomeCreate(OutcomeBase):
    pass

class Outcome(OutcomeBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class ComplaintBase(BaseModel):
    incident_id: UUID4
    complaint_number: Optional[str] = None
    filed_date: date
    complainant_type: Optional[str] = None
    complaint_source: Optional[str] = None
    investigation_status: Optional[str] = None
    investigation_completed_date: Optional[date] = None
    sustained: Optional[bool] = None

class ComplaintCreate(ComplaintBase):
    pass

class Complaint(ComplaintBase):
    id: UUID4
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class Document(BaseModel):
    id: UUID4
    incident_id: UUID4
    document_type: str
    file_name: str
    file_url: str
    file_size: int
    mime_type: Optional[str]
    description: Optional[str]
    is_public: bool
    upload_date: datetime
    class Config:
        from_attributes = True

class ImportHistory(BaseModel):
    id: UUID4
    file_name: str
    import_type: str
    records_imported: int
    records_failed: int
    error_log: Optional[str]
    imported_at: datetime
    class Config:
        from_attributes = True

class IncidentStats(BaseModel):
    total_incidents: int
    incidents_by_type: dict
    incidents_by_department: dict
    incidents_by_year: dict
    use_of_force_incidents: int
    death_incidents: int
    average_outcome_severity: Optional[float] = None

class OfficerStats(BaseModel):
    total_officers: int
    active_officers: int
    officers_with_incidents: int
    average_incidents_per_officer: float
