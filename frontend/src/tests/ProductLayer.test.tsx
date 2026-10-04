// @ts-nocheck
/// <reference types="@testing-library/jest-dom" />
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';

import PqcReadiness from '../components/product/PqcReadiness';
import MoscaReadiness from '../components/product/MoscaReadiness';
import MigrationPriority from '../components/product/MigrationPriority';
import MigrationRoadmap from '../components/product/MigrationRoadmap';
import { apiClient } from '../api/client';

vi.mock('../api/client', () => ({
  apiClient: {
    getPqcReadiness: vi.fn(),
    evaluateMosca: vi.fn(),
    getRisk: vi.fn(),
    getMigrationPriority: vi.fn(),
    getRoadmapState: vi.fn(),
    transitionRoadmapState: vi.fn(),
  }
}));

describe('Product Layer Components', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  describe('PqcReadiness', () => {
    it('1. PQC readiness renders real API fields', async () => {
      vi.mocked(apiClient.getPqcReadiness).mockResolvedValue({
        status: "Preliminary heuristic \u2014 expert validation pending",
        semantic_disclaimer: "Inventory/coverage summary, not a scientifically validated PQC readiness score.",
        asset_count: 5,
        assessed_assets: 4,
        insufficient_evidence_assets: 1,
        assets_requiring_attention: 2,
        migration_candidates: 2,
        recognized_algorithms: ["rsa", "aes"],
        unknown_algorithms: 1
      });

      render(<PqcReadiness />);
      // Fetch is called on mount, so just wait
      await waitFor(() => {
        expect(screen.getByText('Total Assets')).toBeInTheDocument();
        expect(screen.getByText('5')).toBeInTheDocument();
        expect(screen.getByText('rsa')).toBeInTheDocument();
      });
    });

    it('2. Readiness disclaimer is visible', async () => {
      vi.mocked(apiClient.getPqcReadiness).mockResolvedValue({
        status: "Preliminary heuristic \u2014 expert validation pending",
        semantic_disclaimer: "Inventory/coverage summary, not a scientifically validated PQC readiness score.",
      });

      render(<PqcReadiness />);

      await waitFor(() => {
        expect(screen.getByText(/Preliminary heuristic/)).toBeInTheDocument();
        expect(screen.getByText(/Inventory\/coverage summary, not a scientifically validated PQC readiness score/)).toBeInTheDocument();
      });
    });

    it('10. API failure produces a usable error state', async () => {
      vi.mocked(apiClient.getPqcReadiness).mockRejectedValue(new Error("Network Error"));
      
      render(<PqcReadiness />);

      await waitFor(() => {
        expect(screen.getByText('Network Error')).toBeInTheDocument();
      });
    });
  });

  describe('MoscaReadiness', () => {
    it('3. Mosca equality renders NOT_AT_RISK', async () => {
      vi.mocked(apiClient.evaluateMosca).mockResolvedValue({
        total: 30, z: 30, status: "NOT_AT_RISK", explanation: "x + y <= z"
      });

      render(<MoscaReadiness />);
      fireEvent.click(screen.getByText('Evaluate Mosca'));

      await waitFor(() => {
        expect(screen.getByText('NOT_AT_RISK')).toBeInTheDocument();
      });
    });

    it('4. Mosca insufficient data renders correctly', async () => {
      vi.mocked(apiClient.evaluateMosca).mockResolvedValue({
        total: null, z: 30, status: "INSUFFICIENT_DATA", explanation: "Missing x"
      });

      render(<MoscaReadiness />);
      fireEvent.click(screen.getByText('Evaluate Mosca'));

      await waitFor(() => {
        expect(screen.getByText('INSUFFICIENT_DATA')).toBeInTheDocument();
      });
    });
  });

  describe('MigrationPriority', () => {
    it('5. Migration priority keeps risk and priority visually separate', async () => {
      vi.mocked(apiClient.getRisk).mockResolvedValue({ assets: [{ asset_id: "a1" }] } as any);
      vi.mocked(apiClient.getMigrationPriority).mockResolvedValue({
        priority: "HIGH",
        risk_score: 0.85,
        mosca_status: "AT_RISK",
        mosca_provenance: "planning input"
      });

      render(<MigrationPriority />);

      await waitFor(() => {
        expect(screen.getByText('HIGH')).toBeInTheDocument();
        expect(screen.getByText('0.85')).toBeInTheDocument();
      });
    });

    it('6. NOT_ASSESSED does not render as zero', async () => {
      vi.mocked(apiClient.getRisk).mockResolvedValue({ assets: [{ asset_id: "a2" }] } as any);
      vi.mocked(apiClient.getMigrationPriority).mockResolvedValue({
        priority: "NOT_ASSESSED",
        risk_score: null
      });

      render(<MigrationPriority />);

      await waitFor(() => {
        expect(screen.getByText('NOT_ASSESSED')).toBeInTheDocument();
        expect(screen.getByText('Not assessed')).toBeInTheDocument();
        expect(screen.queryByText('0')).not.toBeInTheDocument();
      });
    });
  });

  describe('MigrationRoadmap', () => {
    it('7. Roadmap valid transition works', async () => {
      vi.mocked(apiClient.getRisk).mockResolvedValue({ assets: [{ asset_id: "a1" }] } as any);
      vi.mocked(apiClient.getRoadmapState).mockResolvedValue({ current_state: "NOT_ASSESSED" });
      vi.mocked(apiClient.transitionRoadmapState).mockResolvedValue({ current_state: "ASSESSMENT_REQUIRED" });

      render(<MigrationRoadmap />);

      await waitFor(() => {
        expect(screen.getAllByText('NOT_ASSESSED').length).toBeGreaterThan(0);
      });

      const btn = await screen.findByRole('button', { name: 'ASSESSMENT_REQUIRED' });
      fireEvent.click(btn);

      await waitFor(() => {
        expect(apiClient.transitionRoadmapState).toHaveBeenCalledWith('demo-project', 'a1', 'ASSESSMENT_REQUIRED');
      });
    });

    it('8. Invalid transition displays an error', async () => {
      vi.mocked(apiClient.getRisk).mockResolvedValue({ assets: [{ asset_id: "a1" }] } as any);
      vi.mocked(apiClient.getRoadmapState).mockResolvedValue({ current_state: "NOT_ASSESSED" });
      vi.mocked(apiClient.transitionRoadmapState).mockRejectedValue(new Error("Invalid state transition"));

      render(<MigrationRoadmap />);

      await waitFor(() => {
        expect(screen.queryAllByRole('button', { name: 'VERIFIED' }).length).toBeGreaterThan(0);
      });

      const btns = screen.getAllByRole('button', { name: 'VERIFIED' });
      fireEvent.click(btns[0]);

      await waitFor(() => {
        const p = screen.getAllByText(/Transition failed for a1:/);
        expect(p.length).toBeGreaterThan(0);
      });
    });

    it('9. MIGRATED and VERIFIED are distinct', async () => {
      vi.mocked(apiClient.getRisk).mockResolvedValue({ assets: [{ asset_id: "a1" }, { asset_id: "a2" }] } as any);
      vi.mocked(apiClient.getRoadmapState).mockImplementation(async (_, id) => {
        return { current_state: id === "a1" ? "MIGRATED" : "VERIFIED" };
      });

      render(<MigrationRoadmap />);

      await waitFor(() => {
        expect(screen.queryAllByRole('button', { name: 'VERIFIED' }).length).toBeGreaterThan(0);
      });

      const migratedSpans = screen.getAllByText('MIGRATED', { selector: 'span' });
      const verifiedSpans = screen.getAllByText('VERIFIED', { selector: 'span' });
      // The last ones in the DOM are the actual pills (after the disclaimer)
      expect(migratedSpans[migratedSpans.length - 1].className).not.toEqual(verifiedSpans[verifiedSpans.length - 1].className);
    });
  });
});
