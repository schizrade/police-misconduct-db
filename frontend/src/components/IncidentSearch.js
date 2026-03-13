import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { searchIncidents, getDepartments, getIncidentTypes } from '../services/api';
import './IncidentSearch.css';

function IncidentSearch() {
  const [incidents, setIncidents]       = useState([]);
  const [departments, setDepartments]   = useState([]);
  const [incidentTypes, setTypes]       = useState([]);
  const [loading, setLoading]           = useState(false);
  const [error, setError]               = useState(null);
  const [filters, setFilters] = useState({
    query:'', start_date:'', end_date:'', department_id:'', incident_type_id:'',
    location_city:'', location_state:'', use_of_force:'', death_occurred:'', status:''
  });

  useEffect(() => { loadFilterOptions(); handleSearch(); }, []);

  const loadFilterOptions = async () => {
    try {
      const [d, t] = await Promise.all([getDepartments(), getIncidentTypes()]);
      setDepartments(d.data); setTypes(t.data);
    } catch {}
  };

  const handleSearch = async () => {
    try {
      setLoading(true); setError(null);
      const params = Object.fromEntries(Object.entries(filters).filter(([,v]) => v !== ''));
      const res = await searchIncidents(params);
      setIncidents(res.data);
    } catch { setError('Failed to search incidents'); }
    finally { setLoading(false); }
  };

  const handleFilterChange = e => setFilters(p => ({ ...p, [e.target.name]: e.target.value }));
  const handleReset = () => setFilters({ query:'', start_date:'', end_date:'', department_id:'',
    incident_type_id:'', location_city:'', location_state:'', use_of_force:'', death_occurred:'', status:'' });

  return (
    <div className="incident-search">
      <h2>Search Incidents</h2>
      <div className="search-filters">
        <div className="filter-row">
          <input type="text" name="query" placeholder="Search description..." value={filters.query} onChange={handleFilterChange} className="search-input" />
          <button onClick={handleSearch} className="btn-primary">Search</button>
          <button onClick={handleReset}  className="btn-secondary">Reset</button>
        </div>
        <div className="filter-grid">
          {[['start_date','Start Date','date'],['end_date','End Date','date'],['location_city','City','text'],['location_state','State','text']].map(([name,label,type]) => (
            <div className="filter-group" key={name}>
              <label>{label}</label>
              <input type={type} name={name} value={filters[name]} onChange={handleFilterChange} placeholder={name==='location_state'?'TX':undefined} maxLength={name==='location_state'?2:undefined} />
            </div>
          ))}
          <div className="filter-group"><label>Department</label>
            <select name="department_id" value={filters.department_id} onChange={handleFilterChange}>
              <option value="">All Departments</option>
              {departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          </div>
          <div className="filter-group"><label>Incident Type</label>
            <select name="incident_type_id" value={filters.incident_type_id} onChange={handleFilterChange}>
              <option value="">All Types</option>
              {incidentTypes.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
          </div>
          <div className="filter-group"><label>Use of Force</label>
            <select name="use_of_force" value={filters.use_of_force} onChange={handleFilterChange}>
              <option value="">Any</option><option value="true">Yes</option><option value="false">No</option>
            </select>
          </div>
          <div className="filter-group"><label>Fatal Incident</label>
            <select name="death_occurred" value={filters.death_occurred} onChange={handleFilterChange}>
              <option value="">Any</option><option value="true">Yes</option><option value="false">No</option>
            </select>
          </div>
          <div className="filter-group"><label>Status</label>
            <select name="status" value={filters.status} onChange={handleFilterChange}>
              <option value="">All</option>
              {['reported','investigating','closed','appeal'].map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
        </div>
      </div>
      <div className="search-results">
        <h3>Results ({incidents.length})</h3>
        {loading && <div className="loading">Searching...</div>}
        {error   && <div className="error">{error}</div>}
        {!loading && incidents.length === 0 && <p>No incidents found.</p>}
        {!loading && incidents.length > 0 && (
          <table className="incidents-table">
            <thead><tr><th>Date</th><th>Description</th><th>Location</th><th>Force</th><th>Fatal</th><th>Status</th><th>Actions</th></tr></thead>
            <tbody>
              {incidents.map(i => (
                <tr key={i.id}>
                  <td>{new Date(i.incident_date).toLocaleDateString()}</td>
                  <td className="description-cell">{i.description.substring(0,80)}...</td>
                  <td>{i.location_city}, {i.location_state}</td>
                  <td>{i.use_of_force ? '✓' : '—'}</td>
                  <td>{i.death_occurred ? '✓' : '—'}</td>
                  <td><span className={`status-badge status-${i.status}`}>{i.status}</span></td>
                  <td><Link to={`/incident/${i.id}`} className="btn-view">View</Link></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default IncidentSearch;
