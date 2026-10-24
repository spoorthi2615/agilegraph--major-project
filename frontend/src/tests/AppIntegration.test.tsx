// @ts-nocheck
import { render, screen, fireEvent } from '@testing-library/react';
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
    vi.mocked(apiClient.getRisk).mockResolvedValue({
      project_id: "demo-project",
      assets: []
    });
    vi.mocked(apiClient.getGraph).mockResolvedValue({
      nodes: [],
      edges: []
    });

    render(<App />);

    // Initially on Overview -> Dashboard should be visible
    expect(screen.getByText(/Project Overview/i)).toBeInTheDocument();

    // Click PQC Readiness
    const pqcLinks = screen.getAllByRole('link', { name: /PQC Readiness/i });
    fireEvent.click(pqcLinks[0]);
    expect(await screen.findByText(/PQC Readiness/i, { selector: 'h2' })).toBeInTheDocument();

    // Click Mosca Readiness
    const moscaLink = screen.getByRole('link', { name: /Mosca Readiness/i });
    fireEvent.click(moscaLink);
    expect(await screen.findByText(/Mosca Readiness/i, { selector: 'h2' })).toBeInTheDocument();

    // Click Migration Priority
    const priorityLinks = screen.getAllByRole('link', { name: /Migration Priority/i });
    fireEvent.click(priorityLinks[0]);
    expect(await screen.findByText(/Migration Priority/i, { selector: 'h2' })).toBeInTheDocument();

    // Click Migration Roadmap
    const roadmapLinks = screen.getAllByRole('link', { name: /Migration Roadmap/i });
    fireEvent.click(roadmapLinks[0]);
    expect(await screen.findByText(/Migration Roadmap/i, { selector: 'h2' })).toBeInTheDocument();

    // Click Crypto Inventory
    const inventoryLinks = screen.getAllByRole('link', { name: /Crypto Inventory/i });
    fireEvent.click(inventoryLinks[0]);
    expect(await screen.findByText(/Cryptographic Inventory/i, { selector: 'h2' })).toBeInTheDocument();

    // Click Reports
    const reportsLink = screen.getByRole('link', { name: /Reports/i });
    fireEvent.click(reportsLink);
    expect(await screen.findByText(/Reports/i, { selector: 'h2' })).toBeInTheDocument();

    // Click Risk Analysis
    const riskLink = screen.getByRole('link', { name: /Risk Analysis/i });
    fireEvent.click(riskLink);
    expect(await screen.findByText(/Risk Analysis/i, { selector: 'h2' })).toBeInTheDocument();

    // Click Crypto Graph
    const graphLink = screen.getByRole('link', { name: /Crypto Graph/i });
    fireEvent.click(graphLink);
    expect(await screen.findByText(/Crypto Graph/i, { selector: 'h2' })).toBeInTheDocument();
  });
});
