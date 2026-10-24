import { useState, useEffect } from 'react';
import { useProject } from '../context/ProjectContext';
import { apiClient } from '../api/client';
import type { RiskResponse, GraphResponse } from '../api/client';
import { escapeCsvValue } from '../utils/csv';
import { PieChart, Download, FileText, FileSpreadsheet, AlertCircle, CheckCircle2, Shield, Info, Database } from 'lucide-react';

interface PriorityData {
  priority: string;
  rationale: string;
  pqc_relevance?: boolean;
  mosca_status?: string;
}

export default function Reports() {
  const { projectId, setProjectId } = useProject();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [graphData, setGraphData] = useState<GraphResponse | null>(null);
  const [riskData, setRiskData] = useState<RiskResponse | null>(null);
  const [priorities, setPriorities] = useState<Record<string, PriorityData>>({});
  const [downloadSuccess, setDownloadSuccess] = useState<string | null>(null);

  const fetchProjectData = async (idToFetch?: string) => {
    const id = idToFetch || projectId;
    if (!id) {
      setGraphData(null);
      setRiskData(null);
      setPriorities({});
      return;
    }

    setLoading(true);
    setError(null);
    setDownloadSuccess(null);

    try {
      const [graphRes, riskRes] = await Promise.all([
        apiClient.getGraph(id),
        apiClient.getRisk(id)
      ]);

      setGraphData(graphRes);
      setRiskData(riskRes);

      // Fetch migration priorities for scored assets where available
      if (riskRes?.assets && riskRes.assets.length > 0) {
        const priorityEntries = await Promise.all(
          riskRes.assets.map(async (asset) => {
            try {
              const p = await apiClient.getMigrationPriority(id, asset.asset_id, 'NOT_AT_RISK');
              return [asset.asset_id, {
                priority: p.priority || 'NOT_ASSESSED',
                rationale: p.rationale || '',
                pqc_relevance: p.pqc_relevance,
                mosca_status: p.mosca_status
              }] as const;
            } catch {
              return [asset.asset_id, {
                priority: 'NOT_ASSESSED',
                rationale: 'Priority unavailable',
                pqc_relevance: false,
                mosca_status: 'UNKNOWN'
              }] as const;
            }
          })
        );
        setPriorities(Object.fromEntries(priorityEntries));
      } else {
        setPriorities({});
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load report data for project.');
      setGraphData(null);
      setRiskData(null);
      setPriorities({});
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (projectId) {
      fetchProjectData(projectId);
    } else {
      setGraphData(null);
      setRiskData(null);
      setPriorities({});
      setError(null);
    }
  }, [projectId]);

  const generateReportPayload = () => {
    if (!projectId || !riskData || !graphData) return null;

    // Build node type map
    const nodeTypeMap: Record<string, string> = {};
    for (const node of graphData.nodes || []) {
      const nId = node.id || node.asset_id;
      if (nId) {
        nodeTypeMap[nId] = node.category || node.type || 'file';
      }
    }

    const exportedAssets = (riskData.assets || []).map((asset) => {
      const factorObj = asset.factors || {};
      const prio = priorities[asset.asset_id] || {
        priority: 'NOT_ASSESSED',
        rationale: 'Not evaluated'
      };

      return {
        asset_id: asset.asset_id,
        asset_type: nodeTypeMap[asset.asset_id] || 'file',
        heuristic_risk_score: asset.score !== null && asset.score !== undefined ? asset.score : null,
        scoring_methodology: 'Heuristic Formula (Phase 8 Composite Heuristic — Not GATv2)',
        formula_version: asset.formula_version || 'heuristic-v0.1',
        migration_priority: prio.priority,
        priority_rationale: prio.rationale,
        factors: {
          data_sensitivity: factorObj.data_sensitivity?.value ?? null,
          asset_criticality: factorObj.asset_criticality?.value ?? null,
          internet_exposure: factorObj.internet_exposure?.value ?? null,
          crypto_weakness: factorObj.crypto_weakness?.value ?? null,
          cve_risk: factorObj.cve_risk?.value ?? null,
          library_centrality: factorObj.library_centrality?.value ?? null,
          migration_difficulty: factorObj.migration_difficulty?.value ?? null
        },
        missing_factors: asset.missing_factors || [],
        missing_data_policy: asset.missing_data_policy || 'RENORMALIZE',
        assumptions: asset.assumptions || []
      };
    });

    return {
      report_metadata: {
        project_id: projectId,
        generated_at: new Date().toISOString(),
        disclaimer: 'All risk scores and migration priorities in this export are produced exclusively by deterministic heuristic algorithms and rules. They are NOT predictions from GATv2 or any trained machine learning model.',
        ml_status: riskData.ml_status || 'GATv2: ARCHITECTURAL_PROTOTYPE',
        expert_validation_status: riskData.expert_validation_status || 'NOT_APPLICABLE'
      },
      graph_summary: {
        total_nodes: graphData.nodes?.length || 0,
        total_edges: graphData.edges?.length || 0,
        evaluated_file_assets: riskData.assets?.length || 0
      },
      assets: exportedAssets
    };
  };

  const handleDownloadJson = () => {
    try {
      const payload = generateReportPayload();
      if (!payload) {
        setError('No report data available to export.');
        return;
      }
      const jsonStr = JSON.stringify(payload, null, 2);
      const blob = new Blob([jsonStr], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `agilegraph_report_${projectId.replace(/[^a-zA-Z0-9_-]/g, '_')}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      setDownloadSuccess('JSON report downloaded successfully.');
    } catch (err: any) {
      setError(`Download failed: ${err.message || 'Unknown error'}`);
    }
  };

  const handleDownloadCsv = () => {
    try {
      const payload = generateReportPayload();
      if (!payload) {
        setError('No report data available to export.');
        return;
      }

      const headers = [
        'project_id',
        'asset_id',
        'asset_type',
        'heuristic_risk_score',
        'scoring_methodology',
        'migration_priority',
        'priority_rationale',
        'factor_data_sensitivity',
        'factor_asset_criticality',
        'factor_internet_exposure',
        'factor_crypto_weakness',
        'factor_cve_risk',
        'factor_library_centrality',
        'factor_migration_difficulty',
        'missing_factors',
        'missing_data_policy'
      ];

      const rows: string[] = [];
      rows.push(headers.map(escapeCsvValue).join(','));

      for (const a of payload.assets) {
        const row = [
          projectId,
          a.asset_id,
          a.asset_type,
          a.heuristic_risk_score !== null ? a.heuristic_risk_score : '',
          a.scoring_methodology,
          a.migration_priority,
          a.priority_rationale,
          a.factors.data_sensitivity !== null ? a.factors.data_sensitivity : '',
          a.factors.asset_criticality !== null ? a.factors.asset_criticality : '',
          a.factors.internet_exposure !== null ? a.factors.internet_exposure : '',
          a.factors.crypto_weakness !== null ? a.factors.crypto_weakness : '',
          a.factors.cve_risk !== null ? a.factors.cve_risk : '',
          a.factors.library_centrality !== null ? a.factors.library_centrality : '',
          a.factors.migration_difficulty !== null ? a.factors.migration_difficulty : '',
          (a.missing_factors || []).join('; '),
          a.missing_data_policy
        ];
        rows.push(row.map(escapeCsvValue).join(','));
      }

      const csvContent = rows.join('\r\n');
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `agilegraph_report_${projectId.replace(/[^a-zA-Z0-9_-]/g, '_')}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      setDownloadSuccess('CSV report downloaded successfully.');
    } catch (err: any) {
      setError(`Download failed: ${err.message || 'Unknown error'}`);
    }
  };

  const hasData = !!riskData && !!graphData && (riskData.assets?.length > 0 || graphData.nodes?.length > 0);

  return (
    <div className="flex flex-col gap-8 w-full max-w-7xl mx-auto font-sans animate-fade-up">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 relative">
        <div className="absolute -inset-8 rounded-3xl bg-gradient-to-br from-primary/10 to-transparent blur-2xl -z-10"></div>
        <div className="flex flex-col gap-2">
          <div className="text-xs font-semibold uppercase tracking-widest text-primary">Export Center</div>
          <h2 className="text-3xl font-semibold tracking-tight text-foreground md:text-4xl flex items-center gap-3">
            <PieChart className="w-8 h-8 text-primary" /> Reports &amp; Data Export
          </h2>
          <p className="text-muted-foreground max-w-2xl mt-1">
            Generate and export reproducible risk audit reports for scanned projects in standard CSV and JSON formats.
          </p>
        </div>

        {/* Project Selector Form */}
        <form 
          onSubmit={(e) => { e.preventDefault(); fetchProjectData(); }} 
          className="flex gap-2 items-center bg-card p-1.5 rounded-lg border border-border shadow-sm"
        >
          <input 
            type="text" 
            value={projectId} 
            onChange={(e) => setProjectId(e.target.value)}
            className="bg-background border-none rounded-md px-3 py-1.5 text-sm outline-none focus:ring-1 focus:ring-ring w-48 font-mono"
            placeholder="e.g. org/repo"
            required
            aria-label="Project ID"
          />
          <button 
            type="submit" 
            disabled={loading || !projectId} 
            className="bg-primary hover:bg-primary/90 disabled:opacity-50 px-4 py-1.5 rounded-md text-sm font-medium text-primary-foreground transition-colors shadow-glow"
          >
            {loading ? 'Loading...' : 'Load Project'}
          </button>
        </form>
      </div>

      {/* Status Banners */}
      {error && (
        <div className="flex items-center gap-3 p-4 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm" role="alert">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {downloadSuccess && (
        <div className="flex items-center gap-3 p-4 rounded-xl bg-success/10 border border-success/20 text-success text-sm" role="status">
          <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
          <span>{downloadSuccess}</span>
        </div>
      )}

      {/* Methodology Disclaimer Banner */}
      <div className="flex items-start gap-3 p-4 rounded-xl bg-card border border-border text-muted-foreground text-xs leading-relaxed">
        <Info className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" />
        <div>
          <strong className="text-foreground">Methodology Integrity Note:</strong> All exported risk values and priorities represent operational estimates derived from deterministic 7-factor heuristic scoring with missing-data handling. GATv2 is an architectural prototype; no predictive machine learning inferences or statistical claims are included in these exports.
        </div>
      </div>

      {/* Main Content Area */}
      {!projectId ? (
        <div className="bg-card border border-border rounded-2xl p-12 text-center flex flex-col items-center justify-center gap-3 shadow-sm">
          <Database className="w-12 h-12 text-muted-foreground/50" />
          <h3 className="text-lg font-semibold text-foreground">No Project Selected</h3>
          <p className="text-sm text-muted-foreground max-w-md">
            Enter a Project ID above or scan a repository on the Overview dashboard to generate and export reports.
          </p>
        </div>
      ) : loading ? (
        <div className="bg-card border border-border rounded-2xl p-12 text-center flex flex-col items-center justify-center gap-3 shadow-sm">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
          <p className="text-sm text-muted-foreground">Loading project data and graph topology...</p>
        </div>
      ) : !hasData ? (
        <div className="bg-card border border-border rounded-2xl p-12 text-center flex flex-col items-center justify-center gap-3 shadow-sm">
          <AlertCircle className="w-12 h-12 text-warning/50" />
          <h3 className="text-lg font-semibold text-foreground">No Scanned Assets Found</h3>
          <p className="text-sm text-muted-foreground max-w-md">
            Project <code className="bg-muted px-1.5 py-0.5 rounded text-xs">{projectId}</code> has not been scanned yet or contains no eligible cryptographic records.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Export Actions Card */}
          <div className="lg:col-span-1 flex flex-col gap-6">
            <div className="bg-card border border-border rounded-2xl p-6 shadow-sm flex flex-col gap-6">
              <div>
                <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
                  <Download className="w-5 h-5 text-primary" /> Export Formats
                </h3>
                <p className="text-xs text-muted-foreground mt-1">
                  Choose a format to download the complete audit trail.
                </p>
              </div>

              <div className="flex flex-col gap-3">
                <button
                  type="button"
                  onClick={handleDownloadCsv}
                  className="flex items-center justify-between p-4 rounded-xl border border-border hover:border-primary/50 bg-background/50 hover:bg-muted/50 transition-all text-left group"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2.5 rounded-lg bg-primary/10 text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                      <FileSpreadsheet className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="text-sm font-semibold text-foreground">CSV Spreadsheet</div>
                      <div className="text-xs text-muted-foreground">Formula-safe delimited tabular data</div>
                    </div>
                  </div>
                  <Download className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" />
                </button>

                <button
                  type="button"
                  onClick={handleDownloadJson}
                  className="flex items-center justify-between p-4 rounded-xl border border-border hover:border-primary/50 bg-background/50 hover:bg-muted/50 transition-all text-left group"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2.5 rounded-lg bg-blue-500/10 text-blue-500 group-hover:bg-blue-500 group-hover:text-white transition-colors">
                      <FileText className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="text-sm font-semibold text-foreground">JSON Structured Data</div>
                      <div className="text-xs text-muted-foreground">Full hierarchical audit &amp; graph metadata</div>
                    </div>
                  </div>
                  <Download className="w-4 h-4 text-muted-foreground group-hover:text-blue-500 transition-colors" />
                </button>
              </div>
            </div>

            {/* Scope & Provenance Info */}
            <div className="bg-card border border-border rounded-2xl p-6 shadow-sm flex flex-col gap-3">
              <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
                <Shield className="w-4 h-4 text-primary" /> Export Security &amp; Safety
              </h4>
              <ul className="text-xs text-muted-foreground space-y-1.5 list-disc list-inside">
                <li>Strict CSV formula injection escaping (=, +, -, @ neutralized).</li>
                <li>No source code bodies, environment keys, or tokens exported.</li>
                <li>All heuristic scores explicitly marked as non-ML calculations.</li>
              </ul>
            </div>
          </div>

          {/* Dataset Summary Preview Card */}
          <div className="lg:col-span-2 flex flex-col gap-6">
            <div className="bg-card border border-border rounded-2xl p-6 shadow-sm flex flex-col gap-6">
              <div className="flex items-center justify-between border-b border-border pb-4">
                <div>
                  <div className="text-xs text-muted-foreground uppercase tracking-wider">Project Summary</div>
                  <h3 className="text-xl font-semibold text-foreground font-mono">{projectId}</h3>
                </div>
                <span className="text-xs font-mono px-3 py-1 rounded-full bg-primary/10 text-primary border border-primary/20">
                  Ready for Export
                </span>
              </div>

              {/* Stat Counter Grid */}
              <div className="grid grid-cols-3 gap-4">
                <div className="p-4 rounded-xl bg-background border border-border">
                  <div className="text-xs text-muted-foreground">Total Graph Nodes</div>
                  <div className="text-2xl font-bold text-foreground mt-1">{graphData.nodes?.length || 0}</div>
                </div>
                <div className="p-4 rounded-xl bg-background border border-border">
                  <div className="text-xs text-muted-foreground">Total Graph Edges</div>
                  <div className="text-2xl font-bold text-foreground mt-1">{graphData.edges?.length || 0}</div>
                </div>
                <div className="p-4 rounded-xl bg-background border border-border">
                  <div className="text-xs text-muted-foreground">Scored File Assets</div>
                  <div className="text-2xl font-bold text-foreground mt-1">{riskData.assets?.length || 0}</div>
                </div>
              </div>

              {/* Asset Preview Table */}
              <div>
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                  Included Assets Preview (First 5 of {riskData.assets?.length || 0})
                </h4>
                <div className="rounded-xl border border-border overflow-hidden">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-muted/50 text-muted-foreground uppercase tracking-wider font-semibold border-b border-border">
                      <tr>
                        <th className="p-3">Asset ID</th>
                        <th className="p-3">Heuristic Score</th>
                        <th className="p-3">Migration Priority</th>
                        <th className="p-3">Missing Factors</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border font-mono">
                      {(riskData.assets || []).slice(0, 5).map((a) => {
                        const prio = priorities[a.asset_id]?.priority || 'NOT_ASSESSED';
                        return (
                          <tr key={a.asset_id} className="hover:bg-muted/20">
                            <td className="p-3 max-w-[200px] truncate text-foreground" title={a.asset_id}>
                              {a.asset_id}
                            </td>
                            <td className="p-3 font-semibold text-foreground">
                              {a.score !== null && a.score !== undefined ? a.score.toFixed(4) : 'Unrated'}
                            </td>
                            <td className="p-3">
                              <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                                prio === 'HIGH' ? 'bg-destructive/15 text-destructive' :
                                prio === 'MEDIUM' ? 'bg-warning/15 text-warning' :
                                'bg-muted text-muted-foreground'
                              }`}>
                                {prio}
                              </span>
                            </td>
                            <td className="p-3 text-muted-foreground font-sans">
                              {a.missing_factors && a.missing_factors.length > 0
                                ? `${a.missing_factors.length} missing`
                                : 'None'}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
