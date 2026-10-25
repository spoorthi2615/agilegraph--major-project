// @ts-nocheck
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
    getMe: vi.fn(),
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
  }
}));

describe('App Integration & Routing Tests', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    localStorage.clear();
  });

  it('renders the public landing page at root /', async () => {
    window.history.pushState({}, '', '/');
    render(<App />);

    // Landing page header and brand
    expect(screen.getAllByText(/AgileGraph/i)[0]).toBeInTheDocument();
    expect(screen.getAllByText(/Platform Capabilities/i)[0]).toBeInTheDocument();
    expect(screen.getAllByText(/How It Works/i)[0]).toBeInTheDocument();
    expect(screen.getAllByText(/Research & Methodology/i)[0]).toBeInTheDocument();
    expect(screen.getAllByText(/Technology Stack/i)[0]).toBeInTheDocument();

    // CTA links
    expect(screen.getAllByRole('link', { name: /Sign In/i })[0]).toBeInTheDocument();
    expect(screen.getAllByRole('link', { name: /Get Started/i })[0]).toBeInTheDocument();
  });

  it('redirects unauthenticated user accessing /app to /login', async () => {
    window.history.pushState({}, '', '/app');
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/Sign in to your account/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Sign In/i })).toBeInTheDocument();
    });
  });

  it('11. Navigates between all required routes when authenticated', async () => {
    localStorage.setItem('agilegraph_token', 'test-valid-token');
    localStorage.setItem(
      'agilegraph_user',
      JSON.stringify({
        username: 'researcher',
        email: 'researcher@agilegraph.org',
        role: 'researcher'
      })
    );

    vi.mocked(apiClient.getMe).mockResolvedValue({
      username: 'researcher',
      email: 'researcher@agilegraph.org',
      role: 'researcher'
    });
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

    window.history.pushState({}, '', '/app');
    render(<App />);

    // Initially on Overview -> Dashboard should be visible
    expect(await screen.findByText(/Project Overview/i)).toBeInTheDocument();

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

