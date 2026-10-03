import type { RiskResponse } from '../api/client';

export default function RiskTable({ data }: { data: RiskResponse }) {
  if (!data || !data.assets || data.assets.length === 0) {
    return <div className="text-slate-500 text-sm">No assets found.</div>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm whitespace-nowrap">
        <thead className="bg-slate-900/50 text-slate-400 font-medium">
          <tr>
            <th className="px-3 py-2 rounded-tl-md">Asset ID</th>
            <th className="px-3 py-2 text-right">Heuristic Score</th>
            <th className="px-3 py-2 text-right">Centrality</th>
            <th className="px-3 py-2 rounded-tr-md">ML Status</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-700/50">
          {data.assets.map((asset) => (
            <tr key={asset.asset_id} className="hover:bg-slate-700/30 transition-colors">
              <td className="px-3 py-2 font-mono text-slate-300">{asset.asset_id}</td>
              <td className="px-3 py-2 text-right font-medium">
                <span className={`px-2 py-0.5 rounded-full text-xs ${
                  asset.score > 0.7 ? 'bg-red-500/20 text-red-400' :
                  asset.score > 0.4 ? 'bg-amber-500/20 text-amber-400' :
                  'bg-emerald-500/20 text-emerald-400'
                }`}>
                  {asset.score.toFixed(4)}
                </span>
              </td>
              <td className="px-3 py-2 text-right text-slate-400">
                {asset.library_centrality?.toFixed(4) || '0.0000'}
              </td>
              <td className="px-3 py-2">
                <span className="text-xs bg-slate-800 text-slate-500 px-2 py-0.5 rounded uppercase font-semibold">
                  {data.ml_status}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
