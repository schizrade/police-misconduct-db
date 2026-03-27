import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user,    setUser]    = useState(null);
  const [token,   setToken]   = useState(() => sessionStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  // Inject / remove Authorization header whenever token changes
  useEffect(() => {
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      sessionStorage.setItem('token', token);
    } else {
      delete api.defaults.headers.common['Authorization'];
      sessionStorage.removeItem('token');
    }
  }, [token]);

  // On mount (or token change) fetch the current user profile
  useEffect(() => {
    if (!token) { setLoading(false); return; }
    api.get('/users/me')
      .then(res => setUser(res.data))
      .catch(() => {
        // Token invalid / expired — clear everything
        setToken(null);
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, [token]);

  const login = useCallback(async (username, password) => {
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);

    const res = await api.post('/token', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });

    setToken(res.data.access_token);
    // user profile will be fetched by the effect above
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
}
