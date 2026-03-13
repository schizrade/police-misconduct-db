from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text, Numeric, BigInteger, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from database import Base
import uuid

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(String(50), nullable=False, default='viewer')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime)
    created_departments = relationship("Department", back_populates="creator", foreign_keys="Department.created_by")
    created_officers    = relationship("Officer",     back_populates="creator", foreign_keys="Officer.created_by")
    created_incidents   = relationship("Incident",    back_populates="creator", foreign_keys="Incident.created_by")
    reviewed_incidents  = relationship("Incident",    back_populates="reviewer", foreign_keys="Incident.reviewed_by")

class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id    = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    action     = Column(String(50), nullable=False)
    table_name = Column(String(100), nullable=False)
    record_id  = Column(UUID(as_uuid=True))
    changes    = Column(JSONB)
    ip_address = Column(String(50))
    timestamp  = Column(DateTime, server_default=func.now())

class Department(Base):
    __tablename__ = "departments"
    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name         = Column(String(255), nullable=False)
    agency_type  = Column(String(100))
    jurisdiction = Column(String(255))
    state        = Column(String(2))
    city         = Column(String(100))
    address      = Column(Text)
    phone        = Column(String(20))
    website      = Column(String(255))
    created_at   = Column(DateTime, server_default=func.now())
    updated_at   = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by   = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    creator      = relationship("User", back_populates="created_departments", foreign_keys=[created_by])
    officers     = relationship("Officer",  back_populates="department")
    incidents    = relationship("Incident", back_populates="department")

class Officer(Base):
    __tablename__ = "officers"
    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    badge_number     = Column(String(50))
    first_name       = Column(String(100))
    last_name        = Column(String(100), nullable=False)
    department_id    = Column(UUID(as_uuid=True), ForeignKey("departments.id"))
    rank             = Column(String(100))
    hire_date        = Column(Date)
    termination_date = Column(Date)
    status           = Column(String(50), default="active")
    notes            = Column(Text)
    created_at       = Column(DateTime, server_default=func.now())
    updated_at       = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by       = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    creator          = relationship("User",       back_populates="created_officers", foreign_keys=[created_by])
    department       = relationship("Department", back_populates="officers")
    incidents        = relationship("Incident",   back_populates="officer")

class IncidentType(Base):
    __tablename__ = "incident_types"
    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name        = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    severity    = Column(String(20))
    incidents   = relationship("Incident", back_populates="incident_type")

class Incident(Base):
    __tablename__ = "incidents"
    id                 = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_date      = Column(Date, nullable=False)
    incident_type_id   = Column(UUID(as_uuid=True), ForeignKey("incident_types.id"))
    officer_id         = Column(UUID(as_uuid=True), ForeignKey("officers.id"))
    department_id      = Column(UUID(as_uuid=True), ForeignKey("departments.id"))
    location_address   = Column(Text)
    location_city      = Column(String(100))
    location_state     = Column(String(2))
    location_latitude  = Column(Numeric(10, 8))
    location_longitude = Column(Numeric(11, 8))
    description        = Column(Text, nullable=False)
    civilian_name      = Column(String(255))
    civilian_age       = Column(Integer)
    civilian_race      = Column(String(50))
    civilian_gender    = Column(String(50))
    use_of_force       = Column(Boolean, default=False)
    force_type         = Column(String(100))
    injury_occurred    = Column(Boolean, default=False)
    injury_description = Column(Text)
    death_occurred     = Column(Boolean, default=False)
    witnesses_present  = Column(Boolean)
    body_cam_footage   = Column(Boolean)
    dash_cam_footage   = Column(Boolean)
    status             = Column(String(50), default="reported")
    workflow_status    = Column(String(50), default="draft")
    is_public          = Column(Boolean, default=False)
    created_at         = Column(DateTime, server_default=func.now())
    updated_at         = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by         = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    reviewed_by        = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    review_notes       = Column(Text)
    creator       = relationship("User",         back_populates="created_incidents",  foreign_keys=[created_by])
    reviewer      = relationship("User",         back_populates="reviewed_incidents", foreign_keys=[reviewed_by])
    incident_type = relationship("IncidentType", back_populates="incidents")
    officer       = relationship("Officer",      back_populates="incidents")
    department    = relationship("Department",   back_populates="incidents")
    outcomes      = relationship("Outcome",      back_populates="incident")
    complaints    = relationship("Complaint",    back_populates="incident")
    documents     = relationship("Document",     back_populates="incident")

class Outcome(Base):
    __tablename__ = "outcomes"
    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id    = Column(UUID(as_uuid=True), ForeignKey("incidents.id"))
    outcome_date   = Column(Date)
    outcome_type   = Column(String(100))
    suspension_days= Column(Integer)
    fine_amount    = Column(Numeric(10, 2))
    details        = Column(Text)
    appealed       = Column(Boolean, default=False)
    appeal_outcome = Column(String(100))
    created_at     = Column(DateTime, server_default=func.now())
    updated_at     = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by     = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    incident       = relationship("Incident", back_populates="outcomes")

class Complaint(Base):
    __tablename__ = "complaints"
    id                           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id                  = Column(UUID(as_uuid=True), ForeignKey("incidents.id"))
    complaint_number             = Column(String(100))
    filed_date                   = Column(Date, nullable=False)
    complainant_type             = Column(String(50))
    complaint_source             = Column(String(100))
    investigation_status         = Column(String(50))
    investigation_completed_date = Column(Date)
    sustained                    = Column(Boolean)
    created_at                   = Column(DateTime, server_default=func.now())
    updated_at                   = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by                   = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    incident = relationship("Incident", back_populates="complaints")

class Document(Base):
    __tablename__ = "documents"
    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id   = Column(UUID(as_uuid=True), ForeignKey("incidents.id"))
    document_type = Column(String(100))
    file_name     = Column(String(255))
    file_path     = Column(String(500))
    file_url      = Column(String(500))
    file_size     = Column(BigInteger)
    mime_type     = Column(String(100))
    description   = Column(Text)
    upload_date   = Column(DateTime, server_default=func.now())
    is_public     = Column(Boolean, default=False)
    uploaded_by   = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    incident      = relationship("Incident", back_populates="documents")

class ImportHistory(Base):
    __tablename__ = "import_history"
    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_name        = Column(String(255))
    import_type      = Column(String(50))
    records_imported = Column(Integer, default=0)
    records_failed   = Column(Integer, default=0)
    error_log        = Column(Text)
    imported_at      = Column(DateTime, server_default=func.now())
    imported_by      = Column(UUID(as_uuid=True), ForeignKey("users.id"))
