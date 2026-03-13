import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getIncident, getOutcomes, getComplaints } from '../services/api';
import './IncidentDetail.css';

function IncidentDetail() {
  const { id } = useParams();
  const [incident,   setIncident]   = useState(null);
  const [outcomes,   setOutcomes]   = useState([]);
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const [iRes, oRes, cRes] = await Promise.all([
          getIncident(id), getOutcomes({ incident_id: id }), getComplaints({ incident_id: id })
        ]);
        setIncident(iRes.data); setOutcomes(oRes.data); setComplaints(cRes.data);
      } catch { setError('Failed to load incident details'); }
      finally { setLoading(false); }
    })();
  }, [id]);

  if (loading) return <div className="loading">Loading incident...</div>;
  if (error)   return <div className="error">{error}</div>;
  if (!incident) return <div className="error">Incident not found</div>;

  const Row = ({ label, children }) => (
    <div className="detail-row"><span className="label">{label}:</span><span>{children}</span></div>
  );

  return (
    <div className="incident-detail">
      <div className="detail-header">
        <Link to="/search" className="back-link">← Back to Search</Link>
        <h2>Incident Details</h2>
      </div>
      <div className="detail-grid">
        <div className="detail-section">
          <h3>Basic Information</h3>
          <Row label="Date">{new Date(incident.incident_date).toLocaleDateString()}</Row>
          <Row label="Status"><span className={`status-badge status-${incident.status}`}>{incident.status}</span></Row>
          <Row label="Location">{[incident.location_address, incident.location_city, incident.location_state].filter(Boolean).join(', ')}</Row>
        </div>
        <div className="detail-section">
          <h3>Incident Details</h3>
          <div className="detail-row"><span className="label">Description:</span><p>{incident.description}</p></div>
          <Row label="Use of Force">{incident.use_of_force ? 'Yes' : 'No'}</Row>
          {incident.use_of_force && incident.force_type && <Row label="Force Type">{incident.force_type}</Row>}
          <Row label="Injury">{incident.injury_occurred ? 'Yes' : 'No'}</Row>
          <Row label="Fatal"><span className={incident.death_occurred ? 'fatal-yes' : ''}>{incident.death_occurred ? 'Yes' : 'No'}</span></Row>
        </div>
        {incident.civilian_name && (
          <div className="detail-section">
            <h3>Civilian Information</h3>
            <Row label="Name">{incident.civilian_name}</Row>
            {incident.civilian_age    && <Row label="Age">{incident.civilian_age}</Row>}
            {incident.civilian_race   && <Row label="Race">{incident.civilian_race}</Row>}
            {incident.civilian_gender && <Row label="Gender">{incident.civilian_gender}</Row>}
          </div>
        )}
        <div className="detail-section">
          <h3>Evidence</h3>
          <Row label="Witnesses">{incident.witnesses_present ? 'Yes' : 'No'}</Row>
          <Row label="Body Camera">{incident.body_cam_footage ? 'Yes' : 'No'}</Row>
          <Row label="Dash Camera">{incident.dash_cam_footage ? 'Yes' : 'No'}</Row>
        </div>
        {outcomes.length > 0 && (
          <div className="detail-section full-width">
            <h3>Outcomes</h3>
            {outcomes.map(o => (
              <div key={o.id} className="outcome-card">
                <Row label="Type">{o.outcome_type}</Row>
                {o.outcome_date     && <Row label="Date">{new Date(o.outcome_date).toLocaleDateString()}</Row>}
                {o.suspension_days  && <Row label="Suspension">{o.suspension_days} days</Row>}
                {o.fine_amount      && <Row label="Fine">${o.fine_amount}</Row>}
                {o.details          && <div className="detail-row"><span className="label">Details:</span><p>{o.details}</p></div>}
              </div>
            ))}
          </div>
        )}
        {complaints.length > 0 && (
          <div className="detail-section full-width">
            <h3>Complaints</h3>
            {complaints.map(c => (
              <div key={c.id} className="complaint-card">
                <Row label="Number">{c.complaint_number}</Row>
                <Row label="Filed">{new Date(c.filed_date).toLocaleDateString()}</Row>
                <Row label="Status">{c.investigation_status}</Row>
                {c.sustained !== null && <Row label="Sustained">{c.sustained ? 'Yes' : 'No'}</Row>}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default IncidentDetail;
