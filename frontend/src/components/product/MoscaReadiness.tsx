import { useState } from 'react';
import { apiClient } from '../../api/client';
import { Search, AlertCircle } from 'lucide-react';

export default function MoscaReadiness() {
  const [x, setX] = useState<number>(24);
  const [y, setY] = useState<number>(12);
  const [z, setZ] = useState<number>(30);
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleEvaluate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const result = await apiClient.evaluateMosca({ x, y, z });
      setData(result);
    } catch (err: any) {
      setError(err.message || "Failed to evaluate Mosca readiness.");
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-6 w-full max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold flex items-center gap-2">
          <Search className="text-blue-400" /> Mosca Readiness
        </h2>
      </div>

      <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 shadow-lg">
        <div className="mb-6 p-4 bg-slate-900 border border-slate-700 rounded-md text-sm text-slate-400">
          <p className="font-semibold text-slate-200 mb-2">Planning Assumptions</p>
          <p>This tool evaluates the Mosca theorem: <span className="font-mono text-emerald-400">x + y &gt; z</span></p>
          <p className="mt-2 text-xs italic text-slate-500">Note: `z` is a configurable planning assumption, not a scientific prediction of quantum capability. AgileGraph does not predict when Cryptographically Relevant Quantum Computers (CRQCs) will exist.</p>
        </div>

        <form onSubmit={handleEvaluate} className="flex flex-col gap-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-slate-300">Data Confidentiality Period (x)</label>
              <div className="flex items-center gap-2">
                <input 
                  type="number" 
                  value={x} 
                  onChange={e => setX(parseInt(e.target.value))}
                  className="w-full bg-slate-900 border border-slate-700 rounded-md px-3 py-2 outline-none focus:ring-1 focus:ring-blue-500"
                />
                <span className="text-sm text-slate-500">months</span>
              </div>
            </div>
            
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-slate-300">Migration Time (y)</label>
              <div className="flex items-center gap-2">
                <input 
                  type="number" 
                  value={y} 
                  onChange={e => setY(parseInt(e.target.value))}
                  className="w-full bg-slate-900 border border-slate-700 rounded-md px-3 py-2 outline-none focus:ring-1 focus:ring-blue-500"
                />
                <span className="text-sm text-slate-500">months</span>
              </div>
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-slate-300">Quantum Horizon (z)</label>
              <div className="flex items-center gap-2">
                <input 
                  type="number" 
                  value={z} 
                  onChange={e => setZ(parseInt(e.target.value))}
                  className="w-full bg-slate-900 border border-slate-700 rounded-md px-3 py-2 outline-none focus:ring-1 focus:ring-blue-500"
                />
                <span className="text-sm text-slate-500">months</span>
              </div>
            </div>
          </div>

          <button type="submit" disabled={loading} className="w-full md:w-auto self-end bg-blue-600 hover:bg-blue-500 px-6 py-2 rounded-md font-medium transition-colors">
            {loading ? 'Evaluating...' : 'Evaluate Mosca'}
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
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 shadow-lg">
          <h3 className="text-lg font-semibold mb-6">Evaluation Result</h3>
          
          <div className="flex flex-col md:flex-row gap-6 mb-6">
            <div className="flex-1 bg-slate-900 border border-slate-700 rounded-lg p-4 text-center">
              <p className="text-sm text-slate-400 mb-1">Required Time (x + y)</p>
              <p className="text-3xl font-mono">{data.total !== null ? data.total : '--'}</p>
              <p className="text-xs text-slate-500 mt-1">months</p>
            </div>
            
            <div className="flex items-center justify-center font-mono text-2xl text-slate-500">
              {data.status === 'AT_RISK' ? '>' : data.status === 'NOT_AT_RISK' ? '≤' : '?'}
            </div>

            <div className="flex-1 bg-slate-900 border border-slate-700 rounded-lg p-4 text-center">
              <p className="text-sm text-slate-400 mb-1">Quantum Horizon (z)</p>
              <p className="text-3xl font-mono">{data.z !== null ? data.z : '--'}</p>
              <p className="text-xs text-slate-500 mt-1">months</p>
            </div>
          </div>

          <div className={`p-4 rounded-md border ${
            data.status === 'AT_RISK' ? 'bg-red-900/20 border-red-500/50 text-red-400' :
            data.status === 'NOT_AT_RISK' ? 'bg-emerald-900/20 border-emerald-500/50 text-emerald-400' :
            'bg-amber-900/20 border-amber-500/50 text-amber-400'
          }`}>
            <h4 className="font-bold text-lg mb-1">{data.status}</h4>
            <p className="text-sm opacity-90">{data.explanation}</p>
          </div>
        </div>
      )}
    </div>
  );
}
