// @ts-nocheck
import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import RiskAnalysis from '../components/RiskAnalysis';
import { apiClient } from '../api/client';

vi.mock('../api/client', () => ({
  apiClient: {
    getRisk: vi.fn(),
    getGraph: vi.fn(),
    getAssetExplanation: vi.fn(),
    scan: vi.fn(),
  }
}));

const mockSetProjectId = vi.fn();
let currentProjectId = 'test-project';

vi.mock('../context/ProjectContext', () => ({
  useProject: () => ({
    projectId: currentProjectId,
    setProjectId: mockSetProjectId,
  }),
}));

describe('RiskAnalysis Explainability Drawer Integration', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    currentProjectId = 'test-project';
  });

  it('renders explainability drawer when an asset is selected', async () => {
    vi.mocked(apiClient.getRisk).mockResolvedValue({
      project_id: 'test-project',
      assets: [
        {
          asset_id: 'src/crypto/rsa.py',
          score: 0.85,
          scale: '0.0-1.0',
          formula_version: 'heuristic-v0.1',
          missing_factors: [],
          missing_data_policy: 'RENORMALIZE',
          weighted_contributions: {
            crypto_weakness: { value: 0.9, weight: 0.25, contribution: 0.225 }
          }
        }
      ],
      ml_status: 'ARCHITECTURAL_PROTOTYPE'
    });

    vi.mocked(apiClient.getGraph).mockResolvedValue({
      project_id: 'test-project',
      nodes: [{ id: 'src/crypto/rsa.py', category: 'file' }],
      edges: []
    });

    vi.mocked(apiClient.getAssetExplanation).mockResolvedValue({
      asset_id: 'src/crypto/rsa.py',
      project_id: 'test-project',
      target_node_idx: 0,
      heuristic_decomposition: {
        status: 'COMPUTED',
        method: 'HEURISTIC_LINEAR_DECOMPOSITION',
        formula_version: 'heuristic-v0.1',
        total_risk_score: 0.85,
        missing_factors: [],
        missing_data_policy: 'RENORMALIZE',
        factor_contributions: {},
        caveat: 'Additive linear decomposition of rule prior'
      },
      gnn_feature_attributions: [
        { feature_name: 'crypto_weakness', importance: 0.45, normalized_importance: 0.45 },
        { feature_name: 'migration_difficulty', importance: 0.35, normalized_importance: 0.35 }
      ],
      top_influential_edges: [
        {
          edge_type: 'file->uses_crypto->crypto_usage',
          source_type: 'file',
          source_idx: 0,
          relation: 'uses_crypto',
          target_type: 'crypto_usage',
          target_idx: 1,
          importance: 0.78,
          direct_incident: true
        }
      ],
      ml_status: 'ARCHITECTURAL_PROTOTYPE',
      caveat: 'GNNExplainer attributions reflect the model approximation of weak-supervision heuristic rules'
    });

    render(<RiskAnalysis />);

    // Wait for table to load
    await waitFor(() => {
      expect(screen.getByText('src/crypto/rsa.py')).toBeInTheDocument();
    });

    // Click on the asset row to open explanation drawer
    fireEvent.click(screen.getByText('src/crypto/rsa.py'));

    await waitFor(() => {
      expect(screen.getByText('Explainability Attribution')).toBeInTheDocument();
      expect(screen.getByText('crypto_weakness')).toBeInTheDocument();
      expect(screen.getByText('45.0%')).toBeInTheDocument();
      expect(screen.getByText('uses_crypto')).toBeInTheDocument();
      expect(screen.getByText('Methodological Disclosure:')).toBeInTheDocument();
    });
  });

  it('switches between V1 Baseline and V2 Calibrated experimental engine', async () => {
    vi.mocked(apiClient.getRisk).mockResolvedValue({
      project_id: 'test-project',
      active_engine_version: 'v1',
      available_engine_versions: ['v1', 'v2'],
      assets: [
        {
          asset_id: 'src/crypto/rsa.py',
          score: 0.85,
          scale: '0.0-1.0',
          formula_version: 'heuristic-v1.0',
          engine_version: 'v1',
          heuristic_label: 'HIGH',
          comparison: {
            v1: { score: 0.85, label: 'HIGH', formula_version: 'heuristic-v1.0' },
            v2: { score: 0.85, label: 'HIGH', formula_version: 'heuristic-v2.0-experimental' }
          }
        }
      ],
      ml_status: 'ARCHITECTURAL_PROTOTYPE'
    });

    vi.mocked(apiClient.getGraph).mockResolvedValue({
      project_id: 'test-project',
      nodes: [{ id: 'src/crypto/rsa.py', category: 'file' }],
      edges: []
    });

    render(<RiskAnalysis />);

    // Default V1 should be selected
    await waitFor(() => {
      expect(screen.getByText('V1 Baseline (Default)')).toBeInTheDocument();
      expect(screen.getByText('V2 Calibrated (Experimental)')).toBeInTheDocument();
    });

    // Switch to V2
    fireEvent.click(screen.getByText('V2 Calibrated (Experimental)'));

    await waitFor(() => {
      expect(apiClient.getRisk).toHaveBeenCalledWith('test-project', 'v2');
      expect(screen.getByText(/Engine V2 Active: Calibrated Heuristic/i)).toBeInTheDocument();
    });

    // Switch back to V1
    fireEvent.click(screen.getByText('V1 Baseline (Default)'));

    await waitFor(() => {
      expect(apiClient.getRisk).toHaveBeenCalledWith('test-project', 'v1');
    });
  });
});

