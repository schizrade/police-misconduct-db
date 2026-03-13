import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import './App.css';
import Dashboard      from './components/Dashboard';
import IncidentSearch from './components/IncidentSearch';
import IncidentDetail from './components/IncidentDetail';
import AddIncident    from './components/AddIncident';
import Statistics     from './components/Statistics';

function App() {
  return (
    <Router>
      <div className="App">
        <nav className="navbar">
          <div className="nav-container">
            <h1 className="nav-title">Police Misconduct Database</h1>
            <ul className="nav-links">
              <li><Link to="/">Dashboard</Link></li>
              <li><Link to="/search">Search</Link></li>
              <li><Link to="/statistics">Statistics</Link></li>
              <li><Link to="/add-incident">Add Incident</Link></li>
            </ul>
          </div>
        </nav>
        <main className="main-content">
          <Routes>
            <Route path="/"             element={<Dashboard />} />
            <Route path="/search"       element={<IncidentSearch />} />
            <Route path="/incident/:id" element={<IncidentDetail />} />
            <Route path="/add-incident" element={<AddIncident />} />
            <Route path="/statistics"   element={<Statistics />} />
          </Routes>
        </main>
        <footer className="footer">
          <p>Police Misconduct Database v2.0 | Public Information System</p>
        </footer>
      </div>
    </Router>
  );
}

export default App;
