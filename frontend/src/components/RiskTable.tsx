import type { RiskResponse, GraphResponse } from '../api/client';
import { AlertTriangle, Info, FileCode, HelpCircle } from 'lucide-react';

interface RiskTableProps {
  data: RiskResponse;
  graphData: GraphResponse | null;
  selectedAssetId: string | null;
  onRowClick: (assetId: string) => void;
}

/** Render a score badge, handling null (unrated) safely */
function ScoreBadge({ score }: { score: number | null }) {
  if (score === null || score === undefined) {
    return (
      <span className="px-2 py-0.5 rounded-full text-xs bg-muted text-muted-foreground flex items-center gap-1">
        <HelpCircle className="w-3 h-3" />
        Unrated
      </span>
    );
  }
  const colorClass =
    score > 0.7 ? 'bg-destructive/15 text-destructive border border-destructive/20' :
    score > 0.4 ? 'bg-warning/15 text-warning border border-warning/20' :
                  'bg-success/15 text-success border border-success/20';
  return (
    <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold ${colorClass}`}>
      {score.toFixed(4)}
    </span>
  );
}

/** Summary banner when some assets are unrated or files were skipped */
function ScanIntegritySummary({ data }: { data: RiskResponse }) {
  const unrated = data.assets.filter(a => a.score === null || a.score === undefined).length;
  const scored  = data.assets.filter(a => a.score !== null && a.score !== undefined).length;

  if (unrated === 0) return null;

  return (
    <div className="mb-4 mx-4 mt-4 p-4 bg-warning/10 border border-warning/20 rounded-xl text-xs text-warning">
      <p className="font-semibold flex items-center gap-1.5 mb-1 text-sm">
        <AlertTriangle className="w-4 h-4" /> Scan Integrity Notice
      </p>
      <p>
        {scored} asset{scored !== 1 ? 's' : ''} scored · {unrated} unrated
        (insufficient scoring evidence — not equivalent to low risk).
      </p>
      <p className="mt-1 text-warning/70">
        Unrated assets must be reviewed manually. They are not included in
        vulnerability counts.
      </p>
    </div>
  );
}

export default function RiskTable({ data, graphData, selectedAssetId, onRowClick }: RiskTableProps) {
  if (!data || !data.assets || data.assets.length === 0) {
    return <div className="text-muted-foreground text-sm p-4 text-center">No assets found.</div>;
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
      <ScanIntegritySummary data={data} />

      <div className="overflow-auto flex-1 border-b border-border/50">
        <table className="w-full text-left text-sm whitespace-nowrap">
          <thead className="bg-muted/50 text-muted-foreground font-semibold sticky top-0 z-10 backdrop-blur-md">
            <tr>
              <th className="px-5 py-3 rounded-tl-md">Asset ID</th>
              <th className="px-5 py-3 text-right">Base Risk</th>
              <th className="px-5 py-3 rounded-tr-md">Policy Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/50">
            {data.assets.map((asset) => {
              const isSelected = asset.asset_id === selectedAssetId;
              const isUnrated = asset.score === null || asset.score === undefined;
              const hasMissing = asset.missing_factors && asset.missing_factors.length > 0;
              return (
                <tr 
                  key={asset.asset_id} 
                  onClick={() => onRowClick(asset.asset_id)}
                  className={`cursor-pointer transition-colors ${isSelected ? 'bg-primary/10 border-l-2 border-primary' : 'hover:bg-muted/30 border-l-2 border-transparent'} ${isUnrated ? 'opacity-70' : ''}`}
                >
                  <td className="px-5 py-3 font-mono text-foreground truncate max-w-xs text-xs" title={asset.asset_id}>{asset.asset_id}</td>
                  <td className="px-5 py-3 text-right font-medium">
                    <ScoreBadge score={asset.score} />
                  </td>
                  <td className="px-5 py-3 text-right">
                    {isUnrated ? (
                      <span className="text-[10px] uppercase font-bold tracking-wider bg-muted text-muted-foreground px-2 py-0.5 rounded-full flex items-center gap-1 w-max ml-auto">
                        <HelpCircle className="w-3 h-3" /> UNRATED
                      </span>
                    ) : hasMissing ? (
                      <span className="text-[10px] uppercase font-bold tracking-wider bg-warning/15 text-warning px-2 py-0.5 rounded-full flex items-center gap-1 w-max ml-auto border border-warning/20">
                        <AlertTriangle className="w-3 h-3" /> RENORMALIZED
                      </span>
                    ) : (
                      <span className="text-[10px] uppercase font-bold tracking-wider bg-success/15 text-success px-2 py-0.5 rounded-full flex items-center gap-1 w-max ml-auto border border-success/20">
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
        <div className="bg-background border-t border-border p-5 shrink-0 overflow-y-auto max-h-72">
          <h3 className="text-sm font-bold text-foreground mb-3 flex items-center gap-2 truncate" title={selectedAsset.asset_id}>
            <Info className="w-4 h-4 text-primary" /> Details: {selectedAsset.asset_id}
          </h3>

          {/* Unrated notice */}
          {(selectedAsset.score === null || selectedAsset.score === undefined) && (
            <div className="mb-4 bg-muted/50 border border-border p-3 rounded-xl text-xs text-muted-foreground">
              <p className="font-semibold mb-1 flex items-center gap-1.5 text-foreground">
                <HelpCircle className="w-4 h-4" /> Unrated Asset
              </p>
              <p>
                This asset has insufficient scoring evidence. Unrated does not
                mean low risk — it means the heuristic engine could not produce
                a valid score. Manual review is required.
              </p>
            </div>
          )}
          
          {selectedAsset.missing_factors && selectedAsset.missing_factors.length > 0 && (
            <div className="mb-4 bg-warning/10 border border-warning/20 p-4 rounded-xl text-xs text-warning">
              <p className="font-semibold mb-1.5 flex items-center gap-1.5"><AlertTriangle className="w-4 h-4"/>Missing Factors Detected</p>
              <p className="mb-1">Policy: <span className="font-mono bg-warning/20 px-1.5 py-0.5 rounded">{selectedAsset.missing_data_policy}</span></p>
              <p className="mb-1 text-warning/80">The following factors were unavailable and their weights redistributed (CVE unavailable ≠ CVE risk zero):</p>
              <ul className="list-disc pl-4 mt-2 font-mono">
                {selectedAsset.missing_factors.map(mf => <li key={mf}>{mf}</li>)}
              </ul>
            </div>
          )}

          <div className="grid grid-cols-2 gap-6 text-sm mb-4">
            <div>
              <p className="text-muted-foreground text-[10px] uppercase font-bold tracking-wider mb-2.5">Factor Contributions</p>
              <div className="space-y-1.5">
                {selectedAsset.weighted_contributions && Object.entries(selectedAsset.weighted_contributions).map(([factor, contrib]) => (
                  <div key={factor} className="flex justify-between items-center text-xs bg-muted/30 p-1.5 rounded-lg border border-border/50">
                    <span className="text-foreground font-mono capitalize">{factor.replace('_', ' ')}</span>
                    <div className="text-right flex items-center gap-2">
                      <span className="text-muted-foreground text-[10px]">val: {contrib.value?.toFixed(2) ?? 'N/A'}</span>
                      <span className="text-success font-semibold">+{contrib.contribution?.toFixed(3) ?? 'N/A'}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            <div>
              <p className="text-muted-foreground text-[10px] uppercase font-bold tracking-wider mb-2.5">Heuristic Weights</p>
              <div className="space-y-1.5">
                {selectedAsset.weights && Object.entries(selectedAsset.weights).map(([factor, weight]) => (
                  <div key={factor} className="flex justify-between items-center text-xs bg-muted/30 p-1.5 rounded-lg border border-border/50">
                    <span className="text-foreground font-mono capitalize">{factor.replace('_', ' ')}</span>
                    <span className="text-primary font-mono font-bold">{((weight as number) * 100).toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
          
          {evidenceNodes.length > 0 && (
            <div className="border-t border-border pt-4 mt-2">
              <p className="text-muted-foreground text-[10px] uppercase font-bold tracking-wider mb-3 flex items-center gap-2">
                <FileCode className="w-3.5 h-3.5" /> Scanner Traceability
              </p>
              <div className="space-y-2">
                {evidenceNodes.map((ev, i) => (
                  <div key={i} className="bg-muted/30 p-3 rounded-xl text-xs border border-border">
                    <div className="font-mono text-primary font-semibold mb-2">{ev.category.toUpperCase()}</div>
                    <div className="grid grid-cols-2 gap-x-4 gap-y-2">
                      {ev.library && <div className="flex flex-col"><span className="text-muted-foreground text-[10px] uppercase">Library</span><span className="text-foreground font-medium truncate">{ev.library}</span></div>}
                      {ev.api && <div className="flex flex-col"><span className="text-muted-foreground text-[10px] uppercase">API</span><span className="text-foreground font-medium truncate">{ev.api}</span></div>}
                      {ev.algorithm && <div className="flex flex-col"><span className="text-muted-foreground text-[10px] uppercase">Algorithm</span><span className="text-emerald-500 font-medium truncate">{ev.algorithm}</span></div>}
                      {ev.line && <div className="flex flex-col"><span className="text-muted-foreground text-[10px] uppercase">Line</span><span className="text-foreground font-medium">{ev.line}</span></div>}
                      {ev.evidence && <div className="col-span-2 flex flex-col mt-1"><span className="text-muted-foreground text-[10px] uppercase mb-1">Code</span><span className="text-foreground font-mono bg-background p-1.5 rounded border border-border truncate">{ev.evidence}</span></div>}
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
