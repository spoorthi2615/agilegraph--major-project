import React, { useState, useEffect } from 'react';
import { useProject } from '../context/ProjectContext';
import { apiClient } from '../api/client';
import type { GraphResponse } from '../api/client';
import GraphView from './GraphView';
import { Network, Search, AlertCircle, Play, Activity } from 'lucide-react';

export default function CryptoGraph() {
  const { projectId, setProjectId } = useProject();
  const [repoPath, setRepoPath] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [graphData, setGraphData] = useState<GraphResponse | null>(null);
  const [selectedAssetId, setSelectedAssetId] = useState<string | null>(null);

  const loadGraphData = async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const graph = await apiClient.getGraph(id);
      setGraphData(graph);
    } catch (e: any) {
      setError(e.message || 'Failed to load graph data');
      setGraphData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (projectId) {
      loadGraphData(projectId);
    } else {
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
      await loadGraphData(projectId);
    } catch (err: any) {
      setError(err.message || 'An error occurred during scanning.');
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-8 w-full max-w-7xl mx-auto font-sans animate-fade-up">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 relative">
        <div className="absolute -inset-8 rounded-3xl bg-gradient-to-br from-primary/10 to-transparent blur-2xl -z-10"></div>
        <div className="flex flex-col gap-2">
          <div className="text-xs font-semibold uppercase tracking-widest text-primary">Topology View</div>
          <h2 className="text-3xl font-semibold tracking-tight text-foreground md:text-4xl flex items-center gap-3">
            <Network className="w-8 h-8 text-primary" /> Crypto Graph
          </h2>
          <p className="text-muted-foreground max-w-2xl mt-1">
            Visual representation of cryptographic dependencies, files, and usages discovered in the codebase.
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        
        {/* Left Column: Scan */}
        <div className="lg:col-span-1 flex flex-col gap-6">
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

          <div className="bg-card p-6 rounded-2xl border border-border shadow-sm flex flex-col gap-4">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Legend</h3>
            <div className="flex flex-col gap-3 text-sm">
              <div className="flex items-center gap-3 border-b border-border pb-2">
                <div className="w-3 h-3 rounded-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)]"></div>
                <span className="font-medium text-foreground">File</span>
              </div>
              <div className="flex items-center gap-3 border-b border-border pb-2">
                <div className="w-3 h-3 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]"></div>
                <span className="font-medium text-foreground">Library</span>
              </div>
              <div className="flex items-center gap-3 border-b border-border pb-2">
                <div className="w-3 h-3 rounded-full bg-purple-500 shadow-[0_0_8px_rgba(168,85,247,0.5)]"></div>
                <span className="font-medium text-foreground">CryptoUsage</span>
              </div>
            </div>
            <p className="mt-2 text-[10px] text-muted-foreground italic leading-relaxed">
              * Graph reflects node types currently instantiated by the available scanner evidence.
            </p>
          </div>
        </div>

        {/* Right Column: Graph Topology */}
        <div className="lg:col-span-3 flex flex-col gap-6">
          <div className="bg-card border border-border rounded-2xl shadow-elevated flex flex-col overflow-hidden min-h-[600px] relative">
            <div className="p-4 border-b border-border bg-background/50 flex justify-between items-center z-10">
              <h3 className="text-lg font-semibold text-foreground">Topology Map</h3>
            </div>
            <div className="flex-1 bg-background relative overflow-hidden">
              {loading && !graphData ? (
                <div className="absolute inset-0 flex flex-col items-center justify-center p-16 text-muted-foreground bg-card/50 z-10">
                  <Activity className="w-10 h-10 mb-4 animate-spin text-primary opacity-50" />
                  <span className="font-medium">Loading graph data...</span>
                </div>
              ) : graphData ? (
                <GraphView 
                  data={graphData} 
                  selectedAssetId={selectedAssetId}
                  onNodeClick={setSelectedAssetId}
                />
              ) : (
                <div className="absolute inset-0 flex flex-col items-center justify-center p-16 text-muted-foreground border-2 border-dashed border-border m-6 rounded-2xl bg-background/50 z-10">
                  <Network className="w-12 h-12 mb-4 opacity-30" />
                  <p className="text-lg font-semibold text-foreground">No Graph Data</p>
                  <p className="text-sm mt-2 text-center max-w-sm">Run a scan on your repository to generate the dependency graph.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
