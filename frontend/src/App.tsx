// @ts-nocheck
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './components/Dashboard';
import CryptoInventory from './components/CryptoInventory';
import Reports from './components/Reports';
import PqcReadiness from './components/product/PqcReadiness';
import MoscaReadiness from './components/product/MoscaReadiness';
import MigrationPriority from './components/product/MigrationPriority';
import MigrationRoadmap from './components/product/MigrationRoadmap';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/inventory" element={<CryptoInventory />} />
          <Route path="/risk" element={<Dashboard />} />
          <Route path="/graph" element={<Dashboard />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/pqc-readiness" element={<PqcReadiness />} />
          <Route path="/mosca" element={<MoscaReadiness />} />
          <Route path="/priority" element={<MigrationPriority />} />
          <Route path="/roadmap" element={<MigrationRoadmap />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
