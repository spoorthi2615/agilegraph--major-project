// @ts-nocheck
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './components/Dashboard';
import CryptoInventory from './components/CryptoInventory';
import RiskAnalysis from './components/RiskAnalysis';
import CryptoGraph from './components/CryptoGraph';
import Reports from './components/Reports';
import PqcReadiness from './components/product/PqcReadiness';
import MoscaReadiness from './components/product/MoscaReadiness';
import MigrationPriority from './components/product/MigrationPriority';
import MigrationRoadmap from './components/product/MigrationRoadmap';
import LandingPage from './components/LandingPage';
import LoginPage from './components/auth/LoginPage';
import RegisterPage from './components/auth/RegisterPage';
import ProtectedRoute from './components/ProtectedRoute';
import { ProjectProvider } from './context/ProjectContext';
import { AuthProvider } from './context/AuthContext';

function App() {
  return (
    <AuthProvider>
      <ProjectProvider>
        <BrowserRouter>
          <Routes>
            {/* Public Routes */}
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />

            {/* Protected Routes (Dashboard App) */}
            <Route
              path="/app"
              element={
                <ProtectedRoute>
                  <Layout>
                    <Dashboard />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/inventory"
              element={
                <ProtectedRoute>
                  <Layout>
                    <CryptoInventory />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/risk"
              element={
                <ProtectedRoute>
                  <Layout>
                    <RiskAnalysis />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/graph"
              element={
                <ProtectedRoute>
                  <Layout>
                    <CryptoGraph />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/reports"
              element={
                <ProtectedRoute>
                  <Layout>
                    <Reports />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/pqc-readiness"
              element={
                <ProtectedRoute>
                  <Layout>
                    <PqcReadiness />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/mosca"
              element={
                <ProtectedRoute>
                  <Layout>
                    <MoscaReadiness />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/priority"
              element={
                <ProtectedRoute>
                  <Layout>
                    <MigrationPriority />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/roadmap"
              element={
                <ProtectedRoute>
                  <Layout>
                    <MigrationRoadmap />
                  </Layout>
                </ProtectedRoute>
              }
            />

            {/* Fallback to Landing */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </ProjectProvider>
    </AuthProvider>
  );
}

export default App;

