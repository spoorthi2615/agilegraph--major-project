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

export interface FactorContribution {
  value: number;
  weight: number;
  contribution: number;
}

export interface RiskScore {
  asset_id: string;
  score: number;
  scale?: string;
  formula_version?: string;
  weights?: Record<string, number>;
  factors?: Record<string, any>;
  weighted_contributions?: Record<string, FactorContribution>;
  missing_factors?: string[];
  missing_data_policy?: string;
  assumptions?: string[];
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
  },

  getPqcReadiness: async (project_id: string): Promise<any> => {
    const res = await fetch(`${API_BASE}/product/${project_id}/pqc-readiness`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  evaluateMosca: async (req: {x: number, y: number, z: number}): Promise<any> => {
    const res = await fetch(`${API_BASE}/product/mosca`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req)
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  getMigrationPriority: async (project_id: string, asset_id: string, mosca_status: string = "NOT_AT_RISK"): Promise<any> => {
    const res = await fetch(`${API_BASE}/product/${project_id}/assets/${asset_id}/priority?mosca_status=${mosca_status}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  getRoadmapState: async (project_id: string, asset_id: string): Promise<any> => {
    const res = await fetch(`${API_BASE}/product/${project_id}/assets/${asset_id}/roadmap`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  transitionRoadmapState: async (project_id: string, asset_id: string, requested_state: string): Promise<any> => {
    const res = await fetch(`${API_BASE}/product/${project_id}/assets/${asset_id}/roadmap`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ requested_state })
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }
};

