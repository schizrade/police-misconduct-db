-- Enhanced Police Misconduct Database Schema with Authentication
-- Version 2.0 — PostgreSQL 14+

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) NOT NULL DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(50) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    record_id UUID,
    changes JSONB,
    ip_address VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE departments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    agency_type VARCHAR(100),
    jurisdiction VARCHAR(255),
    state VARCHAR(2),
    city VARCHAR(100),
    address TEXT,
    phone VARCHAR(20),
    website VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id)
);

CREATE TABLE officers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    badge_number VARCHAR(50),
    first_name VARCHAR(100),
    last_name VARCHAR(100) NOT NULL,
    department_id UUID REFERENCES departments(id),
    rank VARCHAR(100),
    hire_date DATE,
    termination_date DATE,
    status VARCHAR(50) DEFAULT 'active',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id)
);

CREATE TABLE incident_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    severity VARCHAR(20)
);

CREATE TABLE incidents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_date DATE NOT NULL,
    incident_type_id UUID REFERENCES incident_types(id),
    officer_id UUID REFERENCES officers(id),
    department_id UUID REFERENCES departments(id),
    location_address TEXT,
    location_city VARCHAR(100),
    location_state VARCHAR(2),
    location_latitude DECIMAL(10, 8),
    location_longitude DECIMAL(11, 8),
    description TEXT NOT NULL,
    civilian_name VARCHAR(255),
    civilian_age INTEGER,
    civilian_race VARCHAR(50),
    civilian_gender VARCHAR(50),
    use_of_force BOOLEAN DEFAULT false,
    force_type VARCHAR(100),
    injury_occurred BOOLEAN DEFAULT false,
    injury_description TEXT,
    death_occurred BOOLEAN DEFAULT false,
    witnesses_present BOOLEAN,
    body_cam_footage BOOLEAN,
    dash_cam_footage BOOLEAN,
    status VARCHAR(50) DEFAULT 'reported',
    workflow_status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    reviewed_by UUID REFERENCES users(id),
    review_notes TEXT,
    is_public BOOLEAN DEFAULT false
);

CREATE TABLE outcomes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID REFERENCES incidents(id),
    outcome_date DATE,
    outcome_type VARCHAR(100),
    suspension_days INTEGER,
    fine_amount DECIMAL(10, 2),
    details TEXT,
    appealed BOOLEAN DEFAULT false,
    appeal_outcome VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id)
);

CREATE TABLE complaints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID REFERENCES incidents(id),
    complaint_number VARCHAR(100),
    filed_date DATE NOT NULL,
    complainant_type VARCHAR(50),
    complaint_source VARCHAR(100),
    investigation_status VARCHAR(50),
    investigation_completed_date DATE,
    sustained BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id)
);

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID REFERENCES incidents(id),
    document_type VARCHAR(100),
    file_name VARCHAR(255),
    file_path VARCHAR(500),
    file_url VARCHAR(500),
    file_size BIGINT,
    mime_type VARCHAR(100),
    description TEXT,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_public BOOLEAN DEFAULT false,
    uploaded_by UUID REFERENCES users(id)
);

CREATE TABLE import_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_name VARCHAR(255),
    import_type VARCHAR(50),
    records_imported INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    error_log TEXT,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    imported_by UUID REFERENCES users(id)
);

-- Indexes
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_officers_last_name ON officers(last_name);
CREATE INDEX idx_officers_department ON officers(department_id);
CREATE INDEX idx_incidents_date ON incidents(incident_date);
CREATE INDEX idx_incidents_officer ON incidents(officer_id);
CREATE INDEX idx_incidents_department ON incidents(department_id);
CREATE INDEX idx_incidents_workflow_status ON incidents(workflow_status);
CREATE INDEX idx_incidents_is_public ON incidents(is_public);
CREATE INDEX idx_incidents_location ON incidents(location_city, location_state);
CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp);
CREATE INDEX idx_incidents_description_fts ON incidents USING gin(to_tsvector('english', description));

-- updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = CURRENT_TIMESTAMP; RETURN NEW; END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at       BEFORE UPDATE ON users       FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_departments_updated_at BEFORE UPDATE ON departments  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_officers_updated_at    BEFORE UPDATE ON officers     FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_incidents_updated_at   BEFORE UPDATE ON incidents    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_outcomes_updated_at    BEFORE UPDATE ON outcomes     FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_complaints_updated_at  BEFORE UPDATE ON complaints   FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Seed incident types
INSERT INTO incident_types (name, description, severity) VALUES
('Excessive Force',         'Use of force beyond what is reasonable',              'severe'),
('Unlawful Search',         'Search conducted without proper warrant or cause',     'moderate'),
('False Arrest',            'Arrest without probable cause',                        'severe'),
('Racial Profiling',        'Targeting based on race or ethnicity',                 'severe'),
('Harassment',              'Verbal or physical harassment of civilians',           'moderate'),
('Neglect of Duty',         'Failure to perform required duties',                   'minor'),
('Misconduct - Sexual',     'Sexual harassment or assault',                         'critical'),
('Evidence Tampering',      'Altering or destroying evidence',                      'critical'),
('False Statement',         'Lying in reports or testimony',                        'severe'),
('Theft/Corruption',        'Theft of property or acceptance of bribes',            'critical'),
('DUI/DWI',                 'Driving under the influence on or off duty',           'severe'),
('Domestic Violence',       'Violence against family or household members',         'critical'),
('Improper Use of Firearm', 'Discharge of weapon outside policy',                   'severe'),
('Failure to Intervene',    'Failing to stop misconduct by another officer',        'severe');

-- Default admin user (password: admin123 — CHANGE IMMEDIATELY)
INSERT INTO users (username, email, hashed_password, full_name, role, is_active) VALUES
('admin', 'admin@example.com',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU8cqCg6eKYu',
 'System Administrator', 'admin', true);
