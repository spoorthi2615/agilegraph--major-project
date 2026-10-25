import React, { useState, useEffect } from 'react';
import { useProject } from '../context/ProjectContext';
import { apiClient } from '../api/client';
import type { RiskResponse, GraphResponse } from '../api/client';
import RiskTable from './RiskTable';
import { Shield, Search, AlertCircle, Play, Activity } from 'lucide-react';

export default function RiskAnalysis() {
  const { projectId, setProjectId } = useProject();
  const [repoPath, setRepoPath] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [riskData, setRiskData] = useState<RiskResponse | null>(null);
  const [graphData, setGraphData] = useState<GraphResponse | null>(null);
  const [selectedAssetId, setSelectedAssetId] = useState<string | null>(null);

  const loadRiskData = async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const [risk, graph] = await Promise.all([
        apiClient.getRisk(id).catch(() => null),
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

  useEffect(() => {
    if (projectId) {
      loadRiskData(projectId);
    } else {
      setRiskData(null);
      setGraphData(null);
    }
  }, [projectId]);

  const handleScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoPath || !projectId) return;
    
    setLoading(true);
    setError(null);
    try {
      await apiClient.scan({ repository_path: repoPath, project_id: projectId });
      await loadRiskData(projectId);
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
            <Shield className="w-8 h-8 text-primary" /> Risk Analysis
          </h2>
          <p className="text-muted-foreground max-w-2xl mt-1">
            Heuristic risk decomposition based on empirical scan evidence and cryptographic dependencies.
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

        {/* Right Column: Decomposition & Table */}
        <div className="lg:col-span-3 flex flex-col gap-6">
          <div className="bg-card border border-border rounded-2xl shadow-elevated flex flex-col overflow-hidden min-h-[600px]">
            <div className="p-5 border-b border-border bg-background/50">
              <h3 className="text-lg font-semibold text-foreground">Heuristic Risk Decomposition</h3>
            </div>
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
        </div>
      </div>
    </div>
  );
}
