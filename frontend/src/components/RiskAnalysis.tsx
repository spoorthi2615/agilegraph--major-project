import React, { useState, useEffect } from 'react';
import { useProject } from '../context/ProjectContext';
import { apiClient } from '../api/client';
import type { RiskResponse, GraphResponse, GNNExplanationResponse } from '../api/client';
import RiskTable from './RiskTable';
import { Shield, Search, AlertCircle, Play, Activity, Sparkles, Network, X, Info } from 'lucide-react';

export default function RiskAnalysis() {
  const { projectId, setProjectId } = useProject();
  const [repoPath, setRepoPath] = useState('');
  const [engineVersion, setEngineVersion] = useState<'v1' | 'v2'>('v1');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [riskData, setRiskData] = useState<RiskResponse | null>(null);
  const [graphData, setGraphData] = useState<GraphResponse | null>(null);
  const [selectedAssetId, setSelectedAssetId] = useState<string | null>(null);
  const [explanation, setExplanation] = useState<GNNExplanationResponse | null>(null);
  const [loadingExplanation, setLoadingExplanation] = useState(false);

  const loadRiskData = async (id: string, ver: string = engineVersion) => {
    setLoading(true);
    setError(null);
    try {
      const [risk, graph] = await Promise.all([
        apiClient.getRisk(id, ver).catch(() => null),
        apiClient.getGraph(id).catch(() => null)
      ]);
      setRiskData(risk);
      setGraphData(graph);
    } catch (e: any) {
      setError(e.message || 'Failed to load risk data');
    } finally {
      setLoading(false);
    }
  };

  const handleSwitchEngine = (newVer: 'v1' | 'v2') => {
    setEngineVersion(newVer);
    if (projectId) {
      loadRiskData(projectId, newVer);
    }
  };

  useEffect(() => {
    if (projectId) {
      loadRiskData(projectId, engineVersion);
    } else {
      setRiskData(null);
      setGraphData(null);
      setSelectedAssetId(null);
    }
  }, [projectId]);

  useEffect(() => {
    if (projectId && selectedAssetId) {
      setLoadingExplanation(true);
      apiClient.getAssetExplanation(projectId, selectedAssetId)
        .then(res => setExplanation(res))
        .catch(() => setExplanation(null))
        .finally(() => setLoadingExplanation(false));
    } else {
      setExplanation(null);
    }
  }, [projectId, selectedAssetId]);

  const handleScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoPath || !projectId) return;
    
    setLoading(true);
    setError(null);
    try {
      await apiClient.scan({ repository_path: repoPath, project_id: projectId, engine_version: engineVersion });
      await loadRiskData(projectId, engineVersion);
    } catch (err: any) {
      setError(err.message || 'An error occurred during scanning.');
      setLoading(false);
    }
  };

  const totalAssets = graphData?.nodes.length || 0;
  const scoredAssets = riskData?.assets.filter(a => a.score !== null && a.score !== undefined).length || 0;
  const unassessedAssets = riskData?.assets.filter(a => a.score === null || a.score === undefined).length || 0;
  const highRiskAssets = riskData?.assets.filter(a => a.score !== null && a.score !== undefined && a.score >= 0.6).length || 0;

  return (
    <div className="flex flex-col gap-8 w-full max-w-7xl mx-auto font-sans animate-fade-up">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 relative">
        <div className="absolute -inset-8 rounded-3xl bg-gradient-to-br from-primary/10 to-transparent blur-2xl -z-10"></div>
        <div className="flex flex-col gap-2">
          <div className="text-xs font-semibold uppercase tracking-widest text-primary">Security Posture</div>
          <h2 className="text-3xl font-semibold tracking-tight text-foreground md:text-4xl flex items-center gap-3">
            <Shield className="w-8 h-8 text-primary" /> Risk Analysis &amp; Interpretability
          </h2>
          <p className="text-muted-foreground max-w-2xl mt-1 text-sm">
            Heuristic factor decomposition coupled with GNNExplainer topological graph attribution for cryptographic risk assessment.
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        
        {/* Left Column: Scan & Summary */}
        <div className="lg:col-span-1 flex flex-col gap-6">
          {/* Scan Section */}
          <div className="bg-card p-6 rounded-2xl border border-border shadow-sm flex flex-col gap-4">
            <h3 className="text-base font-semibold flex items-center gap-2 text-foreground">
              <Search className="w-4 h-4 text-primary" /> Run Discovery
            </h3>
            <form onSubmit={handleScan} className="flex flex-col gap-4">
              <div>
                <label className="block text-[10px] font-semibold text-muted-foreground mb-1.5 uppercase tracking-wider">Project ID</label>
                <input 
                  type="text" 
                  value={projectId} 
                  onChange={e => setProjectId(e.target.value)}
                  className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm focus:ring-1 focus:ring-ring outline-none transition-shadow"
                  placeholder="e.g. org_repo or my-project"
                  required
                />
              </div>
              <div>
                <label className="block text-[10px] font-semibold text-muted-foreground mb-1.5 uppercase tracking-wider">Repository Path</label>
                <input 
                  type="text" 
                  value={repoPath} 
                  onChange={e => setRepoPath(e.target.value)}
                  className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm focus:ring-1 focus:ring-ring outline-none transition-shadow"
                  placeholder="/absolute/path/to/repo"
                  required
                />
              </div>
              <div>
                <label className="block text-[10px] font-semibold text-muted-foreground mb-1.5 uppercase tracking-wider">Engine Version</label>
                <select 
                  value={engineVersion} 
                  onChange={e => handleSwitchEngine(e.target.value as 'v1' | 'v2')}
                  className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm focus:ring-1 focus:ring-ring outline-none transition-shadow"
                >
                  <option value="v1">V1 Production (Default)</option>
                  <option value="v2">V2 Experimental (Calibrated)</option>
                </select>
              </div>
              <button 
                type="submit" 
                disabled={loading || !repoPath || !projectId}
                className="w-full bg-primary hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed text-primary-foreground font-semibold py-2 px-4 rounded-lg flex justify-center items-center gap-2 shadow-glow transition-all"
              >
                {loading ? <span className="animate-pulse flex items-center gap-2"><Activity className="w-4 h-4 animate-spin"/> Scanning...</span> : <><Play className="w-4 h-4" /> Scan Repository</>}
              </button>
            </form>
            {error && (
              <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-lg flex items-start gap-2 text-sm text-destructive-foreground mt-2">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <p>{error}</p>
              </div>
            )}
          </div>

          {/* Risk Summary */}
          <div className="bg-card p-6 rounded-2xl border border-border shadow-sm flex flex-col gap-4">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Risk Summary</h3>
            <div className="flex flex-col gap-3">
              <div className="flex justify-between items-center border-b border-border pb-2">
                <span className="text-sm font-medium text-foreground">Assets Assessed</span>
                <span className="font-semibold text-foreground">{riskData ? totalAssets : <span className="text-muted-foreground font-normal italic text-xs">N/A</span>}</span>
              </div>
              <div className="flex justify-between items-center border-b border-border pb-2">
                <span className="text-sm font-medium text-foreground">Scored Assets</span>
                <span className="font-semibold text-foreground">{riskData ? scoredAssets : <span className="text-muted-foreground font-normal italic text-xs">N/A</span>}</span>
              </div>
              <div className="flex justify-between items-center border-b border-border pb-2">
                <span className="text-sm font-medium text-foreground">Unassessed Assets</span>
                <span className="font-semibold text-muted-foreground">{riskData ? unassessedAssets : <span className="text-muted-foreground font-normal italic text-xs">N/A</span>}</span>
              </div>
              <div className="flex justify-between items-center pt-1">
                <span className="text-sm font-medium text-foreground">High Risk</span>
                <span className={`font-bold ${riskData && highRiskAssets > 0 ? 'text-critical' : 'text-foreground'}`}>
                  {riskData ? highRiskAssets : <span className="text-muted-foreground font-normal italic text-xs">N/A</span>}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Decomposition, Table & Explainability */}
        <div className="lg:col-span-3 flex flex-col gap-6">
          <div className="bg-card border border-border rounded-2xl shadow-elevated flex flex-col overflow-hidden min-h-[450px]">
            <div className="p-5 border-b border-border bg-background/50 flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <h3 className="text-lg font-semibold text-foreground">Cryptographic Asset Inventory &amp; Scoring</h3>
                <p className="text-xs text-muted-foreground mt-0.5">Click any asset row to view unified GNNExplainer graph attribution &amp; factor breakdown.</p>
              </div>
              <div className="flex items-center gap-2 bg-muted/60 p-1 rounded-xl border border-border shrink-0">
                <button
                  type="button"
                  onClick={() => handleSwitchEngine('v1')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    engineVersion === 'v1'
                      ? 'bg-background text-foreground shadow-sm'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  V1 Baseline (Default)
                </button>
                <button
                  type="button"
                  onClick={() => handleSwitchEngine('v2')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    engineVersion === 'v2'
                      ? 'bg-primary text-primary-foreground shadow-sm'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  V2 Calibrated (Experimental)
                </button>
              </div>
            </div>
            {engineVersion === 'v2' && (
              <div className="mx-5 mt-4 p-3 bg-primary/10 border border-primary/20 rounded-xl text-xs text-primary flex items-start gap-2">
                <Sparkles className="w-4 h-4 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold">Engine V2 Active: Calibrated Heuristic (Experimental)</p>
                  <p className="text-primary/80 mt-0.5">
                    Evaluated via Leave-One-Repository-Out cross-validation. Calibrated thresholds (0.18, 0.38) and structural graph weakness propagation applied. Note: optimized for high crypto-risk recall (91.3%) with a known trade-off on test-harness LOW recall (48.3%).
                  </p>
                </div>
              </div>
            )}
            <div className="flex-1 overflow-auto bg-card">
              {loading && !riskData ? (
                <div className="flex flex-col items-center justify-center p-16 text-muted-foreground">
                  <Activity className="w-10 h-10 mb-4 animate-spin text-primary opacity-50" />
                  <span className="font-medium">Loading risk analysis...</span>
                </div>
              ) : riskData ? (
                <RiskTable 
                  data={riskData} 
                  graphData={graphData}
                  selectedAssetId={selectedAssetId} 
                  onRowClick={setSelectedAssetId} 
                />
              ) : (
                <div className="flex flex-col items-center justify-center p-16 text-muted-foreground border-2 border-dashed border-border m-6 rounded-2xl bg-background/50">
                  <Shield className="w-12 h-12 mb-4 opacity-30" />
                  <p className="text-lg font-semibold text-foreground">No Risk Data</p>
                  <p className="text-sm mt-2 text-center max-w-sm">Run a scan on your repository to generate risk scores and heuristic factor decompositions.</p>
                </div>
              )}
            </div>
          </div>

          {/* GNN & Heuristic Explainability Panel */}
          {selectedAssetId && (
            <div className="bg-card border border-border rounded-2xl shadow-elevated p-6 flex flex-col gap-5 animate-fade-in">
              <div className="flex items-center justify-between border-b border-border pb-4">
                <div className="flex items-center gap-2.5">
                  <Sparkles className="w-5 h-5 text-primary" />
                  <div>
                    <h3 className="text-base font-semibold text-foreground">Explainability Attribution</h3>
                    <p className="text-xs font-mono text-muted-foreground mt-0.5 truncate max-w-xl">{selectedAssetId}</p>
                  </div>
                </div>
                <button 
                  onClick={() => setSelectedAssetId(null)} 
                  className="p-1 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {loadingExplanation ? (
                <div className="flex items-center justify-center py-12 text-muted-foreground gap-3">
                  <Activity className="w-5 h-5 animate-spin text-primary" />
                  <span className="text-sm">Calculating GNNExplainer topological masks &amp; feature attributions...</span>
                </div>
              ) : explanation ? (
                <div className="flex flex-col gap-6">
                  {/* Scientific Caveat Banner */}
                  <div className="p-3.5 bg-muted/30 border border-border/60 rounded-xl flex items-start gap-2.5 text-xs text-muted-foreground">
                    <Info className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                    <p className="leading-relaxed">
                      <strong>Methodological Disclosure:</strong> {explanation.caveat}
                    </p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Column 1: GNN Feature Saliency */}
                    <div className="flex flex-col gap-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                          <Network className="w-3.5 h-3.5 text-primary" /> GNNExplainer Feature Saliency
                        </span>
                        <span className="text-[10px] text-muted-foreground font-mono">Normalized</span>
                      </div>
                      <div className="flex flex-col gap-2 bg-muted/15 p-4 rounded-xl border border-border/60">
                        {explanation.gnn_feature_attributions.slice(0, 7).map((item, idx) => (
                          <div key={idx} className="flex flex-col gap-1">
                            <div className="flex justify-between text-xs">
                              <span className="font-mono text-foreground">{item.feature_name}</span>
                              <span className="font-mono font-medium text-primary">{(item.normalized_importance * 100).toFixed(1)}%</span>
                            </div>
                            <div className="h-1.5 w-full bg-muted/60 rounded-full overflow-hidden">
                              <div 
                                className="h-full bg-primary rounded-full transition-all"
                                style={{ width: `${Math.min(100, Math.max(4, item.normalized_importance * 100))}%` }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Column 2: Influential Graph Neighbors / Edges */}
                    <div className="flex flex-col gap-3">
                      <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                        <Network className="w-3.5 h-3.5 text-primary" /> Top Influential Graph Edges
                      </span>
                      <div className="flex flex-col gap-2 bg-muted/15 p-4 rounded-xl border border-border/60 min-h-[160px]">
                        {explanation.top_influential_edges && explanation.top_influential_edges.length > 0 ? (
                          explanation.top_influential_edges.map((edge, idx) => (
                            <div key={idx} className="flex items-center justify-between p-2 rounded-lg bg-background/50 border border-border/40 text-xs">
                              <div className="flex flex-col gap-0.5">
                                <span className="font-mono font-semibold text-foreground text-[11px]">{edge.relation}</span>
                                <span className="text-[10px] text-muted-foreground">{edge.source_type} → {edge.target_type}</span>
                              </div>
                              <span className="font-mono text-xs px-2 py-0.5 rounded bg-primary/10 text-primary border border-primary/20">
                                {edge.importance.toFixed(3)}
                              </span>
                            </div>
                          ))
                        ) : (
                          <p className="text-xs text-muted-foreground italic my-auto text-center">
                            No external neighbor edges connected to this asset node in the code property graph.
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-xs text-muted-foreground italic">Explanation unavailable for this asset.</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
