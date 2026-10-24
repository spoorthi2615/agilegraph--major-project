import { useState, useEffect } from 'react';
import { useProject } from '../context/ProjectContext';
import { apiClient } from '../api/client';
import type { ScanResponse, GraphResponse, RiskResponse } from '../api/client';
import GraphView from './GraphView';
import RiskTable from './RiskTable';
import { AlertCircle, CheckCircle, Search, Shield, Play, ArrowRight, Network, Database, Activity, Map, List } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Dashboard() {
  const [repoPath, setRepoPath] = useState('');
  const { projectId, setProjectId } = useProject();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scanResult, setScanResult] = useState<ScanResponse | null>(null);
  const [graphData, setGraphData] = useState<GraphResponse | null>(null);
  const [riskData, setRiskData] = useState<RiskResponse | null>(null);
  const [selectedAssetId, setSelectedAssetId] = useState<string | null>(null);

  const loadProjectData = async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      // Try to load existing project data silently
      const [graph, risk] = await Promise.all([
        apiClient.getGraph(id).catch(() => null),
        apiClient.getRisk(id).catch(() => null)
      ]);
      setGraphData(graph);
      setRiskData(risk);
    } catch {
      // Ignore initial load errors
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (projectId) {
      loadProjectData(projectId);
    } else {
      setGraphData(null);
      setRiskData(null);
      setScanResult(null);
    }
  }, [projectId]);

  const handleScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoPath || !projectId) return;
    
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.scan({ repository_path: repoPath, project_id: projectId });
      setScanResult(res);
      
      const graph = await apiClient.getGraph(projectId);
      setGraphData(graph);
      
      const risk = await apiClient.getRisk(projectId);
      setRiskData(risk);
      setSelectedAssetId(null);
    } catch (err: any) {
      setError(err.message || 'An error occurred during scanning.');
    } finally {
      setLoading(false);
    }
  };

  // Derived metrics
  const totalAssets = graphData?.nodes.length || 0;
  const highRiskAssets = riskData?.assets.filter(a => (a.score || 0) > 0.7).length || 0;
  const hasData = !!graphData && !!riskData;

  return (
    <div className="flex flex-col gap-8 w-full max-w-7xl mx-auto font-sans animate-fade-up">
      {/* Hero Section */}
      <div className="flex flex-col gap-2 relative">
        <div className="absolute -inset-8 rounded-3xl bg-gradient-to-br from-primary/10 to-transparent blur-2xl -z-10"></div>
        <div className="text-xs font-semibold uppercase tracking-widest text-primary">Executive Snapshot</div>
        <h2 className="text-3xl font-semibold tracking-tight text-foreground md:text-4xl">Project Overview</h2>
        <p className="text-muted-foreground max-w-2xl">
          Live PQC readiness and cryptographic blast-radius. Scan a repository to build the dependency graph and assess heuristic risk.
        </p>
      </div>

      {/* Snapshot Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
          <div className="text-xs text-muted-foreground uppercase tracking-wider mb-2">Discovered Assets</div>
          <div className="text-3xl font-semibold text-foreground">
            {hasData ? totalAssets : <span className="text-muted-foreground text-lg italic">Not available</span>}
          </div>
        </div>
        <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
          <div className="text-xs text-muted-foreground uppercase tracking-wider mb-2">High Risk Assets</div>
          <div className={`text-3xl font-semibold ${hasData && highRiskAssets > 0 ? 'text-critical' : 'text-foreground'}`}>
            {hasData ? highRiskAssets : <span className="text-muted-foreground text-lg italic">Not available</span>}
          </div>
        </div>
        <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
          <div className="text-xs text-muted-foreground uppercase tracking-wider mb-2">Data Status</div>
          <div className={`text-xl font-semibold mt-1 ${hasData ? 'text-success' : 'text-muted-foreground'}`}>
            {hasData ? 'Available' : 'Pending Scan'}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column */}
        <div className="lg:col-span-1 flex flex-col gap-8">
          {/* Scan Card */}
          <div className="rounded-2xl border border-border bg-card p-6 shadow-elevated relative overflow-hidden group">
            <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2 relative z-10">
              <div className="grid h-8 w-8 place-items-center rounded-lg bg-primary/10 text-primary">
                <Search className="w-4 h-4" />
              </div>
              Run Discovery
            </h3>
            <form onSubmit={handleScan} className="flex flex-col gap-4 relative z-10">
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1.5 uppercase tracking-wider">Project ID</label>
                <input 
                  type="text" 
                  value={projectId} 
                  onChange={e => setProjectId(e.target.value)}
                  className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm focus:ring-1 focus:ring-ring outline-none"
                  placeholder="e.g. org/repo"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1.5 uppercase tracking-wider">Repository Path</label>
                <input 
                  type="text" 
                  value={repoPath} 
                  onChange={e => setRepoPath(e.target.value)}
                  className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm focus:ring-1 focus:ring-ring outline-none"
                  placeholder="/absolute/path/to/repo"
                  required
                />
              </div>
              <button 
                type="submit" 
                disabled={loading || !repoPath || !projectId}
                className="mt-2 w-full bg-primary hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed text-primary-foreground font-medium py-2 px-4 rounded-md flex justify-center items-center gap-2 shadow-glow transition-all"
              >
                {loading ? <span className="animate-pulse">Scanning...</span> : <><Play className="w-4 h-4" /> Execute Scan</>}
              </button>
            </form>
            
            {error && (
              <div className="mt-4 p-3 bg-destructive/10 border border-destructive/20 rounded-md flex items-start gap-3 text-sm text-destructive-foreground relative z-10">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <p>{error}</p>
              </div>
            )}
            
            {scanResult && !error && (
              <div className="mt-4 p-3 bg-success/10 border border-success/20 rounded-md flex items-start gap-3 text-sm text-success relative z-10">
                <CheckCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold">Scan Complete</p>
                  <p className="opacity-80">Graph built successfully.</p>
                </div>
              </div>
            )}
          </div>

          {/* Quick Links */}
          <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
            <h3 className="text-sm font-semibold mb-4 uppercase tracking-wider text-muted-foreground">Analysis & Planning</h3>
            <div className="flex flex-col gap-2">
              <Link to="/inventory" className="flex items-center justify-between p-3 rounded-lg border border-transparent hover:border-border hover:bg-muted/50 transition-colors group">
                <div className="flex items-center gap-3">
                  <Database className="w-4 h-4 text-primary" />
                  <span className="text-sm font-medium">Crypto Inventory</span>
                </div>
                <ArrowRight className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
              </Link>
              <Link to="/pqc-readiness" className="flex items-center justify-between p-3 rounded-lg border border-transparent hover:border-border hover:bg-muted/50 transition-colors group">
                <div className="flex items-center gap-3">
                  <Activity className="w-4 h-4 text-primary" />
                  <span className="text-sm font-medium">PQC Readiness</span>
                </div>
                <ArrowRight className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
              </Link>
              <Link to="/priority" className="flex items-center justify-between p-3 rounded-lg border border-transparent hover:border-border hover:bg-muted/50 transition-colors group">
                <div className="flex items-center gap-3">
                  <List className="w-4 h-4 text-primary" />
                  <span className="text-sm font-medium">Migration Priority</span>
                </div>
                <ArrowRight className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
              </Link>
              <Link to="/roadmap" className="flex items-center justify-between p-3 rounded-lg border border-transparent hover:border-border hover:bg-muted/50 transition-colors group">
                <div className="flex items-center gap-3">
                  <Map className="w-4 h-4 text-primary" />
                  <span className="text-sm font-medium">Migration Roadmap</span>
                </div>
                <ArrowRight className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
              </Link>
            </div>
          </div>
        </div>

        {/* Right Column */}
        <div className="lg:col-span-2 flex flex-col gap-8">
          <div className="rounded-2xl border border-border bg-card shadow-elevated flex flex-col overflow-hidden min-h-[400px]">
            <div className="p-4 border-b border-border flex justify-between items-center bg-background/50">
              <h3 className="text-sm font-semibold flex items-center gap-2">
                <Network className="w-4 h-4 text-primary" />
                Crypto Graph Topology
              </h3>
              <div className="flex gap-4 text-[10px] uppercase tracking-wider font-mono text-muted-foreground">
                <span className="flex items-center gap-1.5"><div className="w-1.5 h-1.5 rounded-full bg-blue-500"></div> File</span>
                <span className="flex items-center gap-1.5"><div className="w-1.5 h-1.5 rounded-full bg-emerald-500"></div> Library</span>
                <span className="flex items-center gap-1.5"><div className="w-1.5 h-1.5 rounded-full bg-purple-500"></div> CryptoUsage</span>
              </div>
            </div>
            <div className="flex-1 bg-background relative min-h-[400px]">
              {graphData ? (
                <GraphView 
                  data={graphData} 
                  selectedAssetId={selectedAssetId}
                  onNodeClick={setSelectedAssetId}
                />
              ) : (
                <div className="absolute inset-0 flex flex-col items-center justify-center text-muted-foreground p-8 text-center border-2 border-dashed border-border m-4 rounded-xl">
                  <Shield className="w-12 h-12 mb-4 opacity-20" />
                  <p className="text-sm font-medium">No graph data available</p>
                  <p className="text-xs mt-1 opacity-70">Run a scan on your repository to generate the dependency graph.</p>
                </div>
              )}
            </div>
          </div>

          <div className="rounded-2xl border border-border bg-card shadow-elevated flex flex-col overflow-hidden max-h-[500px]">
            <div className="p-4 border-b border-border bg-background/50">
              <h3 className="text-sm font-semibold">Heuristic Risk Decomposition</h3>
            </div>
            <div className="flex-1 overflow-auto p-0">
              {riskData ? (
                <RiskTable 
                  data={riskData} 
                  graphData={graphData}
                  selectedAssetId={selectedAssetId} 
                  onRowClick={setSelectedAssetId} 
                />
              ) : (
                <div className="flex items-center justify-center text-muted-foreground text-sm border-2 border-dashed border-border m-4 rounded-xl p-8 text-center">
                  Run a scan to view heuristic risk scores.
                </div>
              )}
            </div>
            {riskData && (
               <div className="px-4 py-2 bg-warning/10 border-t border-warning/20 text-[11px] text-warning/90">
                 Disclaimer: Empirical ML pipeline and expert labels are currently BLOCKED. Scores shown are initial heuristic estimates only.
               </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
