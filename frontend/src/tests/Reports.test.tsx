// @ts-nocheck
import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import Reports from '../components/Reports';
import { escapeCsvValue } from '../utils/csv';
import { apiClient } from '../api/client';

vi.mock('../api/client', () => ({
  apiClient: {
    getGraph: vi.fn(),
    getRisk: vi.fn(),
    getMigrationPriority: vi.fn(),
  }
}));

const mockSetProjectId = vi.fn();
let currentProjectId = 'test-project';

vi.mock('../context/ProjectContext', () => ({
  useProject: () => ({
    projectId: currentProjectId,
    setProjectId: mockSetProjectId,
  }),
  ProjectProvider: ({ children }: any) => <>{children}</>,
}));

describe('Reports Component', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    currentProjectId = 'test-project';
  });

  describe('CSV escaping and formula injection protection', () => {
    it('neutralizes formula injection characters (=, +, -, @, \\t, \\r, %, |)', () => {
      expect(escapeCsvValue('=1+1')).toBe(`"'=1+1"`);
      expect(escapeCsvValue('+cmd|/c calc')).toBe(`"'+cmd|/c calc"`);
      expect(escapeCsvValue('-2+3')).toBe(`"'-2+3"`);
      expect(escapeCsvValue('@SUM(A1:A10)')).toBe(`"'@SUM(A1:A10)"`);
      expect(escapeCsvValue('\tTAB')).toBe(`"'\tTAB"`);
      expect(escapeCsvValue('\rCR')).toBe(`"'\rCR"`);
      expect(escapeCsvValue('%NAME%')).toBe(`"'%NAME%"`);
      expect(escapeCsvValue('|touch /tmp/pwn')).toBe(`"'|touch /tmp/pwn"`);
    });

    it('neutralizes whitespace-prefixed formula bypasses (e.g., spaces before =)', () => {
      expect(escapeCsvValue('   =1+1')).toBe(`"'   =1+1"`);
      expect(escapeCsvValue('  @SUM(A1:A5)')).toBe(`"'  @SUM(A1:A5)"`);
      expect(escapeCsvValue('\t\t-5+10')).toBe(`"'\t\t-5+10"`);
    });

    it('escapes quotes and wraps values in double quotes', () => {
      expect(escapeCsvValue('Simple Text')).toBe('"Simple Text"');
      expect(escapeCsvValue('Text with "quotes" inside')).toBe('"Text with ""quotes"" inside"');
      expect(escapeCsvValue('Text, with, commas')).toBe('"Text, with, commas"');
      expect(escapeCsvValue(null)).toBe('""');
      expect(escapeCsvValue(undefined)).toBe('""');
      expect(escapeCsvValue(0.75)).toBe('"0.75"');
    });
  });

  describe('UI States & Integration', () => {
    it('renders empty state when no project is selected', () => {
      currentProjectId = '';
      render(<Reports />);
      expect(screen.getByText(/No Project Selected/i)).toBeInTheDocument();
      expect(screen.getByText(/Enter a Project ID above or scan a repository/i)).toBeInTheDocument();
    });

    it('renders error state when API fails', async () => {
      vi.mocked(apiClient.getGraph).mockRejectedValue(new Error('Project not found or not scanned.'));
      vi.mocked(apiClient.getRisk).mockRejectedValue(new Error('Project not found or not scanned.'));

      render(<Reports />);

      await waitFor(() => {
        expect(screen.getByText(/Project not found or not scanned/i)).toBeInTheDocument();
      });
    });

    it('renders no scanned assets when project has empty data', async () => {
      vi.mocked(apiClient.getGraph).mockResolvedValue({ project_id: 'test-project', nodes: [], edges: [] });
      vi.mocked(apiClient.getRisk).mockResolvedValue({
        project_id: 'test-project',
        assets: [],
        ml_status: 'GATv2: BLOCKED',
        expert_validation_status: 'NOT_APPLICABLE'
      });

      render(<Reports />);

      await waitFor(() => {
        expect(screen.getByText(/No Scanned Assets Found/i)).toBeInTheDocument();
      });
    });

    it('renders real project summary, export buttons, and asset preview when data is loaded', async () => {
      vi.mocked(apiClient.getGraph).mockResolvedValue({
        project_id: 'test-project',
        nodes: [
          { id: 'test-project:file1.py', category: 'file' },
          { id: 'test-project:file2.py', category: 'file' },
        ],
        edges: [
          { source: 'test-project:file1.py', target: 'test-project:file2.py' }
        ]
      });

      vi.mocked(apiClient.getRisk).mockResolvedValue({
        project_id: 'test-project',
        assets: [
          {
            asset_id: 'test-project:file1.py',
            score: 0.85,
            formula_version: 'heuristic-v0.1',
            missing_factors: [],
            missing_data_policy: 'RENORMALIZE',
            factors: {
              data_sensitivity: { value: 0.5 },
              asset_criticality: { value: 0.75 }
            }
          }
        ],
        ml_status: 'GATv2: BLOCKED',
        expert_validation_status: 'NOT_APPLICABLE'
      });

      vi.mocked(apiClient.getMigrationPriority).mockResolvedValue({
        priority: 'HIGH',
        rationale: 'High Priority: Critical risk score',
        pqc_relevance: true,
        mosca_status: 'NOT_AT_RISK'
      });

      render(<Reports />);

      // Await loading completion
      await waitFor(() => {
        expect(screen.getByText('Ready for Export')).toBeInTheDocument();
      });

      // Verify stats
      expect(screen.getByText('Total Graph Nodes')).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument(); // 2 nodes
      expect(screen.getByText('Total Graph Edges')).toBeInTheDocument();
      expect(screen.getAllByText('1').length).toBeGreaterThanOrEqual(1); // 1 edge and 1 scored asset

      // Verify buttons
      expect(screen.getByText('CSV Spreadsheet')).toBeInTheDocument();
      expect(screen.getByText('JSON Structured Data')).toBeInTheDocument();

      // Verify asset table preview
      expect(screen.getByText('test-project:file1.py')).toBeInTheDocument();
      expect(screen.getByText('0.8500')).toBeInTheDocument();
      expect(screen.getByText('HIGH')).toBeInTheDocument();
    });

    it('triggers JSON and CSV downloads without errors', async () => {
      vi.mocked(apiClient.getGraph).mockResolvedValue({
        project_id: 'test-project',
        nodes: [{ id: 'test-project:file1.py', category: 'file' }],
        edges: []
      });

      vi.mocked(apiClient.getRisk).mockResolvedValue({
        project_id: 'test-project',
        assets: [{
          asset_id: 'test-project:file1.py',
          score: 0.5,
          factors: {}
        }],
        ml_status: 'GATv2: BLOCKED',
        expert_validation_status: 'NOT_APPLICABLE'
      });

      vi.mocked(apiClient.getMigrationPriority).mockResolvedValue({
        priority: 'MEDIUM',
        rationale: 'Moderate risk',
      });

      // Mock URL and click behaviors
      const createObjectURLMock = vi.fn().mockReturnValue('blob:mock-url');
      const revokeObjectURLMock = vi.fn();
      global.URL.createObjectURL = createObjectURLMock;
      global.URL.revokeObjectURL = revokeObjectURLMock;

      render(<Reports />);

      await waitFor(() => {
        expect(screen.getByText('Ready for Export')).toBeInTheDocument();
      });

      // Click JSON Download
      const jsonBtn = screen.getByText('JSON Structured Data').closest('button');
      fireEvent.click(jsonBtn!);

      expect(createObjectURLMock).toHaveBeenCalled();
      expect(screen.getByText(/JSON report downloaded successfully/i)).toBeInTheDocument();

      // Click CSV Download
      const csvBtn = screen.getByText('CSV Spreadsheet').closest('button');
      fireEvent.click(csvBtn!);

      expect(screen.getByText(/CSV report downloaded successfully/i)).toBeInTheDocument();
    });
  });
});
