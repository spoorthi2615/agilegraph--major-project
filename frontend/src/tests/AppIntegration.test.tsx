// @ts-nocheck
/// <reference types="@testing-library/jest-dom" />
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from '../App';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { apiClient } from '../api/client';

vi.mock('../api/client', () => ({
  apiClient: {
    getPqcReadiness: vi.fn(),
    evaluateMosca: vi.fn(),
    getMigrationPriority: vi.fn(),
    getRoadmapState: vi.fn(),
    transitionRoadmapState: vi.fn(),
    scan: vi.fn(),
    getGraph: vi.fn(),
    getRisk: vi.fn(),
  }
}));

describe('App Integration & Routing Tests', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('11. Navigates between all required routes', async () => {
    vi.mocked(apiClient.getPqcReadiness).mockResolvedValue({
      project_id: "demo-project",
      pqc_algorithm_found: false,
      readiness_summary: "No post-quantum algorithms detected.",
      evidence: []
    });

    render(<App />);

    // Initially on Overview -> Dashboard should be visible
    expect(screen.getByText(/AgileGraph Analysis Dashboard/i)).toBeInTheDocument();

    // Click PQC Readiness
    const pqcLink = screen.getByRole('link', { name: /PQC Readiness/i });
    fireEvent.click(pqcLink);
    expect(await screen.findByText(/PQC Readiness/i, { selector: 'h2' })).toBeInTheDocument();

    // Click Mosca Readiness
    const moscaLink = screen.getByRole('link', { name: /Mosca Readiness/i });
    fireEvent.click(moscaLink);
    expect(await screen.findByText(/Mosca Readiness/i, { selector: 'h2' })).toBeInTheDocument();

    // Click Migration Priority
    const priorityLink = screen.getByRole('link', { name: /Migration Priority/i });
    fireEvent.click(priorityLink);
    expect(await screen.findByText(/Migration Priority/i, { selector: 'h2' })).toBeInTheDocument();

    // Click Migration Roadmap
    const roadmapLink = screen.getByRole('link', { name: /Migration Roadmap/i });
    fireEvent.click(roadmapLink);
    expect(await screen.findByText(/Migration Roadmap/i, { selector: 'h2' })).toBeInTheDocument();

    // Click Crypto Inventory
    const inventoryLink = screen.getByRole('link', { name: /Crypto Inventory/i });
    fireEvent.click(inventoryLink);
    expect(await screen.findByText(/Crypto Inventory/i, { selector: 'h2' })).toBeInTheDocument();

    // Click Reports
    const reportsLink = screen.getByRole('link', { name: /Reports/i });
    fireEvent.click(reportsLink);
    expect(await screen.findByText(/Reports/i, { selector: 'h2' })).toBeInTheDocument();

    // Click Risk Analysis
    const riskLink = screen.getByRole('link', { name: /Risk Analysis/i });
    fireEvent.click(riskLink);
    expect(await screen.findByText(/Heuristic Risk Decomposition/i)).toBeInTheDocument();

    // Click Crypto Graph
    const graphLink = screen.getByRole('link', { name: /Crypto Graph/i });
    fireEvent.click(graphLink);
    expect(await screen.findByText(/AgileGraph Topology/i)).toBeInTheDocument();
  });
});
