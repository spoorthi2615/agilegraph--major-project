import { useState, useEffect } from 'react';
import { useProject } from '../../context/ProjectContext';
import { apiClient } from '../../api/client';
import { AlertCircle, ShieldAlert, Activity, Info, FileCode, CheckCircle2 } from 'lucide-react';
export default function PqcReadiness() {
  const { projectId, setProjectId } = useProject();
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
    if (projectId) {
      fetchReadiness();
    } else {
      setData(null);
    }
  }, [projectId]);

  return (
    <div className="flex flex-col gap-8 w-full max-w-7xl mx-auto font-sans animate-fade-up">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 relative">
        <div className="absolute -inset-8 rounded-3xl bg-gradient-to-br from-primary/10 to-transparent blur-2xl -z-10"></div>
        <div className="flex flex-col gap-2">
          <div className="text-xs font-semibold uppercase tracking-widest text-primary">Evidence Summary</div>
          <h2 className="text-3xl font-semibold tracking-tight text-foreground md:text-4xl flex items-center gap-3">
            <Activity className="w-8 h-8 text-primary" /> PQC Readiness
          </h2>
          <p className="text-muted-foreground max-w-2xl mt-1">
            Summarizes available cryptographic evidence relevant to post-quantum migration.
          </p>
        </div>
        <form onSubmit={fetchReadiness} className="flex gap-2 items-center bg-card p-1.5 rounded-lg border border-border shadow-sm">
          <input 
            type="text" 
            value={projectId} 
            onChange={e => setProjectId(e.target.value)}
            className="bg-background border-none rounded-md px-3 py-1.5 text-sm outline-none focus:ring-1 focus:ring-ring w-48"
            placeholder="Project ID"
          />
          <button type="submit" disabled={loading || !projectId} className="bg-primary hover:bg-primary/90 disabled:opacity-50 px-4 py-1.5 rounded-md text-sm font-medium text-primary-foreground transition-colors shadow-glow">
            {loading ? 'Loading...' : 'Fetch'}
          </button>
        </form>
      </div>

      {error && (
        <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-xl flex items-start gap-3 text-destructive">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <p>{error}</p>
        </div>
      )}

      {!projectId ? (
        <div className="flex flex-col items-center justify-center p-16 text-muted-foreground border-2 border-dashed border-border rounded-2xl bg-background/50 h-[400px] w-full">
          <Info className="w-12 h-12 mb-4 opacity-30" />
          <p className="text-lg font-semibold text-foreground">No Project Selected</p>
          <p className="text-sm mt-2 text-center max-w-sm">Please select a project or enter a Project ID to view PQC readiness.</p>
        </div>
      ) : data ? (
        <div className="flex flex-col gap-8">
          {/* Preliminary Status Badge */}
          <div className="p-4 bg-warning/10 border border-warning/20 rounded-xl flex items-start gap-3">
            <ShieldAlert className="w-5 h-5 text-warning shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-warning text-sm">Preliminary heuristic — initial configurable weights.</h3>
              <p className="text-sm text-warning/80 mt-1">{data.semantic_disclaimer || "Inventory/coverage summary, not a scientifically validated PQC readiness score."}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <StatCard label="Total Assets" value={data.asset_count} />
            <StatCard label="Assessed Assets" value={data.assessed_assets} />
            <StatCard label="Insufficient Evidence" value={data.insufficient_evidence_assets} alert={data.insufficient_evidence_assets > 0} />
            <StatCard label="Requiring Attention" value={data.assets_requiring_attention} />
            <StatCard label="Migration Candidates" value={data.migration_candidates} />
            <StatCard label="Unknown Algorithms" value={data.unknown_algorithms} alert={data.unknown_algorithms > 0} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="bg-card border border-border rounded-2xl p-6 shadow-elevated flex flex-col gap-6">
              <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
                <FileCode className="w-5 h-5 text-primary" /> Recognized Algorithms
              </h3>
              <div className="flex flex-wrap gap-2">
                {data.recognized_algorithms?.length > 0 ? (
                  data.recognized_algorithms.map((alg: string) => (
                    <span key={alg} className="px-3 py-1.5 bg-muted/50 border border-border rounded-lg text-sm font-mono text-foreground shadow-sm">
                      {alg}
                    </span>
                  ))
                ) : (
                  <span className="text-muted-foreground italic text-sm">Not available</span>
                )}
              </div>
            </div>

            <div className="bg-card border border-border rounded-2xl p-6 shadow-elevated flex flex-col gap-6">
              <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-primary" /> Evidence Coverage
              </h3>
              <div className="flex flex-col gap-3">
                <CoverageItem label="File Dependencies" status="COLLECTED" />
                <CoverageItem label="Library Imports" status="COLLECTED" />
                <CoverageItem label="Certificates" status="NOT_COLLECTED" />
                <CoverageItem label="Endpoints" status="NOT_COLLECTED" />
                <CoverageItem label="Sensitive Data" status="NOT_COLLECTED" />
              </div>
            </div>
          </div>
        </div>
      ) : (
        loading && (
          <div className="flex flex-col items-center justify-center p-16 text-muted-foreground h-[400px]">
            <Activity className="w-10 h-10 mb-4 animate-spin text-primary opacity-50" />
            <span className="font-medium">Loading readiness data...</span>
          </div>
        )
      )}
    </div>
  );
}

function StatCard({ label, value, alert = false }: { label: string, value: any, alert?: boolean }) {
  return (
    <div className={`p-5 rounded-2xl border ${alert ? 'bg-warning/10 border-warning/30 shadow-sm' : 'bg-card border-border shadow-sm'} flex flex-col gap-2`}>
      <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{label}</span>
      <span className={`text-3xl font-bold ${alert ? 'text-warning' : 'text-foreground'}`}>
        {value !== undefined && value !== null ? value : <span className="text-lg font-normal text-muted-foreground italic">Not available</span>}
      </span>
    </div>
  );
}

function CoverageItem({ label, status }: { label: string, status: string }) {
  const isCollected = status === 'COLLECTED';
  return (
    <div className="flex items-center justify-between p-3 bg-muted/30 border border-border/50 rounded-xl">
      <span className="text-sm font-medium text-foreground">{label}</span>
      <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${
        isCollected 
          ? 'bg-success/15 text-success border-success/20' 
          : 'bg-muted text-muted-foreground border-border'
      }`}>
        {status}
      </span>
    </div>
  );
}
