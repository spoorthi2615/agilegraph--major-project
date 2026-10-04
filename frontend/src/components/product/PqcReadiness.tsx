import { useState, useEffect } from 'react';
import { apiClient } from '../../api/client';
import { AlertCircle, ShieldAlert, Activity, Info } from 'lucide-react';

export default function PqcReadiness() {
  const [projectId, setProjectId] = useState('demo-project');
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchReadiness = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const result = await apiClient.getPqcReadiness(projectId);
      setData(result);
    } catch (err: any) {
      setError(err.message || "Failed to load PQC readiness.");
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReadiness();
  }, []);

  return (
    <div className="flex flex-col gap-6 w-full">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold flex items-center gap-2">
          <Activity className="text-blue-400" /> PQC Readiness
        </h2>
        <form onSubmit={fetchReadiness} className="flex gap-2">
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

      {error && (
        <div className="p-4 bg-red-900/50 border border-red-500/50 rounded-md flex items-start gap-3 text-red-200">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <p>{error}</p>
        </div>
      )}

      {data && (
        <div className="flex flex-col gap-6">
          <div className="p-4 bg-amber-900/20 border border-amber-900/50 rounded-md">
            <h3 className="font-semibold text-amber-500 flex items-center gap-2 mb-2">
              <ShieldAlert className="w-4 h-4" /> {data.status}
            </h3>
            <p className="text-sm text-amber-500/80">{data.semantic_disclaimer || "Inventory/coverage summary, not a scientifically validated PQC readiness score."}</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard label="Total Assets" value={data.asset_count} />
            <StatCard label="Assessed Assets" value={data.assessed_assets} />
            <StatCard label="Insufficient Evidence" value={data.insufficient_evidence_assets} alert={data.insufficient_evidence_assets > 0} />
            <StatCard label="Requiring Attention" value={data.assets_requiring_attention} />
            <StatCard label="Migration Candidates" value={data.migration_candidates} />
            <StatCard label="Unknown Algorithms" value={data.unknown_algorithms} alert={data.unknown_algorithms > 0} />
          </div>

          <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 shadow-lg">
            <h3 className="text-lg font-semibold mb-4">Recognized Algorithms</h3>
            <div className="flex flex-wrap gap-2">
              {data.recognized_algorithms?.length > 0 ? (
                data.recognized_algorithms.map((alg: string) => (
                  <span key={alg} className="px-3 py-1 bg-slate-900 border border-slate-700 rounded-md text-sm font-mono text-slate-300">
                    {alg}
                  </span>
                ))
              ) : (
                <span className="text-slate-500 italic text-sm">Not available</span>
              )}
            </div>
          </div>
        </div>
      )}
      
      {!data && !error && !loading && (
        <div className="flex flex-col items-center justify-center p-12 text-slate-500 border-2 border-dashed border-slate-700 rounded-xl">
          <Info className="w-12 h-12 mb-4 opacity-50" />
          <p>Enter a Project ID and fetch to view readiness.</p>
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value, alert = false }: { label: string, value: any, alert?: boolean }) {
  return (
    <div className={`p-4 rounded-xl border ${alert ? 'bg-amber-900/10 border-amber-500/30' : 'bg-slate-800 border-slate-700'} shadow-md flex flex-col`}>
      <span className="text-sm text-slate-400 mb-1">{label}</span>
      <span className={`text-2xl font-bold ${alert ? 'text-amber-400' : 'text-slate-100'}`}>
        {value !== undefined && value !== null ? value : <span className="text-sm font-normal text-slate-500 italic">Not available</span>}
      </span>
    </div>
  );
}
