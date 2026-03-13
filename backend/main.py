from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import List, Optional
from datetime import date, datetime, timedelta
from pathlib import Path
import pandas as pd
import io
import uuid
import shutil

import models
import schemas
from database import engine, get_db, settings
from auth import (
    authenticate_user, create_access_token, get_current_active_user,
    get_password_hash, Token, require_data_entry, require_admin
)

models.Base.metadata.create_all(bind=engine)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="Police Misconduct Database API",
    description="Tracking and analyzing police misconduct incidents",
    version="2.0.0"
)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

origins = settings.allowed_origins.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Auth ──────────────────────────────────────────────────────────────────────

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect username or password",
                            headers={"WWW-Authenticate": "Bearer"})
    user.last_login = datetime.utcnow()
    db.commit()
    expires = timedelta(minutes=settings.access_token_expire_minutes)
    token = create_access_token(data={"sub": user.username}, expires_delta=expires)
    return {"access_token": token, "token_type": "bearer"}

@app.post("/register", response_model=schemas.User)
async def register_user(user: schemas.UserCreate, db: Session = Depends(get_db),
                        current_user: models.User = Depends(require_admin)):
    if db.query(models.User).filter(models.User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user = models.User(username=user.username, email=user.email,
                          hashed_password=get_password_hash(user.password),
                          full_name=user.full_name, role=user.role)
    db.add(db_user); db.commit(); db.refresh(db_user)
    return db_user

@app.get("/users/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(get_current_active_user)):
    return current_user

@app.get("/users", response_model=List[schemas.User])
async def list_users(db: Session = Depends(get_db),
                     current_user: models.User = Depends(require_admin)):
    return db.query(models.User).all()

# ── Departments ───────────────────────────────────────────────────────────────

@app.get("/departments", response_model=List[schemas.Department])
def get_departments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Department).offset(skip).limit(limit).all()

@app.post("/departments", response_model=schemas.Department)
def create_department(department: schemas.DepartmentCreate, db: Session = Depends(get_db),
                      current_user: models.User = Depends(require_data_entry)):
    obj = models.Department(**department.model_dump(), created_by=current_user.id)
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

@app.get("/departments/{department_id}", response_model=schemas.Department)
def get_department(department_id: str, db: Session = Depends(get_db)):
    obj = db.query(models.Department).filter(models.Department.id == department_id).first()
    if not obj: raise HTTPException(status_code=404, detail="Department not found")
    return obj

# ── Officers ──────────────────────────────────────────────────────────────────

@app.get("/officers", response_model=List[schemas.Officer])
def get_officers(skip: int = 0, limit: int = 100,
                 department_id: Optional[str] = None, status: Optional[str] = None,
                 db: Session = Depends(get_db)):
    q = db.query(models.Officer)
    if department_id: q = q.filter(models.Officer.department_id == department_id)
    if status:        q = q.filter(models.Officer.status == status)
    return q.offset(skip).limit(limit).all()

@app.post("/officers", response_model=schemas.Officer)
def create_officer(officer: schemas.OfficerCreate, db: Session = Depends(get_db),
                   current_user: models.User = Depends(require_data_entry)):
    obj = models.Officer(**officer.model_dump(), created_by=current_user.id)
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

@app.get("/officers/{officer_id}", response_model=schemas.Officer)
def get_officer(officer_id: str, db: Session = Depends(get_db)):
    obj = db.query(models.Officer).filter(models.Officer.id == officer_id).first()
    if not obj: raise HTTPException(status_code=404, detail="Officer not found")
    return obj

# ── Incident Types ────────────────────────────────────────────────────────────

@app.get("/incident-types", response_model=List[schemas.IncidentType])
def get_incident_types(db: Session = Depends(get_db)):
    return db.query(models.IncidentType).all()

# ── Incidents ─────────────────────────────────────────────────────────────────

@app.get("/incidents", response_model=List[schemas.Incident])
def search_incidents(
    query: Optional[str] = None,
    start_date: Optional[date] = None, end_date: Optional[date] = None,
    department_id: Optional[str] = None, officer_id: Optional[str] = None,
    incident_type_id: Optional[str] = None,
    location_city: Optional[str] = None, location_state: Optional[str] = None,
    use_of_force: Optional[bool] = None, death_occurred: Optional[bool] = None,
    status: Optional[str] = None, workflow_status: Optional[str] = None,
    skip: int = 0, limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_active_user)
):
    q = db.query(models.Incident)
    if not current_user or current_user.role == 'viewer':
        q = q.filter(models.Incident.is_public == True)
    if query:            q = q.filter(models.Incident.description.ilike(f"%{query}%"))
    if start_date:       q = q.filter(models.Incident.incident_date >= start_date)
    if end_date:         q = q.filter(models.Incident.incident_date <= end_date)
    if department_id:    q = q.filter(models.Incident.department_id == department_id)
    if officer_id:       q = q.filter(models.Incident.officer_id == officer_id)
    if incident_type_id: q = q.filter(models.Incident.incident_type_id == incident_type_id)
    if location_city:    q = q.filter(models.Incident.location_city.ilike(f"%{location_city}%"))
    if location_state:   q = q.filter(models.Incident.location_state == location_state)
    if use_of_force  is not None: q = q.filter(models.Incident.use_of_force  == use_of_force)
    if death_occurred is not None: q = q.filter(models.Incident.death_occurred == death_occurred)
    if status:           q = q.filter(models.Incident.status == status)
    if workflow_status:  q = q.filter(models.Incident.workflow_status == workflow_status)
    return q.order_by(models.Incident.incident_date.desc()).offset(skip).limit(limit).all()

@app.post("/incidents", response_model=schemas.Incident)
def create_incident(incident: schemas.IncidentCreate, db: Session = Depends(get_db),
                    current_user: models.User = Depends(require_data_entry)):
    obj = models.Incident(**incident.model_dump(), created_by=current_user.id)
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

@app.get("/incidents/{incident_id}", response_model=schemas.Incident)
def get_incident(incident_id: str, db: Session = Depends(get_db),
                 current_user: Optional[models.User] = Depends(get_current_active_user)):
    obj = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not obj: raise HTTPException(status_code=404, detail="Incident not found")
    if not obj.is_public and (not current_user or current_user.role == 'viewer'):
        raise HTTPException(status_code=403, detail="Access denied")
    return obj

@app.put("/incidents/{incident_id}/workflow", response_model=schemas.Incident)
def update_incident_workflow(incident_id: str, workflow_status: str,
                             review_notes: Optional[str] = None,
                             db: Session = Depends(get_db),
                             current_user: models.User = Depends(require_data_entry)):
    obj = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not obj: raise HTTPException(status_code=404, detail="Incident not found")
    obj.workflow_status = workflow_status
    if review_notes:
        obj.review_notes = review_notes
        obj.reviewed_by  = current_user.id
    if workflow_status == 'published':
        obj.is_public = True
    db.commit(); db.refresh(obj)
    return obj

# ── File Upload ───────────────────────────────────────────────────────────────

ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx', '.mp4', '.avi', '.mov'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB

@app.post("/incidents/{incident_id}/documents")
async def upload_document(incident_id: str, file: UploadFile = File(...),
                          document_type: str = Form(...),
                          description: Optional[str] = Form(None),
                          is_public: bool = Form(False),
                          db: Session = Depends(get_db),
                          current_user: models.User = Depends(require_data_entry)):
    obj = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not obj: raise HTTPException(status_code=404, detail="Incident not found")
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type {ext} not allowed")
    unique_name = f"{uuid.uuid4()}{ext}"
    file_path = UPLOAD_DIR / unique_name
    try:
        with file_path.open("wb") as buf:
            shutil.copyfileobj(file.file, buf)
        size = file_path.stat().st_size
        if size > MAX_FILE_SIZE:
            file_path.unlink()
            raise HTTPException(status_code=400, detail="File too large (max 100 MB)")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")
    doc = models.Document(incident_id=incident_id, document_type=document_type,
                          file_name=file.filename, file_path=str(file_path),
                          file_url=f"/uploads/{unique_name}", file_size=size,
                          mime_type=file.content_type, description=description,
                          is_public=is_public, uploaded_by=current_user.id)
    db.add(doc); db.commit(); db.refresh(doc)
    return {"message": "File uploaded successfully", "document_id": str(doc.id), "file_url": doc.file_url}

@app.get("/incidents/{incident_id}/documents")
def get_incident_documents(incident_id: str, db: Session = Depends(get_db),
                           current_user: Optional[models.User] = Depends(get_current_active_user)):
    q = db.query(models.Document).filter(models.Document.incident_id == incident_id)
    if not current_user or current_user.role == 'viewer':
        q = q.filter(models.Document.is_public == True)
    return q.all()

@app.delete("/documents/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db),
                    current_user: models.User = Depends(require_data_entry)):
    doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc: raise HTTPException(status_code=404, detail="Document not found")
    try:
        p = Path(doc.file_path)
        if p.exists(): p.unlink()
    except Exception as e:
        print(f"Error deleting file: {e}")
    db.delete(doc); db.commit()
    return {"message": "Document deleted successfully"}

# ── CSV Import ────────────────────────────────────────────────────────────────

@app.post("/import/incidents")
async def import_incidents_csv(file: UploadFile = File(...), db: Session = Depends(get_db),
                               current_user: models.User = Depends(require_data_entry)):
    contents = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(contents)) if file.filename.endswith('.csv') \
             else pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {e}")
    for col in ['incident_date', 'description']:
        if col not in df.columns:
            raise HTTPException(status_code=400, detail=f"Missing required column: {col}")
    imported, failed, errors = 0, 0, []
    for idx, row in df.iterrows():
        try:
            dept_id = None
            if 'department_name' in row and pd.notna(row.get('department_name')):
                d = db.query(models.Department).filter(models.Department.name == row['department_name']).first()
                if d: dept_id = d.id
            off_id = None
            if 'officer_badge' in row and pd.notna(row.get('officer_badge')):
                o = db.query(models.Officer).filter(models.Officer.badge_number == str(row['officer_badge'])).first()
                if o: off_id = o.id
            type_id = None
            if 'incident_type' in row and pd.notna(row.get('incident_type')):
                t = db.query(models.IncidentType).filter(models.IncidentType.name == row['incident_type']).first()
                if t: type_id = t.id
            inc = models.Incident(
                incident_date=pd.to_datetime(row['incident_date']).date(),
                description=str(row['description']),
                department_id=dept_id, officer_id=off_id, incident_type_id=type_id,
                location_city=str(row['location_city']) if pd.notna(row.get('location_city')) else None,
                location_state=str(row['location_state']) if pd.notna(row.get('location_state')) else None,
                use_of_force=bool(row.get('use_of_force', False)) if pd.notna(row.get('use_of_force')) else False,
                death_occurred=bool(row.get('death_occurred', False)) if pd.notna(row.get('death_occurred')) else False,
                created_by=current_user.id, workflow_status='draft')
            db.add(inc); imported += 1
        except Exception as e:
            failed += 1; errors.append(f"Row {idx+2}: {e}")
    db.commit()
    log = models.ImportHistory(file_name=file.filename, import_type='incidents',
                               records_imported=imported, records_failed=failed,
                               error_log='\n'.join(errors) if errors else None,
                               imported_by=current_user.id)
    db.add(log); db.commit()
    return {"message": "Import completed", "imported": imported, "failed": failed, "errors": errors[:10]}

@app.post("/import/officers")
async def import_officers_csv(file: UploadFile = File(...), db: Session = Depends(get_db),
                              current_user: models.User = Depends(require_data_entry)):
    contents = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(contents)) if file.filename.endswith('.csv') \
             else pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {e}")
    if 'last_name' not in df.columns:
        raise HTTPException(status_code=400, detail="Missing required column: last_name")
    imported, failed, errors = 0, 0, []
    for idx, row in df.iterrows():
        try:
            dept_id = None
            if 'department_name' in row and pd.notna(row.get('department_name')):
                d = db.query(models.Department).filter(models.Department.name == row['department_name']).first()
                if d: dept_id = d.id
            officer = models.Officer(
                badge_number=str(row.get('badge_number','')) if pd.notna(row.get('badge_number')) else None,
                first_name=str(row.get('first_name','')) if pd.notna(row.get('first_name')) else None,
                last_name=str(row['last_name']), department_id=dept_id,
                rank=str(row.get('rank','')) if pd.notna(row.get('rank')) else None,
                status=str(row.get('status','active')) if pd.notna(row.get('status')) else 'active',
                created_by=current_user.id)
            db.add(officer); imported += 1
        except Exception as e:
            failed += 1; errors.append(f"Row {idx+2}: {e}")
    db.commit()
    log = models.ImportHistory(file_name=file.filename, import_type='officers',
                               records_imported=imported, records_failed=failed,
                               error_log='\n'.join(errors) if errors else None,
                               imported_by=current_user.id)
    db.add(log); db.commit()
    return {"message": "Import completed", "imported": imported, "failed": failed, "errors": errors[:10]}

@app.get("/import/history")
def get_import_history(db: Session = Depends(get_db),
                       current_user: models.User = Depends(require_data_entry)):
    return db.query(models.ImportHistory).order_by(models.ImportHistory.imported_at.desc()).limit(50).all()

@app.get("/import/template/{import_type}")
def download_import_template(import_type: str):
    templates = {
        'incidents':   'incident_date,department_name,officer_badge,incident_type,description,location_city,location_state,use_of_force,death_occurred\n2024-01-15,Fort Worth Police Department,1001,Excessive Force,Description here,Fort Worth,TX,true,false',
        'officers':    'badge_number,first_name,last_name,department_name,rank,status\n1001,John,Smith,Fort Worth Police Department,Officer,active',
        'departments': 'name,agency_type,jurisdiction,state,city,phone\nFort Worth Police Department,Municipal Police,City,TX,Fort Worth,817-555-0100'
    }
    if import_type not in templates:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"template": templates[import_type]}

# ── Outcomes & Complaints ─────────────────────────────────────────────────────

@app.get("/outcomes", response_model=List[schemas.Outcome])
def get_outcomes(incident_id: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(models.Outcome)
    if incident_id: q = q.filter(models.Outcome.incident_id == incident_id)
    return q.all()

@app.post("/outcomes", response_model=schemas.Outcome)
def create_outcome(outcome: schemas.OutcomeCreate, db: Session = Depends(get_db),
                   current_user: models.User = Depends(require_data_entry)):
    obj = models.Outcome(**outcome.model_dump(), created_by=current_user.id)
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

@app.get("/complaints", response_model=List[schemas.Complaint])
def get_complaints(incident_id: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(models.Complaint)
    if incident_id: q = q.filter(models.Complaint.incident_id == incident_id)
    return q.all()

@app.post("/complaints", response_model=schemas.Complaint)
def create_complaint(complaint: schemas.ComplaintCreate, db: Session = Depends(get_db),
                     current_user: models.User = Depends(require_data_entry)):
    obj = models.Complaint(**complaint.model_dump(), created_by=current_user.id)
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

# ── Statistics ────────────────────────────────────────────────────────────────

@app.get("/stats/incidents", response_model=schemas.IncidentStats)
def get_incident_stats(db: Session = Depends(get_db)):
    total      = db.query(func.count(models.Incident.id)).scalar()
    by_type    = db.query(models.IncidentType.name, func.count(models.Incident.id))\
                   .join(models.Incident).group_by(models.IncidentType.name).all()
    by_dept    = db.query(models.Department.name, func.count(models.Incident.id))\
                   .join(models.Incident).group_by(models.Department.name).all()
    by_year    = db.query(extract('year', models.Incident.incident_date).label('year'),
                          func.count(models.Incident.id)).group_by('year').all()
    force_cnt  = db.query(func.count(models.Incident.id)).filter(models.Incident.use_of_force  == True).scalar()
    death_cnt  = db.query(func.count(models.Incident.id)).filter(models.Incident.death_occurred == True).scalar()
    return {"total_incidents": total,
            "incidents_by_type": {n: c for n, c in by_type},
            "incidents_by_department": {n: c for n, c in by_dept},
            "incidents_by_year": {int(y): c for y, c in by_year},
            "use_of_force_incidents": force_cnt,
            "death_incidents": death_cnt}

@app.get("/stats/officers", response_model=schemas.OfficerStats)
def get_officer_stats(db: Session = Depends(get_db)):
    total        = db.query(func.count(models.Officer.id)).scalar()
    active       = db.query(func.count(models.Officer.id)).filter(models.Officer.status == "active").scalar()
    with_inc     = db.query(func.count(func.distinct(models.Incident.officer_id))).scalar()
    avg_inc      = db.query(func.avg(
        db.query(func.count(models.Incident.id))
          .filter(models.Incident.officer_id == models.Officer.id)
          .correlate(models.Officer).scalar_subquery()
    )).scalar() or 0
    return {"total_officers": total, "active_officers": active,
            "officers_with_incidents": with_inc,
            "average_incidents_per_officer": float(avg_inc)}

@app.get("/")
def root():
    return {"message": "Police Misconduct Database API", "version": "2.0.0", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
