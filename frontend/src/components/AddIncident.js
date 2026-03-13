import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { createIncident, getDepartments, getOfficers, getIncidentTypes } from '../services/api';
import './AddIncident.css';

const initialForm = {
  incident_date:'', incident_type_id:'', officer_id:'', department_id:'',
  location_address:'', location_city:'', location_state:'', description:'',
  civilian_name:'', civilian_age:'', civilian_race:'', civilian_gender:'',
  use_of_force:false, force_type:'', injury_occurred:false, injury_description:'',
  death_occurred:false, witnesses_present:false, body_cam_footage:false, dash_cam_footage:false,
  status:'reported'
};

function AddIncident() {
  const navigate = useNavigate();
  const [departments, setDepartments] = useState([]);
  const [officers,    setOfficers]    = useState([]);
  const [types,       setTypes]       = useState([]);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState(null);
  const [success, setSuccess] = useState(false);
  const [formData, setFormData] = useState(initialForm);

  useEffect(() => {
    (async () => {
      try {
        const [d, o, t] = await Promise.all([getDepartments(), getOfficers(), getIncidentTypes()]);
        setDepartments(d.data); setOfficers(o.data); setTypes(t.data);
      } catch {}
    })();
  }, []);

  const handleChange = e => {
    const { name, value, type, checked } = e.target;
    setFormData(p => ({ ...p, [name]: type === 'checkbox' ? checked : value }));
  };

  const handleSubmit = async e => {
    e.preventDefault();
    try {
      setLoading(true); setError(null);
      const clean = {};
      Object.entries(formData).forEach(([k, v]) => {
        if (v !== '' && v !== null) clean[k] = k === 'civilian_age' && v ? parseInt(v) : v;
      });
      await createIncident(clean);
      setSuccess(true);
      setTimeout(() => navigate('/search'), 2000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create incident');
    } finally {
      setLoading(false);
    }
  };

  if (success) return <div className="add-incident"><div className="success-message"><h2>✓ Incident Created</h2><p>Redirecting...</p></div></div>;

  return (
    <div className="add-incident">
      <h2>Add New Incident</h2>
      {error && <div className="error-message">{error}</div>}
      <form onSubmit={handleSubmit} className="incident-form">

        <div className="form-section">
          <h3>Basic Information</h3>
          <div className="form-group"><label>Incident Date *</label>
            <input type="date" name="incident_date" value={formData.incident_date} onChange={handleChange} required />
          </div>
          <div className="form-group"><label>Incident Type</label>
            <select name="incident_type_id" value={formData.incident_type_id} onChange={handleChange}>
              <option value="">Select type...</option>
              {types.map(t => <option key={t.id} value={t.id}>{t.name} ({t.severity})</option>)}
            </select>
          </div>
          <div className="form-group"><label>Department</label>
            <select name="department_id" value={formData.department_id} onChange={handleChange}>
              <option value="">Select department...</option>
              {departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          </div>
          <div className="form-group"><label>Officer</label>
            <select name="officer_id" value={formData.officer_id} onChange={handleChange}>
              <option value="">Select officer...</option>
              {officers.map(o => <option key={o.id} value={o.id}>{o.first_name} {o.last_name} ({o.badge_number})</option>)}
            </select>
          </div>
          <div className="form-group"><label>Status</label>
            <select name="status" value={formData.status} onChange={handleChange}>
              {['reported','investigating','closed','appeal'].map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
        </div>

        <div className="form-section">
          <h3>Location</h3>
          <div className="form-group"><label>Address</label>
            <input type="text" name="location_address" value={formData.location_address} onChange={handleChange} />
          </div>
          <div className="form-row">
            <div className="form-group"><label>City</label>
              <input type="text" name="location_city" value={formData.location_city} onChange={handleChange} />
            </div>
            <div className="form-group"><label>State</label>
              <input type="text" name="location_state" value={formData.location_state} onChange={handleChange} maxLength="2" placeholder="TX" />
            </div>
          </div>
        </div>

        <div className="form-section">
          <h3>Description *</h3>
          <div className="form-group">
            <textarea name="description" value={formData.description} onChange={handleChange} rows="6" required placeholder="Detailed description..." />
          </div>
        </div>

        <div className="form-section">
          <h3>Civilian Information</h3>
          <div className="form-group"><label>Name</label>
            <input type="text" name="civilian_name" value={formData.civilian_name} onChange={handleChange} />
          </div>
          <div className="form-row">
            <div className="form-group"><label>Age</label>
              <input type="number" name="civilian_age" value={formData.civilian_age} onChange={handleChange} min="0" max="120" />
            </div>
            <div className="form-group"><label>Race</label>
              <input type="text" name="civilian_race" value={formData.civilian_race} onChange={handleChange} />
            </div>
            <div className="form-group"><label>Gender</label>
              <select name="civilian_gender" value={formData.civilian_gender} onChange={handleChange}>
                <option value="">Select...</option>
                {['Male','Female','Non-binary','Unknown'].map(g => <option key={g} value={g}>{g}</option>)}
              </select>
            </div>
          </div>
        </div>

        <div className="form-section">
          <h3>Incident Characteristics</h3>
          {[['use_of_force','Use of Force'],['injury_occurred','Injury Occurred'],['death_occurred','Death Occurred'],
            ['witnesses_present','Witnesses Present'],['body_cam_footage','Body Camera Footage'],['dash_cam_footage','Dash Camera Footage']
          ].map(([name, label]) => (
            <div className="checkbox-group" key={name}>
              <label><input type="checkbox" name={name} checked={formData[name]} onChange={handleChange} />{label}</label>
            </div>
          ))}
          {formData.use_of_force && (
            <div className="form-group"><label>Force Type</label>
              <input type="text" name="force_type" value={formData.force_type} onChange={handleChange} placeholder="e.g., Firearm, Taser, Physical" />
            </div>
          )}
          {formData.injury_occurred && (
            <div className="form-group"><label>Injury Description</label>
              <textarea name="injury_description" value={formData.injury_description} onChange={handleChange} rows="3" />
            </div>
          )}
        </div>

        <div className="form-actions">
          <button type="submit" className="btn-primary" disabled={loading}>{loading ? 'Creating...' : 'Create Incident'}</button>
          <button type="button" className="btn-secondary" onClick={() => navigate('/search')}>Cancel</button>
        </div>
      </form>
    </div>
  );
}

export default AddIncident;
