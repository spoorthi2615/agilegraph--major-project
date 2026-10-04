import { useState, useEffect } from 'react';
import { apiClient } from '../../api/client';
import { List, AlertCircle, Info } from 'lucide-react';

export default function MigrationPriority() {
  const [projectId, setProjectId] = useState('demo-project');
  const [moscaStatus, setMoscaStatus] = useState('NOT_AT_RISK');
  const [assetsPriority, setAssetsPriority] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPriorities = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      // Fetch all assets from risk response first to get the asset IDs
      const riskRes = await apiClient.getRisk(projectId);
      if (!riskRes.assets || riskRes.assets.length === 0) {
        setAssetsPriority([]);
        return;
      }
      
      // Fetch priority for each asset
      const priorities = await Promise.all(
        riskRes.assets.map(async (asset) => {
          try {
            const p = await apiClient.getMigrationPriority(projectId, asset.asset_id, moscaStatus);
            return { asset_id: asset.asset_id, ...p };
          } catch (e) {
            return { asset_id: asset.asset_id, priority: 'NOT_ASSESSED', rationale: 'Failed to fetch priority' };
          }
        })
      );
      
      // Sort deterministically by sort_key
      priorities.sort((a, b) => {
        if (!a.sort_key || !b.sort_key) return 0;
        for (let i = 0; i < a.sort_key.length; i++) {
          if (a.sort_key[i] < b.sort_key[i]) return -1;
          if (a.sort_key[i] > b.sort_key[i]) return 1;
        }
        return 0;
      });
      
      setAssetsPriority(priorities);
    } catch (err: any) {
      setError(err.message || "Failed to load migration priorities.");
      setAssetsPriority([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPriorities();
  }, []);

  return (
    <div className="flex flex-col gap-6 w-full">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <h2 className="text-2xl font-semibold flex items-center gap-2">
          <List className="text-blue-400" /> Migration Priority
        </h2>
        <form onSubmit={fetchPriorities} className="flex flex-wrap items-center gap-2 bg-slate-800 p-2 rounded-lg border border-slate-700">
          <input 
            type="text" 
            value={projectId} 
            onChange={e => setProjectId(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-md px-3 py-1 text-sm outline-none focus:ring-1 focus:ring-blue-500"
            placeholder="Project ID"
          />
          <select
            value={moscaStatus}
            onChange={e => setMoscaStatus(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-md px-3 py-1 text-sm outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="NOT_AT_RISK">Mosca: Not At Risk</option>
            <option value="AT_RISK">Mosca: At Risk</option>
            <option value="INSUFFICIENT_DATA">Mosca: Insufficient Data</option>
          </select>
          <button type="submit" disabled={loading} className="bg-blue-600 hover:bg-blue-500 px-3 py-1 rounded-md text-sm font-medium">
            {loading ? 'Loading...' : 'Fetch'}
          </button>
        </form>
      </div>

      <div className="p-4 bg-slate-800 border border-slate-700 rounded-md text-sm text-slate-400">
        <p>This view is a downstream planning heuristic.</p>
        <p className="mt-1 text-xs italic">Preliminary risk drives the base priority. Mosca acts as planning urgency. Algorithm/migration difficulty are informational.</p>
      </div>

      {error && (
        <div className="p-4 bg-red-900/50 border border-red-500/50 rounded-md flex items-start gap-3 text-red-200">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <p>{error}</p>
        </div>
      )}

      {assetsPriority.length > 0 ? (
        <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden shadow-lg">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-slate-900 border-b border-slate-700 text-slate-400">
                <tr>
                  <th className="p-4 font-semibold">Asset ID</th>
                  <th className="p-4 font-semibold">Priority</th>
                  <th className="p-4 font-semibold">Preliminary Risk</th>
                  <th className="p-4 font-semibold">Mosca Status</th>
                  <th className="p-4 font-semibold">Evidence Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50">
                {assetsPriority.map(asset => (
                  <tr key={asset.asset_id} className="hover:bg-slate-800/50 transition-colors">
                    <td className="p-4 font-mono text-slate-300">{asset.asset_id}</td>
                    <td className="p-4">
                      <span className={`px-2 py-1 rounded-md text-xs font-bold ${
                        asset.priority === 'HIGH' ? 'bg-red-900/50 text-red-400 border border-red-500/30' :
                        asset.priority === 'MEDIUM' ? 'bg-amber-900/50 text-amber-400 border border-amber-500/30' :
                        asset.priority === 'LOW' ? 'bg-emerald-900/50 text-emerald-400 border border-emerald-500/30' :
                        'bg-slate-700 text-slate-400'
                      }`}>
                        {asset.priority}
                      </span>
                    </td>
                    <td className="p-4">
                      {asset.risk_score !== null && asset.risk_score !== undefined ? (
                         <span className="font-mono text-slate-300">{asset.risk_score.toFixed(2)}</span>
                      ) : (
                         <span className="text-slate-500 italic">Not assessed</span>
                      )}
                    </td>
                    <td className="p-4">
                      {asset.mosca_status ? (
                        <div className="flex flex-col gap-1">
                          <span className={`text-xs font-semibold ${
                            asset.mosca_status === 'AT_RISK' ? 'text-red-400' : 
                            asset.mosca_status === 'NOT_AT_RISK' ? 'text-emerald-400' : 'text-slate-400'
                          }`}>
                            {asset.mosca_status}
                          </span>
                          <span className="text-[10px] text-slate-500" title={asset.mosca_provenance}>Planning input</span>
                        </div>
                      ) : (
                        <span className="text-slate-500 italic">Not available</span>
                      )}
                    </td>
                    <td className="p-4">
                      <div className="flex flex-col">
                        <span className="text-slate-300">{asset.evidence_status || 'Unknown'}</span>
                        <span className="text-xs text-slate-500 mt-1 max-w-xs whitespace-normal break-words">{asset.rationale}</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        !loading && !error && (
          <div className="flex flex-col items-center justify-center p-12 text-slate-500 border-2 border-dashed border-slate-700 rounded-xl">
            <Info className="w-12 h-12 mb-4 opacity-50" />
            <p>No assets found. Scan a repository to view migration priorities.</p>
          </div>
        )
      )}
    </div>
  );
}
