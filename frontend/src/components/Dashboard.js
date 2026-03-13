import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { searchIncidents, getIncidentStats } from '../services/api';
import './Dashboard.css';

function Dashboard() {
  const [recentIncidents, setRecentIncidents] = useState([]);
  const [stats, setStats]   = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState(null);

  useEffect(() => { loadDashboardData(); }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [incRes, stRes] = await Promise.all([searchIncidents({ limit: 10 }), getIncidentStats()]);
      setRecentIncidents(incRes.data);
      setStats(stRes.data);
      setError(null);
    } catch (err) {
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading dashboard...</div>;
  if (error)   return <div className="error">{error}</div>;

  return (
    <div className="dashboard">
      <h2>Dashboard</h2>
      <div className="stats-grid">
        <div className="stat-card"><h3>Total Incidents</h3><p className="stat-number">{stats?.total_incidents || 0}</p></div>
        <div className="stat-card"><h3>Use of Force</h3><p className="stat-number">{stats?.use_of_force_incidents || 0}</p></div>
        <div className="stat-card"><h3>Fatal Incidents</h3><p className="stat-number">{stats?.death_incidents || 0}</p></div>
      </div>
      <div className="recent-incidents">
        <h3>Recent Incidents</h3>
        {recentIncidents.length === 0 ? <p>No incidents recorded yet.</p> : (
          <table className="incidents-table">
            <thead><tr><th>Date</th><th>Description</th><th>Location</th><th>Status</th><th>Actions</th></tr></thead>
            <tbody>
              {recentIncidents.map(i => (
                <tr key={i.id}>
                  <td>{new Date(i.incident_date).toLocaleDateString()}</td>
                  <td className="description-cell">{i.description.substring(0,100)}{i.description.length > 100 ? '...' : ''}</td>
                  <td>{i.location_city}, {i.location_state}</td>
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

export default Dashboard;
