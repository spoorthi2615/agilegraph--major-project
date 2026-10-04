import { useState, useEffect } from 'react';
import { apiClient } from '../../api/client';
import { Map, AlertCircle, Info } from 'lucide-react';

const STATES = [
  "NOT_ASSESSED",
  "ASSESSMENT_REQUIRED",
  "MIGRATION_CANDIDATE",
  "HIGH_PRIORITY",
  "PLANNED",
  "IN_PROGRESS",
  "MIGRATED",
  "VERIFIED"
];

export default function MigrationRoadmap() {
  const [projectId, setProjectId] = useState('demo-project');
  const [assets, setAssets] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const fetchRoadmap = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!projectId) return;
    setLoading(true);
    setError(null);
    setActionError(null);
    try {
      const riskRes = await apiClient.getRisk(projectId);
      if (!riskRes.assets || riskRes.assets.length === 0) {
        setAssets([]);
        return;
      }
      
      const states = await Promise.all(
        riskRes.assets.map(async (asset) => {
          try {
            const state = await apiClient.getRoadmapState(projectId, asset.asset_id);
            return { ...asset, roadmap: state };
          } catch (e) {
            return { ...asset, roadmap: { current_state: "NOT_ASSESSED" } };
          }
        })
      );
      setAssets(states);
    } catch (err: any) {
      setError(err.message || "Failed to load migration roadmap.");
      setAssets([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRoadmap();
  }, []);

  const handleTransition = async (assetId: string, newState: string) => {
    setActionError(null);
    try {
      const res = await apiClient.transitionRoadmapState(projectId, assetId, newState);
      setAssets(prev => prev.map(a => a.asset_id === assetId ? { ...a, roadmap: res } : a));
    } catch (err: any) {
      setActionError(`Transition failed for ${assetId}: ${err.message}`);
    }
  };

  return (
    <div className="flex flex-col gap-6 w-full">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <h2 className="text-2xl font-semibold flex items-center gap-2">
          <Map className="text-blue-400" /> Migration Roadmap
        </h2>
        <form onSubmit={fetchRoadmap} className="flex gap-2">
          <input 
            type="text" 
            value={projectId} 
            onChange={e => setProjectId(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-md px-3 py-1 text-sm outline-none focus:ring-1 focus:ring-blue-500"
            placeholder="Project ID"
          />
          <button type="submit" disabled={loading} className="bg-blue-600 hover:bg-blue-500 px-3 py-1 rounded-md text-sm font-medium">
            {loading ? 'Loading...' : 'Fetch'}
          </button>
        </form>
      </div>

      <div className="p-4 bg-slate-800 border border-slate-700 rounded-md text-sm text-slate-400 flex flex-col gap-2">
        <p className="font-semibold text-slate-200">Migration planning</p>
        <p>This is a user-managed planning state board, not migration execution. Transitions represent planning decisions.</p>
        <p className="text-amber-500/80 mt-1">Note: <span className="font-mono">MIGRATED</span> and <span className="font-mono">VERIFIED</span> are user-asserted workflow states, not empirically validated claims.</p>
      </div>

      {error && (
        <div className="p-4 bg-red-900/50 border border-red-500/50 rounded-md flex items-start gap-3 text-red-200">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <p>{error}</p>
        </div>
      )}
      
      {actionError && (
        <div className="p-4 bg-amber-900/50 border border-amber-500/50 rounded-md flex items-start gap-3 text-amber-200">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <p>{actionError}</p>
        </div>
      )}

      {assets.length > 0 ? (
        <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden shadow-lg p-6">
          <div className="flex flex-col gap-4">
            {assets.map(asset => (
              <div key={asset.asset_id} className="bg-slate-900 border border-slate-700 p-4 rounded-lg flex flex-col gap-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <span className="font-mono font-medium text-slate-200">{asset.asset_id}</span>
                  <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                    asset.roadmap.current_state === 'VERIFIED' ? 'bg-emerald-900/50 text-emerald-400 border border-emerald-500/30' :
                    asset.roadmap.current_state === 'MIGRATED' ? 'bg-blue-900/50 text-blue-400 border border-blue-500/30' :
                    asset.roadmap.current_state === 'IN_PROGRESS' ? 'bg-purple-900/50 text-purple-400 border border-purple-500/30' :
                    'bg-slate-800 text-slate-300 border border-slate-600'
                  }`}>
                    {asset.roadmap.current_state}
                  </span>
                </div>
                
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-sm text-slate-400 mr-2">Transition to:</span>
                  {STATES.map(state => (
                    <button
                      key={state}
                      onClick={() => handleTransition(asset.asset_id, state)}
                      disabled={state === asset.roadmap.current_state}
                      className={`text-xs px-2 py-1 rounded flex items-center gap-1 transition-colors ${
                        state === asset.roadmap.current_state 
                          ? 'bg-slate-800 text-slate-600 cursor-not-allowed'
                          : 'bg-slate-700 hover:bg-blue-600 text-slate-300 hover:text-white'
                      }`}
                    >
                      {state}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        !loading && !error && (
          <div className="flex flex-col items-center justify-center p-12 text-slate-500 border-2 border-dashed border-slate-700 rounded-xl">
            <Info className="w-12 h-12 mb-4 opacity-50" />
            <p>No assets found. Scan a repository to start planning migration.</p>
          </div>
        )
      )}
    </div>
  );
}
