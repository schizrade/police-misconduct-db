import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useNavigate } from 'react-router-dom';
import './App.css';

import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedRoute  from './components/ProtectedRoute';
import Login           from './components/Login';
import Dashboard       from './components/Dashboard';
import IncidentSearch  from './components/IncidentSearch';
import IncidentDetail  from './components/IncidentDetail';
import AddIncident     from './components/AddIncident';
import Statistics      from './components/Statistics';

// ── Role badge colours ────────────────────────────────────────────────────────
const ROLE_COLOURS = {
  admin:      '#e74c3c',
  reviewer:   '#8e44ad',
  data_entry: '#27ae60',
  viewer:     '#7f8c8d',
};

function NavBar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => { logout(); navigate('/login'); };

  return (
    <nav className="navbar">
      <div className="nav-container">
        <h1 className="nav-title">Police Misconduct Database</h1>

        <ul className="nav-links">
          <li><Link to="/">Dashboard</Link></li>
          <li><Link to="/search">Search</Link></li>
          <li><Link to="/statistics">Statistics</Link></li>
          {user && ['admin','data_entry'].includes(user.role) && (
            <li><Link to="/add-incident">Add Incident</Link></li>
          )}
        </ul>

        {user && (
          <div className="nav-user">
            <span className="nav-user-name">{user.full_name || user.username}</span>
            <span
              className="nav-role-badge"
              style={{ background: ROLE_COLOURS[user.role] || '#7f8c8d' }}
            >
              {user.role.replace('_', ' ')}
            </span>
            <button className="btn-logout" onClick={handleLogout}>Sign out</button>
          </div>
        )}
      </div>
    </nav>
  );
}

function AppRoutes() {
  const { user } = useAuth();

  return (
    <>
      {user && <NavBar />}
      <main className="main-content">
        <Routes>
          {/* Public */}
          <Route path="/login" element={<Login />} />

          {/* Protected — any authenticated user */}
          <Route path="/" element={
            <ProtectedRoute><Dashboard /></ProtectedRoute>
          }/>
          <Route path="/search" element={
            <ProtectedRoute><IncidentSearch /></ProtectedRoute>
          }/>
          <Route path="/incident/:id" element={
            <ProtectedRoute><IncidentDetail /></ProtectedRoute>
          }/>
          <Route path="/statistics" element={
            <ProtectedRoute><Statistics /></ProtectedRoute>
          }/>

          {/* Protected — data_entry or above */}
          <Route path="/add-incident" element={
            <ProtectedRoute requiredRole="data_entry"><AddIncident /></ProtectedRoute>
          }/>
        </Routes>
      </main>

      {user && (
        <footer className="footer">
          <p>Police Misconduct Database v2.0 | Public Information System</p>
        </footer>
      )}
    </>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <AppRoutes />
        </div>
      </Router>
    </AuthProvider>
  );
}
