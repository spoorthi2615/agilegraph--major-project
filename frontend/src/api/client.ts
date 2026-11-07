export interface ScanRequest {
  repository_path: string;
  project_id: string;
  engine_version?: string;
}

export interface ScanResponse {
  project_id: string;
  status: string;
  message: string;
  asset_count?: number;
  engine_version?: string;
  available_engine_versions?: string[];
}

export interface FactorContribution {
  value: number;
  weight: number;
  contribution: number;
}

export interface RiskScore {
  asset_id: string;
  score: number | null;
  scale?: string;
  formula_version?: string;
  engine_version?: string;
  heuristic_label?: string;
  v1_score?: number | null;
  v1_label?: string | null;
  v2_score?: number | null;
  v2_label?: string | null;
  comparison?: {
    v1: { score: number | null; label: string | null; formula_version: string };
    v2: { score: number | null; label: string | null; formula_version: string };
  };
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
  active_engine_version?: string;
  available_engine_versions?: string[];
  ml_status: string;
}

export interface GraphResponse {
  project_id: string;
  nodes: any[];
  edges: any[];
}

export interface FeatureAttribution {
  feature_name: string;
  importance: number;
  normalized_importance: number;
}

export interface InfluentialEdge {
  edge_type: string;
  source_type: string;
  source_idx: number;
  relation: string;
  target_type: string;
  target_idx: number;
  importance: number;
  direct_incident: boolean;
}

export interface GNNExplanationResponse {
  asset_id: string;
  project_id: string;
  target_node_idx: number | null;
  heuristic_decomposition: {
    status: string;
    method: string;
    formula_version: string;
    total_risk_score: number | null;
    missing_factors: string[];
    missing_data_policy: string;
    factor_contributions: Record<string, any>;
    caveat: string;
  };
  gnn_feature_attributions: FeatureAttribution[];
  top_influential_edges: InfluentialEdge[];
  ml_status: string;
  caveat: string;
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

// Lightweight client-side response cache with short TTL (30s)
const apiCache = new Map<string, { data: any; expiry: number }>();

export function clearApiCache(prefix?: string) {
  if (!prefix) {
    apiCache.clear();
    return;
  }
  for (const k of apiCache.keys()) {
    if (k.includes(prefix)) {
      apiCache.delete(k);
    }
  }
}

function getCached<T>(key: string): T | null {
  const item = apiCache.get(key);
  if (item && item.expiry > Date.now()) {
    return item.data as T;
  }
  apiCache.delete(key);
  return null;
}

function setCached(key: string, data: any, ttlMs: number = 30000) {
  apiCache.set(key, { data, expiry: Date.now() + ttlMs });
}

export const apiClient = {
  // Authentication
  register: async (data: { username: string; email: string; password: string }): Promise<AuthResponse> => {
    clearApiCache();
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
    if (!res.ok) throw await parseError(res);
    return res.json();
  },

  login: async (data: { username: string; password: string }): Promise<AuthResponse> => {
    clearApiCache();
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
    clearApiCache();
    const res = await fetch(`${API_BASE}/auth/logout`, {
      method: "POST",
      headers: getAuthHeaders()
    });
    if (!res.ok) throw await parseError(res);
    return res.json();
  },

  // Scanners & Analysis
  scan: async (req: ScanRequest): Promise<ScanResponse> => {
    clearApiCache(req.project_id);
    const res = await fetch(`${API_BASE}/scan`, {
      method: "POST",
      headers: getAuthHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(req)
    });
    if (!res.ok) throw await parseError(res);
    return res.json();
  },

  getGraph: async (project_id: string): Promise<GraphResponse> => {
    const cacheKey = `graph:${project_id}`;
    const cached = getCached<GraphResponse>(cacheKey);
    if (cached) return cached;

    const res = await fetch(`${API_BASE}/projects/${project_id}/graph`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) throw await parseError(res);
    const data = await res.json();
    setCached(cacheKey, data);
    return data;
  },

  getRisk: async (project_id: string, engine_version?: string): Promise<RiskResponse> => {
    const cacheKey = `risk:${project_id}:${engine_version || "default"}`;
    const cached = getCached<RiskResponse>(cacheKey);
    if (cached) return cached;

    const url = engine_version
      ? `${API_BASE}/projects/${project_id}/risk?engine_version=${encodeURIComponent(engine_version)}`
      : `${API_BASE}/projects/${project_id}/risk`;

    const res = await fetch(url, {
      headers: getAuthHeaders()
    });
    if (!res.ok) throw await parseError(res);
    const data = await res.json();
    setCached(cacheKey, data);
    return data;
  },

  getAssetExplanation: async (projectId: string, assetId: string, epochs: number = 25): Promise<GNNExplanationResponse> => {
    const encodedAssetId = encodeURIComponent(assetId);
    const res = await fetch(`${API_BASE}/projects/${projectId}/assets/${encodedAssetId}/explanation?epochs=${epochs}`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) throw await parseError(res);
    return res.json();
  },

  getPqcReadiness: async (project_id: string): Promise<any> => {
    const cacheKey = `pqc:${project_id}`;
    const cached = getCached<any>(cacheKey);
    if (cached) return cached;

    const res = await fetch(`${API_BASE}/product/${project_id}/pqc-readiness`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) throw await parseError(res);
    const data = await res.json();
    setCached(cacheKey, data);
    return data;
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

  getAllMigrationPriorities: async (project_id: string, mosca_status: string = "SAFE"): Promise<any[]> => {
    const cacheKey = `priorities:${project_id}:${mosca_status}`;
    const cached = getCached<any[]>(cacheKey);
    if (cached) return cached;

    const res = await fetch(`${API_BASE}/product/${project_id}/priorities?mosca_status=${mosca_status}`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) throw await parseError(res);
    const data = await res.json();
    setCached(cacheKey, data);
    return data;
  },

  getMigrationPriority: async (project_id: string, asset_id: string, mosca_status: string = "SAFE"): Promise<any> => {
    const res = await fetch(`${API_BASE}/product/${project_id}/assets/${asset_id}/priority?mosca_status=${mosca_status}`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) throw await parseError(res);
    return res.json();
  },

  getAllRoadmapStates: async (project_id: string): Promise<Record<string, any>> => {
    const cacheKey = `roadmap:${project_id}`;
    const cached = getCached<Record<string, any>>(cacheKey);
    if (cached) return cached;

    const res = await fetch(`${API_BASE}/product/${project_id}/roadmap-all`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) throw await parseError(res);
    const data = await res.json();
    setCached(cacheKey, data);
    return data;
  },

  getRoadmapState: async (project_id: string, asset_id: string): Promise<any> => {
    const res = await fetch(`${API_BASE}/product/${project_id}/assets/${asset_id}/roadmap`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) throw await parseError(res);
    return res.json();
  },

  transitionRoadmapState: async (project_id: string, asset_id: string, requested_state: string): Promise<any> => {
    clearApiCache(`roadmap:${project_id}`);
    const res = await fetch(`${API_BASE}/product/${project_id}/assets/${asset_id}/roadmap`, {
      method: "POST",
      headers: getAuthHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ requested_state })
    });
    if (!res.ok) throw await parseError(res);
    return res.json();
  },

  getCryptoInventory: async (project_id: string): Promise<CryptoInventoryResponse> => {
    const cacheKey = `inventory:${project_id}`;
    const cached = getCached<CryptoInventoryResponse>(cacheKey);
    if (cached) return cached;

    const res = await fetch(`${API_BASE}/product/${project_id}/crypto-inventory`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) throw await parseError(res);
    const data = await res.json();
    setCached(cacheKey, data);
    return data;
  },

  getReportMarkdown: async (project_id: string): Promise<string> => {
    const cacheKey = `report_md:${project_id}`;
    const cached = getCached<string>(cacheKey);
    if (cached) return cached;

    const res = await fetch(`${API_BASE}/projects/${project_id}/report/markdown`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) throw await parseError(res);
    const data = await res.text();
    setCached(cacheKey, data);
    return data;
  }
};
