export interface ScanRequest {
  repository_path: string;
  project_id: string;
}

export interface ScanResponse {
  project_id: string;
  status: string;
  message: string;
  asset_count?: number;
}

export interface RiskScore {
  asset_id: string;
  score: number;
  data_sensitivity?: number;
  asset_criticality?: number;
  internet_exposure?: number;
  crypto_weakness?: number;
  cve_risk?: number;
  library_centrality?: number;
  migration_difficulty?: number;
}

export interface RiskResponse {
  project_id: string;
  assets: RiskScore[];
  ml_status: string;
  expert_validation_status: string;
}

export interface GraphResponse {
  project_id: string;
  nodes: any[];
  edges: any[];
}

const API_BASE = "/api/v1";

export const apiClient = {
  scan: async (req: ScanRequest): Promise<ScanResponse> => {
    const res = await fetch(`${API_BASE}/scan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req)
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  getGraph: async (project_id: string): Promise<GraphResponse> => {
    const res = await fetch(`${API_BASE}/projects/${project_id}/graph`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  getRisk: async (project_id: string): Promise<RiskResponse> => {
    const res = await fetch(`${API_BASE}/projects/${project_id}/risk`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }
};
