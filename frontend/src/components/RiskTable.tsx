import type { RiskResponse, GraphResponse } from '../api/client';
import { AlertTriangle, Info, FileCode } from 'lucide-react';

interface RiskTableProps {
  data: RiskResponse;
  graphData: GraphResponse | null;
  selectedAssetId: string | null;
  onRowClick: (assetId: string) => void;
}

export default function RiskTable({ data, graphData, selectedAssetId, onRowClick }: RiskTableProps) {
  if (!data || !data.assets || data.assets.length === 0) {
    return <div className="text-slate-500 text-sm">No assets found.</div>;
  }

  const selectedAsset = data.assets.find(a => a.asset_id === selectedAssetId);
  
  // Find evidence if it's a file
  const evidenceNodes = [];
  if (selectedAssetId && graphData) {
    const outEdges = graphData.edges.filter(e => e.source === selectedAssetId && e.type === "CONTAINS");
    for (const e of outEdges) {
      const targetNode = graphData.nodes.find(n => n.id === e.target);
      if (targetNode) evidenceNodes.push(targetNode);
    }
    // Also include IMPORTS
    const importEdges = graphData.edges.filter(e => e.source === selectedAssetId && e.type === "IMPORTS");
    for (const e of importEdges) {
      const targetNode = graphData.nodes.find(n => n.id === e.target);
      if (targetNode) evidenceNodes.push(targetNode);
    }
    // If no direct edges by "type", they might be stored in a relationship property or source/target
    if (evidenceNodes.length === 0) {
      const allEdges = graphData.edges.filter(e => e.source === selectedAssetId);
      for (const e of allEdges) {
         const targetNode = graphData.nodes.find(n => n.id === e.target);
         if (targetNode && targetNode.category !== "file") evidenceNodes.push(targetNode);
      }
    }
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <div className="overflow-auto flex-1 border-b border-slate-700/50">
        <table className="w-full text-left text-sm whitespace-nowrap">
          <thead className="bg-slate-900/50 text-slate-400 font-medium sticky top-0 z-10 backdrop-blur">
            <tr>
              <th className="px-3 py-2 rounded-tl-md">Asset ID</th>
              <th className="px-3 py-2 text-right">Base Risk</th>
              <th className="px-3 py-2 rounded-tr-md">Policy Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700/50">
            {data.assets.map((asset) => {
              const isSelected = asset.asset_id === selectedAssetId;
              const hasMissing = asset.missing_factors && asset.missing_factors.length > 0;
              return (
                <tr 
                  key={asset.asset_id} 
                  onClick={() => onRowClick(asset.asset_id)}
                  className={`cursor-pointer transition-colors ${isSelected ? 'bg-blue-900/30 border-l-2 border-blue-500' : 'hover:bg-slate-700/30 border-l-2 border-transparent'}`}
                >
                  <td className="px-3 py-2 font-mono text-slate-300 truncate max-w-xs" title={asset.asset_id}>{asset.asset_id}</td>
                  <td className="px-3 py-2 text-right font-medium">
                    <span className={`px-2 py-0.5 rounded-full text-xs ${
                      asset.score > 0.7 ? 'bg-red-500/20 text-red-400' :
                      asset.score > 0.4 ? 'bg-amber-500/20 text-amber-400' :
                      'bg-emerald-500/20 text-emerald-400'
                    }`}>
                      {asset.score.toFixed(4)}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-right">
                    {hasMissing ? (
                      <span className="text-xs bg-amber-900/40 text-amber-500 px-2 py-0.5 rounded flex items-center gap-1 w-max ml-auto">
                        <AlertTriangle className="w-3 h-3" /> RENORMALIZED
                      </span>
                    ) : (
                      <span className="text-xs bg-emerald-900/40 text-emerald-500 px-2 py-0.5 rounded flex items-center gap-1 w-max ml-auto">
                        <Info className="w-3 h-3" /> COMPLETE
                      </span>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {selectedAsset && (
        <div className="bg-slate-800/80 p-4 shrink-0 overflow-y-auto max-h-64">
          <h3 className="text-sm font-bold text-slate-200 mb-2 truncate" title={selectedAsset.asset_id}>
            Details: {selectedAsset.asset_id}
          </h3>
          
          {selectedAsset.missing_factors && selectedAsset.missing_factors.length > 0 && (
            <div className="mb-4 bg-amber-950/30 border border-amber-900/50 p-3 rounded text-xs text-amber-400/90">
              <p className="font-semibold mb-1 flex items-center gap-1"><AlertTriangle className="w-4 h-4"/> Missing Factors Detected</p>
              <p className="mb-1">Policy: <span className="font-mono bg-slate-900 px-1 rounded">{selectedAsset.missing_data_policy}</span></p>
              <p className="mb-1">The following factors were unavailable and their weights redistributed (CVE unavailable ≠ CVE risk zero):</p>
              <ul className="list-disc pl-4 mt-1 font-mono">
                {selectedAsset.missing_factors.map(mf => <li key={mf}>{mf}</li>)}
              </ul>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4 text-sm mb-4">
            <div>
              <p className="text-slate-400 font-semibold mb-2">Factor Contributions</p>
              {selectedAsset.weighted_contributions && Object.entries(selectedAsset.weighted_contributions).map(([factor, contrib]) => (
                <div key={factor} className="flex justify-between items-center mb-1 text-xs">
                  <span className="text-slate-300 font-mono capitalize">{factor.replace('_', ' ')}</span>
                  <div className="text-right">
                    <span className="text-slate-400 mr-2">val: {contrib.value?.toFixed(2)}</span>
                    <span className="text-emerald-400">+{contrib.contribution?.toFixed(3)}</span>
                  </div>
                </div>
              ))}
            </div>
            
            <div>
              <p className="text-slate-400 font-semibold mb-2">Heuristic Weights</p>
              {selectedAsset.weights && Object.entries(selectedAsset.weights).map(([factor, weight]) => (
                <div key={factor} className="flex justify-between items-center mb-1 text-xs">
                  <span className="text-slate-300 font-mono capitalize">{factor.replace('_', ' ')}</span>
                  <span className="text-blue-400 font-mono">{(weight * 100).toFixed(1)}%</span>
                </div>
              ))}
            </div>
          </div>
          
          {evidenceNodes.length > 0 && (
            <div className="border-t border-slate-700/50 pt-3">
              <p className="text-slate-400 font-semibold mb-2 flex items-center gap-2"><FileCode className="w-4 h-4" /> Scanner Traceability</p>
              <div className="space-y-2">
                {evidenceNodes.map((ev, i) => (
                  <div key={i} className="bg-slate-900/50 p-2 rounded text-xs border border-slate-700/50">
                    <div className="font-mono text-blue-400 mb-1">{ev.category.toUpperCase()}</div>
                    <div className="grid grid-cols-2 gap-x-2 gap-y-1">
                      {ev.library && <><span className="text-slate-500">Library</span><span className="text-slate-300 truncate">{ev.library}</span></>}
                      {ev.api && <><span className="text-slate-500">API</span><span className="text-slate-300 truncate">{ev.api}</span></>}
                      {ev.algorithm && <><span className="text-slate-500">Algorithm</span><span className="text-slate-300 truncate">{ev.algorithm}</span></>}
                      {ev.line && <><span className="text-slate-500">Line</span><span className="text-slate-300">{ev.line}</span></>}
                      {ev.evidence && <><span className="text-slate-500">Code</span><span className="text-slate-300 font-mono bg-slate-950 px-1 rounded truncate">{ev.evidence}</span></>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
