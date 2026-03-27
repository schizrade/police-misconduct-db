import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

/**
 * Wraps a route so only authenticated users can access it.
 * Optionally restrict to specific roles, e.g. requiredRole="admin"
 */
export default function ProtectedRoute({ children, requiredRole }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) return <div className="loading">Loading...</div>;

  if (!user) {
    // Redirect to login, remembering where we came from
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requiredRole) {
    const hierarchy = { viewer: 0, data_entry: 1, reviewer: 2, admin: 3 };
    if ((hierarchy[user.role] ?? 0) < (hierarchy[requiredRole] ?? 0)) {
      return (
        <div className="error" style={{ margin: '2rem' }}>
          You don't have permission to view this page.
          Required role: <strong>{requiredRole}</strong> — your role: <strong>{user.role}</strong>.
        </div>
      );
    }
  }

  return children;
}
