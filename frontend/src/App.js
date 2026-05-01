import React, { createContext, useContext, useState, useEffect, Component } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import api from './api';
import './index.css';

import Giris          from './components/Giris';
import Kayit          from './components/Kayit';
import SohbetArayuz   from './components/SohbetArayuz';

// Hata yakalama
class ErrorBoundary extends Component {
  constructor(props) { super(props); this.state = { hasError: false }; }
  static getDerivedStateFromError() { return { hasError: true }; }
  componentDidCatch(error, info) { console.error('[Emlakisim] Hata:', error, info); }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', flexDirection: 'column', gap: 16 }}>
          <div style={{ fontSize: 48 }}>⚠️</div>
          <div style={{ fontSize: 18, fontWeight: 700, color: '#dc2626' }}>Bir hata oluştu</div>
          <button onClick={() => window.location.reload()} style={{ background: '#16a34a', color: '#fff', border: 'none', borderRadius: 8, padding: '10px 20px', fontSize: 14, cursor: 'pointer' }}>
            Sayfayı Yenile
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

const AuthCtx = createContext(null);
export const useAuth = () => useContext(AuthCtx);

function AuthProvider({ children }) {
  const [user, setUser]      = useState(null);
  const [yukleniyor, setYuk] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) { setYuk(false); return; }
    api.get('/api/auth/profil')
      .then(r => setUser(r.data.user))
      .catch(() => localStorage.removeItem('token'))
      .finally(() => setYuk(false));
  }, []);

  const girisYap = (token, userData) => {
    localStorage.setItem('token', token);
    setUser(userData);
  };
  const cikisYap = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  if (yukleniyor) return (
    <div style={{ display:'flex', alignItems:'center', justifyContent:'center', height:'100vh' }}>
      <div style={{ fontSize: 48 }}>🏠</div>
    </div>
  );

  return (
    <AuthCtx.Provider value={{ user, setUser, girisYap, cikisYap }}>
      {children}
    </AuthCtx.Provider>
  );
}

function Koruma({ children }) {
  const { user } = useAuth();
  return user ? children : <Navigate to="/giris" replace />;
}

export default function App() {
  return (
    <ErrorBoundary>
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/giris" element={<Giris />} />
          <Route path="/kayit" element={<Kayit />} />
          <Route path="/"      element={<Koruma><SohbetArayuz /></Koruma>} />
          <Route path="*"      element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
    </ErrorBoundary>
  );
}
