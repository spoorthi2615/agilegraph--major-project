import { useState } from 'react';
import { apiClient } from '../../api/client';
import { Search, AlertCircle, Calculator } from 'lucide-react';

export default function MoscaReadiness() {
  const [x, setX] = useState<number>(24);
  const [y, setY] = useState<number>(12);
  const [z, setZ] = useState<number>(30);
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Evaluate initially or when the user wants to
  const handleEvaluate = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
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
    <div className="flex flex-col gap-8 w-full max-w-7xl mx-auto font-sans animate-fade-up">
      {/* Page Header */}
      <div className="flex flex-col gap-2 relative">
        <div className="absolute -inset-8 rounded-3xl bg-gradient-to-br from-primary/10 to-transparent blur-2xl -z-10"></div>
        <div className="text-xs font-semibold uppercase tracking-widest text-primary">Theorem Analysis</div>
        <h2 className="text-3xl font-semibold tracking-tight text-foreground md:text-4xl flex items-center gap-3">
          <Calculator className="w-8 h-8 text-primary" /> Mosca Readiness
        </h2>
        <p className="text-muted-foreground max-w-2xl mt-1">
          Planning view based on confidentiality period, migration time, and quantum capability horizon.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-1 flex flex-col gap-6">
          <div className="bg-card border border-border rounded-2xl p-6 shadow-sm flex flex-col gap-4">
            <h3 className="text-base font-semibold flex items-center gap-2 text-foreground">
              <Search className="w-4 h-4 text-primary" /> Parameters
            </h3>
            
            <form onSubmit={handleEvaluate} className="flex flex-col gap-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Data Confidentiality Period (x)</label>
                <div className="flex items-center gap-2">
                  <input 
                    type="number" 
                    value={x} 
                    onChange={e => setX(parseInt(e.target.value))}
                    className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-ring transition-shadow font-mono"
                  />
                  <span className="text-xs font-medium text-muted-foreground w-12">months</span>
                </div>
              </div>
              
              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Migration Time (y)</label>
                <div className="flex items-center gap-2">
                  <input 
                    type="number" 
                    value={y} 
                    onChange={e => setY(parseInt(e.target.value))}
                    className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-ring transition-shadow font-mono"
                  />
                  <span className="text-xs font-medium text-muted-foreground w-12">months</span>
                </div>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Quantum Horizon (z)</label>
                <div className="flex items-center gap-2">
                  <input 
                    type="number" 
                    value={z} 
                    onChange={e => setZ(parseInt(e.target.value))}
                    className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-ring transition-shadow font-mono"
                  />
                  <span className="text-xs font-medium text-muted-foreground w-12">months</span>
                </div>
              </div>

              <button type="submit" disabled={loading} className="w-full mt-2 bg-primary hover:bg-primary/90 text-primary-foreground font-semibold py-2 px-4 rounded-lg transition-all shadow-glow flex justify-center items-center">
                {loading ? 'Evaluating...' : 'Evaluate Mosca'}
              </button>
            </form>

            <div className="mt-4 p-4 bg-muted/30 border border-border/50 rounded-xl text-xs text-muted-foreground">
              <p className="font-semibold text-foreground mb-1">Planning Assumption</p>
              <p className="leading-relaxed">
                <span className="font-mono text-primary font-bold">z</span> is a configurable planning assumption, not a scientific prediction of quantum capability. AgileGraph does not predict when CRQCs will exist.
              </p>
            </div>
          </div>
        </div>

        <div className="lg:col-span-2 flex flex-col gap-6">
          {error && (
            <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-xl flex items-start gap-3 text-destructive shadow-sm">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              <p>{error}</p>
            </div>
          )}

          {data ? (
            <div className="bg-card border border-border rounded-2xl shadow-elevated flex flex-col overflow-hidden">
              <div className="p-5 border-b border-border bg-background/50 flex justify-between items-center">
                <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
                  Mosca Theorem <span className="text-muted-foreground text-sm font-normal ml-2 font-mono">x + y vs z</span>
                </h3>
              </div>
              
              <div className="p-8 flex flex-col gap-8 items-center bg-card">
                <div className="flex flex-col md:flex-row items-center gap-6 w-full justify-center">
                  <div className="flex flex-col items-center gap-2 flex-1 max-w-[200px]">
                    <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Required Time (x+y)</span>
                    <div className="h-24 w-full bg-muted/30 border border-border rounded-2xl flex flex-col items-center justify-center shadow-inner">
                      <span className="text-4xl font-mono font-bold text-foreground">{data.total !== null ? data.total : '--'}</span>
                      <span className="text-[10px] text-muted-foreground uppercase tracking-widest mt-1">Months</span>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-center font-mono text-4xl text-primary font-bold px-4">
                    {data.status === 'AT_RISK' ? '>' : data.status === 'NOT_AT_RISK' ? '≤' : '?'}
                  </div>

                  <div className="flex flex-col items-center gap-2 flex-1 max-w-[200px]">
                    <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Quantum Horizon (z)</span>
                    <div className="h-24 w-full bg-muted/30 border border-border rounded-2xl flex flex-col items-center justify-center shadow-inner">
                      <span className="text-4xl font-mono font-bold text-foreground">{data.z !== null ? data.z : '--'}</span>
                      <span className="text-[10px] text-muted-foreground uppercase tracking-widest mt-1">Months</span>
                    </div>
                  </div>
                </div>

                <div className={`w-full max-w-2xl p-6 rounded-2xl border flex flex-col items-center text-center gap-3 ${
                  data.status === 'AT_RISK' ? 'bg-destructive/10 border-destructive/30' :
                  data.status === 'NOT_AT_RISK' ? 'bg-success/10 border-success/30' :
                  'bg-warning/10 border-warning/30'
                }`}>
                  <span className={`text-sm font-bold uppercase tracking-widest px-3 py-1 rounded-full border ${
                    data.status === 'AT_RISK' ? 'bg-destructive/20 text-destructive border-destructive/30' :
                    data.status === 'NOT_AT_RISK' ? 'bg-success/20 text-success border-success/30' :
                    'bg-warning/20 text-warning border-warning/30'
                  }`}>
                    {data.status}
                  </span>
                  <p className={`text-base font-medium ${
                    data.status === 'AT_RISK' ? 'text-destructive' :
                    data.status === 'NOT_AT_RISK' ? 'text-success' :
                    'text-warning'
                  }`}>
                    {data.explanation}
                  </p>
                </div>
              </div>
            </div>
          ) : loading ? (
            <div className="flex flex-col items-center justify-center p-16 text-muted-foreground border-2 border-dashed border-border m-6 rounded-2xl bg-background/50 h-[300px]">
              <Calculator className="w-10 h-10 mb-4 animate-spin text-primary opacity-50" />
              <span className="font-medium">Evaluating Mosca theorem...</span>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center p-16 text-muted-foreground border-2 border-dashed border-border m-6 rounded-2xl bg-background/50 h-[300px]">
              <Calculator className="w-10 h-10 mb-4 opacity-30 text-primary" />
              <p className="text-base font-semibold text-foreground">Awaiting Evaluation</p>
              <span className="text-sm mt-1 text-center max-w-xs">Configure parameters on the left and click &quot;Evaluate Mosca&quot; to calculate theorem results.</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
