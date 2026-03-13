import React, { useState, useEffect } from 'react';
import { Bar, Pie, Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, PointElement, LineElement, ArcElement, Title, Tooltip, Legend } from 'chart.js';
import { getIncidentStats, getOfficerStats } from '../services/api';
import './Statistics.css';

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, ArcElement, Title, Tooltip, Legend);

const COLORS = ['rgba(255,99,132,0.6)','rgba(54,162,235,0.6)','rgba(255,206,86,0.6)','rgba(75,192,192,0.6)','rgba(153,102,255,0.6)','rgba(255,159,64,0.6)'];
const BORDERS= ['rgba(255,99,132,1)','rgba(54,162,235,1)','rgba(255,206,86,1)','rgba(75,192,192,1)','rgba(153,102,255,1)','rgba(255,159,64,1)'];
const opts   = { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'top' } } };

function Statistics() {
  const [inc, setInc]     = useState(null);
  const [off, setOff]     = useState(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const [iRes, oRes] = await Promise.all([getIncidentStats(), getOfficerStats()]);
        setInc(iRes.data); setOff(oRes.data);
      } catch { setError('Failed to load statistics'); }
      finally { setLoading(false); }
    })();
  }, []);

  if (loading) return <div className="loading">Loading statistics...</div>;
  if (error)   return <div className="error">{error}</div>;

  const byType = { labels: Object.keys(inc?.incidents_by_type || {}),
    datasets: [{ label: 'By Type', data: Object.values(inc?.incidents_by_type || {}), backgroundColor: COLORS, borderColor: BORDERS, borderWidth: 1 }] };

  const byYear = { labels: Object.keys(inc?.incidents_by_year || {}).sort(),
    datasets: [{ label: 'By Year', data: Object.keys(inc?.incidents_by_year || {}).sort().map(y => inc.incidents_by_year[y]),
      backgroundColor: 'rgba(75,192,192,0.6)', borderColor: 'rgba(75,192,192,1)', borderWidth: 1 }] };

  const byDept = { labels: Object.keys(inc?.incidents_by_department || {}).slice(0,10),
    datasets: [{ label: 'Top 10 Departments', data: Object.values(inc?.incidents_by_department || {}).slice(0,10),
      backgroundColor: 'rgba(153,102,255,0.6)', borderColor: 'rgba(153,102,255,1)', borderWidth: 1 }] };

  const pct = (n, d) => d ? ((n/d)*100).toFixed(1) : 0;

  return (
    <div className="statistics">
      <h2>Statistics & Analytics</h2>
      <div className="stats-summary">
        <div className="summary-grid">
          {[
            ['Total Incidents',         inc?.total_incidents,         null,                                   null],
            ['Use of Force',            inc?.use_of_force_incidents,  pct(inc?.use_of_force_incidents, inc?.total_incidents)+'%', null],
            ['Fatal Incidents',         inc?.death_incidents,         pct(inc?.death_incidents, inc?.total_incidents)+'%',        null],
            ['Total Officers',          off?.total_officers,          null,                                   off?.active_officers+' active'],
            ['Officers w/ Incidents',   off?.officers_with_incidents, pct(off?.officers_with_incidents, off?.total_officers)+'%', null],
            ['Avg Incidents/Officer',   off?.average_incidents_per_officer?.toFixed(2), null,                null],
          ].map(([label, num, pctVal, detail]) => (
            <div className="summary-card" key={label}>
              <h3>{label}</h3>
              <p className="summary-number">{num || 0}</p>
              {pctVal  && <p className="summary-percent">{pctVal}</p>}
              {detail  && <p className="summary-detail">{detail}</p>}
            </div>
          ))}
        </div>
      </div>
      <div className="charts-grid">
        <div className="chart-container"><h3>Incidents by Type</h3><div className="chart"><Bar data={byType} options={opts} /></div></div>
        <div className="chart-container"><h3>Incidents Over Time</h3><div className="chart"><Line data={byYear} options={opts} /></div></div>
        <div className="chart-container"><h3>Top 10 Departments</h3><div className="chart"><Bar data={byDept} options={{ ...opts, indexAxis:'y' }} /></div></div>
        <div className="chart-container"><h3>Type Distribution</h3><div className="chart"><Pie data={byType} options={opts} /></div></div>
      </div>
    </div>
  );
}

export default Statistics;
