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
}

export interface GraphResponse {
  project_id: string;
  nodes: any[];
  edges: any[];
}

export interface CryptoInventoryItem {
  asset_id: string;
  language: string;
  algorithm: string;
  operation: string;
  library: string;
  source: string;
  evidence_status: string;
  risk: number | null;
}

export interface CryptoInventoryResponse {
  project_id: string;
  summary: {
    total_assets: number;
    crypto_usages: number;
    languages: number;
    algorithms: number;
    libraries: number;
  };
  items: CryptoInventoryItem[];
  coverage: {
    certificates: string;
    endpoints: string;
    sensitive_data: string;
  };
}

export interface UserProfile {
  id: string;
  username: string;
  email: string;
  created_at?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: UserProfile;
}

const API_BASE = "/api/v1";

function getAuthHeaders(extraHeaders: Record<string, string> = {}): Record<string, string> {
  const headers: Record<string, string> = { ...extraHeaders };
  const token = typeof window !== 'undefined' ? localStorage.getItem("agilegraph_token") : null;
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

async function parseError(res: Response): Promise<Error> {
  const text = await res.text();
  try {
    const data = JSON.parse(text);
    if (data.detail) {
      if (typeof data.detail === 'string') return new Error(data.detail);
      if (Array.isArray(data.detail)) {
        return new Error(data.detail.map((d: any) => d.msg || JSON.stringify(d)).join(', '));
      }
    }
  } catch {}
  return new Error(text || `Request failed with status ${res.status}`);
}

export const apiClient = {
  // Authentication
  register: async (data: { username: string; email: string; password: string }): Promise<AuthResponse> => {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
    if (!res.ok) throw await parseError(res);
    return res.json();
  },

  login: async (data: { username: string; password: string }): Promise<AuthResponse> => {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
    if (!res.ok) throw await parseError(res);
    return res.json();
  },

  getMe: async (): Promise<UserProfile> => {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) throw await parseError(res);
    return res.json();
  },

  logout: async (): Promise<{ message: string }> => {
    const res = await fetch(`${API_BASE}/auth/logout`, {
      method: "POST",
      headers: getAuthHeaders()
    });
    if (!res.ok) throw await parseError(res);
    return res.json();
  },

  // Scanners & Analysis
  scan: async (req: ScanRequest): Promise<ScanResponse> => {
    const res = await fetch(`${API_BASE}/scan`, {
      method: "POST",
      headers: getAuthHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(req)
    });
    if (!res.ok) throw await parseError(res);
    return res.json();
  },

  getGraph: async (project_id: string): Promise<GraphResponse> => {
    const res = await fetch(`${API_BASE}/projects/${project_id}/graph`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) throw await parseError(res);
    return res.json();
  },

  getRisk: async (project_id: string): Promise<RiskResponse> => {
    const res = await fetch(`${API_BASE}/projects/${project_id}/risk`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) throw await parseError(res);
    return res.json();
  },

  getPqcReadiness: async (project_id: string): Promise<any> => {
    const res = await fetch(`${API_BASE}/product/${project_id}/pqc-readiness`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) throw await parseError(res);
    return res.json();
  },

  evaluateMosca: async (req: {x: number, y: number, z: number}): Promise<any> => {
    const res = await fetch(`${API_BASE}/product/mosca`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req)
    });
    if (!res.ok) throw await parseError(res);
    return res.json();
  },

  getMigrationPriority: async (project_id: string, asset_id: string, mosca_status: string = "SAFE"): Promise<any> => {
    const res = await fetch(`${API_BASE}/product/${project_id}/assets/${asset_id}/priority?mosca_status=${mosca_status}`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) throw await parseError(res);
    return res.json();
  },

  getRoadmapState: async (project_id: string, asset_id: string): Promise<any> => {
    const res = await fetch(`${API_BASE}/product/${project_id}/assets/${asset_id}/roadmap`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) throw await parseError(res);
    return res.json();
  },

  transitionRoadmapState: async (project_id: string, asset_id: string, requested_state: string): Promise<any> => {
    const res = await fetch(`${API_BASE}/product/${project_id}/assets/${asset_id}/roadmap`, {
      method: "POST",
      headers: getAuthHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ requested_state })
    });
    if (!res.ok) throw await parseError(res);
    return res.json();
  },

  getCryptoInventory: async (project_id: string): Promise<CryptoInventoryResponse> => {
    const res = await fetch(`${API_BASE}/product/${project_id}/crypto-inventory`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) throw await parseError(res);
    return res.json();
  },

  getReportMarkdown: async (project_id: string): Promise<string> => {
    const res = await fetch(`${API_BASE}/projects/${project_id}/report/markdown`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) throw await parseError(res);
    return res.text();
  }
};
