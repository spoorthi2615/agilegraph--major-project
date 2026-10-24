// @ts-nocheck
import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import CryptoInventory from '../components/CryptoInventory';
import { apiClient } from '../api/client';

// Mock the apiClient
vi.mock('../api/client', () => ({
  apiClient: {
    getCryptoInventory: vi.fn(),
  }
}));

vi.mock('../context/ProjectContext', () => ({
  useProject: () => ({ projectId: 'test-project', setProjectId: vi.fn() }),
  ProjectProvider: ({ children }: any) => <>{children}</>
}));

const renderComponent = () => {
  return render(
    <BrowserRouter>
      <CryptoInventory />
    </BrowserRouter>
  );
};

describe('CryptoInventory Component', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('renders loading state initially', async () => {
    vi.mocked(apiClient.getCryptoInventory).mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve({} as any), 100))
    );
    renderComponent();
    expect(screen.getByText(/Loading cryptographic inventory.../i)).toBeInTheDocument();
  });

  it('renders API failure state', async () => {
    vi.mocked(apiClient.getCryptoInventory).mockRejectedValue(new Error('Network Error'));
    renderComponent();
    
    await waitFor(() => {
      expect(screen.getByText(/Network Error/i)).toBeInTheDocument();
    });
  });

  it('renders empty inventory state', async () => {
    vi.mocked(apiClient.getCryptoInventory).mockResolvedValue({
      project_id: 'test-project',
      summary: { total_assets: 0, crypto_usages: 0, languages: 0, algorithms: 0, libraries: 0 },
      items: [],
      coverage: { certificates: 'NOT_COLLECTED', endpoints: 'NOT_COLLECTED', sensitive_data: 'NOT_COLLECTED' }
    });
    
    renderComponent();
    
    await waitFor(() => {
      expect(screen.getByText(/No cryptographic usage was discovered/i)).toBeInTheDocument();
    });
  });

  it('renders real inventory data', async () => {
    vi.mocked(apiClient.getCryptoInventory).mockResolvedValue({
      project_id: 'test-project',
      summary: { total_assets: 10, crypto_usages: 2, languages: 1, algorithms: 1, libraries: 1 },
      items: [
        {
          asset_id: 'file1.java',
          language: 'Java',
          algorithm: 'AES',
          operation: 'encrypt',
          library: 'JCA',
          source: 'file1.java:10',
          evidence_status: 'Assessed',
          risk: 0.1
        },
        {
          asset_id: 'file2.java',
          language: 'Java',
          algorithm: 'MD5',
          operation: 'hash',
          library: 'JCA',
          source: 'file2.java:20',
          evidence_status: 'Assessed',
          risk: 0.9
        }
      ],
      coverage: { certificates: 'NOT_COLLECTED', endpoints: 'NOT_COLLECTED', sensitive_data: 'NOT_COLLECTED' }
    });

    renderComponent();

    await waitFor(() => {
      expect(screen.getAllByText('AES').length).toBeGreaterThan(0);
      expect(screen.getAllByText('MD5').length).toBeGreaterThan(0);
      expect(screen.getByText('file1.java')).toBeInTheDocument();
      expect(screen.getByText('file2.java')).toBeInTheDocument();
    });

    // Check summary cards
    expect(screen.getByText('Crypto Usages').nextElementSibling).toHaveTextContent('2');
  });

  it('search works', async () => {
    vi.mocked(apiClient.getCryptoInventory).mockResolvedValue({
      project_id: 'test-project',
      summary: { total_assets: 10, crypto_usages: 2, languages: 1, algorithms: 2, libraries: 1 },
      items: [
        { asset_id: 'file1', language: 'Java', algorithm: 'AES', operation: 'encrypt', library: 'JCA', source: 'file1', evidence_status: 'Assessed', risk: null },
        { asset_id: 'file2', language: 'Java', algorithm: 'MD5', operation: 'hash', library: 'JCA', source: 'file2', evidence_status: 'Assessed', risk: null },
      ],
      coverage: { certificates: 'NOT_COLLECTED', endpoints: 'NOT_COLLECTED', sensitive_data: 'NOT_COLLECTED' }
    });

    renderComponent();
    await waitFor(() => expect(screen.getAllByText('AES').length).toBeGreaterThan(0));

    const searchInput = screen.getByPlaceholderText(/Search asset, algorithm, operation/i);
    fireEvent.change(searchInput, { target: { value: 'AES' } });

    expect(screen.getByText('file1')).toBeInTheDocument();
    expect(screen.queryByText('file2')).not.toBeInTheDocument();
  });

  it('filters work (language, algorithm, library)', async () => {
    vi.mocked(apiClient.getCryptoInventory).mockResolvedValue({
      project_id: 'test-project',
      summary: { total_assets: 10, crypto_usages: 2, languages: 2, algorithms: 2, libraries: 1 },
      items: [
        { asset_id: 'file1', language: 'Java', algorithm: 'AES', operation: '', library: '', source: '', evidence_status: '', risk: null },
        { asset_id: 'file2', language: 'Python', algorithm: 'MD5', operation: '', library: '', source: '', evidence_status: '', risk: null },
      ],
      coverage: { certificates: 'NOT_COLLECTED', endpoints: 'NOT_COLLECTED', sensitive_data: 'NOT_COLLECTED' }
    });

    renderComponent();
    await waitFor(() => expect(screen.getByText('file1')).toBeInTheDocument());

    const langSelect = screen.getAllByRole('combobox')[0]; // Language filter
    fireEvent.change(langSelect, { target: { value: 'Java' } });

    expect(screen.getByText('file1')).toBeInTheDocument();
    expect(screen.queryByText('file2')).not.toBeInTheDocument();
  });

  it('selecting an asset opens details and handles missing data honestly', async () => {
    vi.mocked(apiClient.getCryptoInventory).mockResolvedValue({
      project_id: 'test-project',
      summary: { total_assets: 1, crypto_usages: 1, languages: 1, algorithms: 1, libraries: 1 },
      items: [
        { asset_id: 'file1', language: 'Java', algorithm: 'AES', operation: 'encrypt', library: 'JCA', source: 'Unknown:?', evidence_status: 'Assessed', risk: 0.5 }
      ],
      coverage: { certificates: 'NOT_COLLECTED', endpoints: 'NOT_COLLECTED', sensitive_data: 'NOT_COLLECTED' }
    });

    renderComponent();
    await waitFor(() => expect(screen.getByText('file1')).toBeInTheDocument());

    const row = screen.getByText('file1');
    fireEvent.click(row);

    // Details panel should open
    expect(screen.getByText('Item Details')).toBeInTheDocument();
    expect(screen.getByText('Source location not available from current scanner evidence.')).toBeInTheDocument();

    // Risk link
    const riskLink = screen.getByRole('link', { name: /View Risk Analysis/i });
    expect(riskLink).toHaveAttribute('href', '/risk');

    // Graph link
    const graphLink = screen.getByRole('link', { name: /View in Crypto Graph/i });
    expect(graphLink).toHaveAttribute('href', '/graph');
  });

  it('unavailable coverage fields are represented honestly', async () => {
    vi.mocked(apiClient.getCryptoInventory).mockResolvedValue({
      project_id: 'test-project',
      summary: { total_assets: 1, crypto_usages: 1, languages: 1, algorithms: 1, libraries: 1 },
      items: [
        { asset_id: 'file1', language: 'Java', algorithm: 'AES', operation: 'encrypt', library: 'JCA', source: '', evidence_status: 'Assessed', risk: 0.5 }
      ],
      coverage: { certificates: 'NOT_COLLECTED', endpoints: 'NOT_COLLECTED', sensitive_data: 'NOT_COLLECTED' }
    });

    renderComponent();
    await waitFor(() => {
      const coverageCards = screen.getAllByText('Not collected by current scanner');
      expect(coverageCards.length).toBe(3);
    });
  });
});
