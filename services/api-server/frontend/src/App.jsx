import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import LeadBrowser from './pages/LeadBrowser';
import LeadDetail from './pages/LeadDetail';
import Pipeline from './pages/Pipeline';
import ContractorDirectory from './pages/ContractorDirectory';
import ContractorProfile from './pages/ContractorProfile';
import MarketMaps from './pages/MarketMaps';
import Alerts from './pages/Alerts';

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/leads" element={<LeadBrowser />} />
        <Route path="/leads/:id" element={<LeadDetail />} />
        <Route path="/pipeline" element={<Pipeline />} />
        <Route path="/contractors" element={<ContractorDirectory />} />
        <Route path="/contractors/:id" element={<ContractorProfile />} />
        <Route path="/markets" element={<MarketMaps />} />
        <Route path="/alerts" element={<Alerts />} />
      </Route>
    </Routes>
  );
}
