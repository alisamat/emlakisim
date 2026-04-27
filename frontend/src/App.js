import React, { createContext, useContext, useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import api from './api';
import './index.css';

import Giris          from './components/Giris';
import Kayit          from './components/Kayit';
import Panel          from './components/Panel';
import Musteriler     from './components/Musteriler';
import Mulkler        from './components/Mulkler';
import YerGostermeler from './components/YerGostermeler';
import Profil         from './components/Profil';

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
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/giris"      element={<Giris />} />
          <Route path="/kayit"      element={<Kayit />} />
          <Route path="/"           element={<Koruma><Panel /></Koruma>} />
          <Route path="/musteriler" element={<Koruma><Musteriler /></Koruma>} />
          <Route path="/mulkler"    element={<Koruma><Mulkler /></Koruma>} />
          <Route path="/kayitlar"   element={<Koruma><YerGostermeler /></Koruma>} />
          <Route path="/profil"     element={<Koruma><Profil /></Koruma>} />
          <Route path="*"           element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
