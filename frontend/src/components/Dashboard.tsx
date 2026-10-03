import { useState } from 'react';
import { apiClient } from '../api/client';
import type { ScanResponse, GraphResponse, RiskResponse } from '../api/client';
import GraphView from './GraphView';
import RiskTable from './RiskTable';
import { AlertCircle, CheckCircle, Search, Shield, Play } from 'lucide-react';

export default function Dashboard() {
  const [repoPath, setRepoPath] = useState('');
  const [projectId, setProjectId] = useState('demo-project');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scanResult, setScanResult] = useState<ScanResponse | null>(null);
  const [graphData, setGraphData] = useState<GraphResponse | null>(null);
  const [riskData, setRiskData] = useState<RiskResponse | null>(null);

  const handleScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoPath) return;
    
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.scan({ repository_path: repoPath, project_id: projectId });
      setScanResult(res);
      
      const graph = await apiClient.getGraph(projectId);
      setGraphData(graph);
      
      const risk = await apiClient.getRisk(projectId);
      setRiskData(risk);
    } catch (err: any) {
      setError(err.message || 'An error occurred during scanning.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col font-sans">
      <header className="bg-slate-800 border-b border-slate-700 p-4 shadow-md flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield className="text-emerald-400 w-8 h-8" />
          <h1 className="text-xl font-bold tracking-tight text-white">AgileGraph Analysis Dashboard</h1>
        </div>
        <div className="flex items-center gap-4 text-sm font-mono text-slate-400 bg-slate-900 px-3 py-1 rounded-md border border-slate-700">
          <span>GATv2: <span className="text-amber-400">BLOCKED</span></span>
          <span className="text-slate-600">|</span>
          <span>Expert Validation: <span className="text-amber-400">PENDING_EXPERT_LABELS</span></span>
        </div>
      </header>

      <main className="flex-1 p-6 max-w-7xl mx-auto w-full grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Controls and Risk */}
        <div className="lg:col-span-1 flex flex-col gap-6">
          <div className="bg-slate-800 rounded-xl p-5 border border-slate-700 shadow-lg">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Search className="w-5 h-5 text-blue-400" />
              Scan Repository
            </h2>
            <form onSubmit={handleScan} className="flex flex-col gap-4">
              <div>
                <label className="block text-sm text-slate-400 mb-1">Project ID</label>
                <input 
                  type="text" 
                  value={projectId} 
                  onChange={e => setProjectId(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                  placeholder="e.g. org/repo"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">Repository Path</label>
                <input 
                  type="text" 
                  value={repoPath} 
                  onChange={e => setRepoPath(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                  placeholder="/absolute/path/to/repo"
                />
              </div>
              <button 
                type="submit" 
                disabled={loading || !repoPath}
                className="mt-2 w-full bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:cursor-not-allowed text-white font-medium py-2 px-4 rounded-md flex justify-center items-center gap-2 transition-colors"
              >
                {loading ? <span className="animate-pulse">Scanning...</span> : <><Play className="w-4 h-4" /> Run Heuristic Scan</>}
              </button>
            </form>
            
            {error && (
              <div className="mt-4 p-3 bg-red-900/50 border border-red-500/50 rounded-md flex items-start gap-3 text-sm text-red-200">
                <AlertCircle className="w-5 h-5 shrink-0" />
                <p>{error}</p>
              </div>
            )}
            
            {scanResult && !error && (
              <div className="mt-4 p-3 bg-emerald-900/30 border border-emerald-500/30 rounded-md flex items-start gap-3 text-sm text-emerald-300">
                <CheckCircle className="w-5 h-5 shrink-0 text-emerald-400" />
                <div>
                  <p className="font-semibold">Scan Complete</p>
                  <p className="text-emerald-400/80">Graph built successfully.</p>
                </div>
              </div>
            )}
          </div>

          <div className="bg-slate-800 rounded-xl border border-slate-700 shadow-lg flex-1 overflow-hidden flex flex-col">
            <h2 className="text-lg font-semibold p-5 pb-0">Heuristic Risk Decomposition</h2>
            <div className="p-5 flex-1 overflow-auto">
              {riskData ? (
                <RiskTable data={riskData} />
              ) : (
                <div className="h-full flex items-center justify-center text-slate-500 text-sm border-2 border-dashed border-slate-700 rounded-lg p-6 text-center">
                  Run a scan to view asset risk decompositions.
                </div>
              )}
            </div>
            {riskData && (
               <div className="px-5 py-3 bg-amber-900/20 border-t border-amber-900/50 text-xs text-amber-500/80">
                 Disclaimer: Empirical ML pipeline and expert labels are currently BLOCKED. Scores shown are initial heuristic estimates only.
               </div>
            )}
          </div>
        </div>

        {/* Right Column: Graph View */}
        <div className="lg:col-span-2 bg-slate-800 rounded-xl border border-slate-700 shadow-lg overflow-hidden flex flex-col">
          <div className="p-5 border-b border-slate-700 flex justify-between items-center bg-slate-800/80 backdrop-blur">
            <h2 className="text-lg font-semibold">AgileGraph Topology</h2>
            <div className="flex gap-4 text-xs font-mono text-slate-400">
              <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-blue-400"></div> File</span>
              <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-emerald-400"></div> Library</span>
              <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-purple-400"></div> CryptoUsage</span>
            </div>
          </div>
          <div className="flex-1 bg-slate-950 relative min-h-[500px]">
            {graphData ? (
              <GraphView data={graphData} />
            ) : (
              <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-600">
                 <Shield className="w-16 h-16 mb-4 opacity-20" />
                 <p>Graph Topology Pending Scan</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
