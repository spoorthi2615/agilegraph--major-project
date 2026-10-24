import React, { useState, useEffect, useMemo } from 'react';
import { useProject } from '../context/ProjectContext';
import { apiClient } from '../api/client';
import type { CryptoInventoryResponse, CryptoInventoryItem } from '../api/client';
import { Database, Search, AlertCircle, Info, Shield, CheckCircle, XCircle, Activity, Link as LinkIcon, Filter, X } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function CryptoInventory() {
  const { projectId, setProjectId } = useProject();
  const [data, setData] = useState<CryptoInventoryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters & Search
  const [searchQuery, setSearchQuery] = useState('');
  const [languageFilter, setLanguageFilter] = useState('');
  const [algorithmFilter, setAlgorithmFilter] = useState('');
  const [libraryFilter, setLibraryFilter] = useState('');
  const [evidenceFilter, setEvidenceFilter] = useState('');
  
  // Selection
  const [selectedItem, setSelectedItem] = useState<CryptoInventoryItem | null>(null);

  const fetchInventory = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!projectId) return;
    setLoading(true);
    setError(null);
    setSelectedItem(null);
    try {
      const result = await apiClient.getCryptoInventory(projectId);
      setData(result);
    } catch (err: any) {
      setError(err.message || "Inventory data could not be loaded.");
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (projectId) {
      fetchInventory();
    } else {
      setData(null);
    }
  }, [projectId]);

  const filteredItems = useMemo(() => {
    if (!data) return [];
    return data.items.filter((item: CryptoInventoryItem) => {
      const q = searchQuery.toLowerCase();
      const matchesSearch = 
        (item.asset_id && item.asset_id.toLowerCase().includes(q)) ||
        (item.algorithm && item.algorithm.toLowerCase().includes(q)) ||
        (item.operation && item.operation.toLowerCase().includes(q)) ||
        (item.library && item.library.toLowerCase().includes(q));

      const matchesLang = languageFilter ? item.language === languageFilter : true;
      const matchesAlg = algorithmFilter ? item.algorithm === algorithmFilter : true;
      const matchesLib = libraryFilter ? item.library === libraryFilter : true;
      const matchesEvid = evidenceFilter ? item.evidence_status === evidenceFilter : true;

      return matchesSearch && matchesLang && matchesAlg && matchesLib && matchesEvid;
    });
  }, [data, searchQuery, languageFilter, algorithmFilter, libraryFilter, evidenceFilter]);

  const uniqueValues = (key: keyof CryptoInventoryItem) => {
    if (!data) return [];
    const vals = new Set(data.items.map((i: CryptoInventoryItem) => i[key]).filter(Boolean));
    return Array.from(vals).sort() as string[];
  };

  return (
    <div className="flex flex-col gap-8 w-full max-w-7xl mx-auto font-sans animate-fade-up">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 relative">
        <div className="absolute -inset-8 rounded-3xl bg-gradient-to-br from-primary/10 to-transparent blur-2xl -z-10"></div>
        <div className="flex flex-col gap-2">
          <div className="text-xs font-semibold uppercase tracking-widest text-primary">Data View</div>
          <h2 className="text-3xl font-semibold tracking-tight text-foreground md:text-4xl flex items-center gap-3">
            <Database className="w-8 h-8 text-primary" /> Cryptographic Inventory
          </h2>
          <p className="text-muted-foreground max-w-2xl mt-1">
            Cryptographic usage discovered from the project's scanned source and dependency evidence.
          </p>
        </div>
        <form onSubmit={fetchInventory} className="flex gap-2 items-center bg-card p-1.5 rounded-lg border border-border shadow-sm">
          <input 
            type="text" 
            value={projectId} 
            onChange={e => setProjectId(e.target.value)}
            className="bg-background border-none rounded-md px-3 py-1.5 text-sm outline-none focus:ring-1 focus:ring-ring w-48"
            placeholder="Project ID"
            required
          />
          <button type="submit" disabled={loading || !projectId} className="bg-primary hover:bg-primary/90 disabled:opacity-50 px-4 py-1.5 rounded-md text-sm font-medium text-primary-foreground transition-colors shadow-glow">
            {loading ? 'Loading...' : 'Fetch'}
          </button>
        </form>
      </div>

      {error && (
        <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-xl flex items-start gap-3 text-destructive-foreground shadow-sm">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <p>{error}</p>
        </div>
      )}

      {loading && !data && projectId && (
        <div className="flex flex-col items-center justify-center p-16 text-muted-foreground border-2 border-dashed border-border rounded-2xl bg-card/50">
          <Activity className="w-10 h-10 mb-4 animate-spin opacity-50 text-primary" />
          <span className="font-medium">Loading cryptographic inventory...</span>
        </div>
      )}

      {!projectId && !data && (
        <div className="flex flex-col items-center justify-center p-16 text-muted-foreground border-2 border-dashed border-border rounded-2xl bg-card/50">
          <Info className="w-12 h-12 mb-4 opacity-30" />
          <p className="text-lg font-semibold text-foreground">No Project Selected</p>
          <p className="mt-2 text-center text-sm max-w-md">Run a scan or select an existing scanned project on the dashboard to view its cryptographic inventory.</p>
          <Link to="/" className="mt-6 bg-primary hover:bg-primary/90 text-primary-foreground px-5 py-2.5 rounded-lg font-medium shadow-glow transition-colors">
            Go to Overview
          </Link>
        </div>
      )}

      {!loading && !error && data && data.items.length === 0 && (
        <div className="flex flex-col items-center justify-center p-16 text-muted-foreground border-2 border-dashed border-border rounded-2xl bg-card/50">
          <Info className="w-12 h-12 mb-4 opacity-30" />
          <p className="text-lg font-semibold text-foreground">No Evidence Found</p>
          <p className="mt-2 text-sm">No cryptographic usage was discovered in the available scan evidence.</p>
        </div>
      )}

      {data && data.items.length > 0 && (
        <div className="flex flex-col gap-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard label="Crypto Usages" value={data.summary.crypto_usages} />
            <StatCard label="Algorithms Detected" value={data.summary.algorithms} />
            <StatCard label="Libraries Detected" value={data.summary.libraries} />
            <StatCard label="Languages Covered" value={data.summary.languages} />
          </div>

          <div className="flex gap-6 relative">
            {/* Main Table Area */}
            <div className={`flex-1 flex flex-col gap-4 transition-all ${selectedItem ? 'w-2/3 pr-[340px]' : 'w-full'}`}>
              
              {/* Toolbar */}
              <div className="bg-card p-3 rounded-2xl border border-border flex flex-wrap gap-3 items-center shadow-sm">
                <div className="relative flex-1 min-w-[200px]">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <input 
                    type="text" 
                    placeholder="Search asset, algorithm, operation..."
                    value={searchQuery}
                    onChange={e => setSearchQuery(e.target.value)}
                    className="w-full bg-background border border-border rounded-xl pl-9 pr-3 py-2 text-sm outline-none focus:ring-1 focus:ring-ring"
                  />
                </div>
                
                <div className="flex gap-2 items-center text-sm">
                  <Filter className="w-4 h-4 text-muted-foreground mx-1" />
                  <select 
                    value={languageFilter} 
                    onChange={e => setLanguageFilter(e.target.value)}
                    className="bg-background border border-border rounded-lg px-2 py-2 outline-none focus:ring-1 focus:ring-ring"
                  >
                    <option value="">All Languages</option>
                    {uniqueValues('language').map(v => <option key={v} value={v}>{v}</option>)}
                  </select>
                  
                  <select 
                    value={algorithmFilter} 
                    onChange={e => setAlgorithmFilter(e.target.value)}
                    className="bg-background border border-border rounded-lg px-2 py-2 outline-none focus:ring-1 focus:ring-ring"
                  >
                    <option value="">All Algorithms</option>
                    {uniqueValues('algorithm').map(v => <option key={v} value={v}>{v}</option>)}
                  </select>

                  <select 
                    value={libraryFilter} 
                    onChange={e => setLibraryFilter(e.target.value)}
                    className="bg-background border border-border rounded-lg px-2 py-2 outline-none focus:ring-1 focus:ring-ring"
                  >
                    <option value="">All Libraries</option>
                    {uniqueValues('library').map(v => <option key={v} value={v}>{v}</option>)}
                  </select>

                  <select 
                    value={evidenceFilter} 
                    onChange={e => setEvidenceFilter(e.target.value)}
                    className="bg-background border border-border rounded-lg px-2 py-2 outline-none focus:ring-1 focus:ring-ring"
                  >
                    <option value="">All Evidence</option>
                    {uniqueValues('evidence_status').map(v => <option key={v} value={v}>{v}</option>)}
                  </select>
                </div>
              </div>

              {/* Table */}
              <div className="bg-card rounded-2xl border border-border shadow-elevated overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm text-left">
                    <thead className="bg-muted/50 text-muted-foreground border-b border-border">
                      <tr>
                        <th className="px-5 py-3 font-semibold">Asset</th>
                        <th className="px-5 py-3 font-semibold">Language</th>
                        <th className="px-5 py-3 font-semibold">Algorithm</th>
                        <th className="px-5 py-3 font-semibold">Operation</th>
                        <th className="px-5 py-3 font-semibold">Library</th>
                        <th className="px-5 py-3 font-semibold">Evidence</th>
                        <th className="px-5 py-3 font-semibold">Risk</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/50">
                      {filteredItems.map((item: CryptoInventoryItem) => (
                        <tr 
                          key={item.asset_id} 
                          onClick={() => setSelectedItem(item)}
                          className={`cursor-pointer hover:bg-muted/30 transition-colors ${selectedItem?.asset_id === item.asset_id ? 'bg-primary/5' : ''}`}
                        >
                          <td className="px-5 py-3.5 font-mono text-xs text-primary max-w-[200px] truncate" title={item.asset_id}>
                            {item.asset_id.split('/').pop() || item.asset_id}
                          </td>
                          <td className="px-5 py-3.5">
                            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium uppercase tracking-wider bg-secondary text-secondary-foreground border border-border">
                              {item.language || '-'}
                            </span>
                          </td>
                          <td className="px-5 py-3.5 font-mono text-emerald-500 font-medium">{item.algorithm || '-'}</td>
                          <td className="px-5 py-3.5 text-foreground">{item.operation || '-'}</td>
                          <td className="px-5 py-3.5 text-muted-foreground truncate max-w-[120px]">{item.library || '-'}</td>
                          <td className="px-5 py-3.5">
                            <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider ${item.evidence_status === 'Assessed' ? 'bg-success/15 text-success border border-success/20' : 'bg-muted text-muted-foreground border border-border'}`}>
                              {item.evidence_status}
                            </span>
                          </td>
                          <td className="px-5 py-3.5">
                            {item.risk !== null ? (
                              <span className={`font-semibold ${item.risk > 0.5 ? 'text-critical' : 'text-muted-foreground'}`}>
                                {item.risk.toFixed(2)}
                              </span>
                            ) : <span className="text-muted-foreground">-</span>}
                          </td>
                        </tr>
                      ))}
                      {filteredItems.length === 0 && (
                        <tr>
                          <td colSpan={7} className="px-5 py-12 text-center text-muted-foreground">
                            No assets match the current filters.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

            </div>

            {/* Details Sidebar */}
            {selectedItem && (
              <div className="absolute right-0 top-0 bottom-0 w-[320px] bg-card border border-border shadow-elevated rounded-2xl p-5 flex flex-col gap-5 overflow-y-auto z-10 animate-in slide-in-from-right-4">
                <div className="flex justify-between items-start">
                  <h3 className="text-lg font-semibold flex items-center gap-2 text-foreground">
                    <Info className="w-5 h-5 text-primary" /> Item Details
                  </h3>
                  <button onClick={() => setSelectedItem(null)} className="p-1.5 hover:bg-muted text-muted-foreground hover:text-foreground rounded-lg transition-colors">
                    <X className="w-4 h-4" />
                  </button>
                </div>

                <div className="flex flex-col gap-4 text-sm">
                  <div>
                    <label className="text-muted-foreground text-[10px] uppercase tracking-wider font-semibold block mb-1.5">Asset ID</label>
                    <div className="font-mono text-primary text-xs break-all bg-background p-3 rounded-xl border border-border">
                      {selectedItem.asset_id}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-muted-foreground text-[10px] uppercase tracking-wider font-semibold block mb-1.5">Language</label>
                      <div className="text-foreground font-medium">{selectedItem.language || 'N/A'}</div>
                    </div>
                    <div>
                      <label className="text-muted-foreground text-[10px] uppercase tracking-wider font-semibold block mb-1.5">Algorithm</label>
                      <div className="font-mono text-emerald-500 font-medium">{selectedItem.algorithm || 'N/A'}</div>
                    </div>
                    <div>
                      <label className="text-muted-foreground text-[10px] uppercase tracking-wider font-semibold block mb-1.5">Operation</label>
                      <div className="text-foreground">{selectedItem.operation || 'N/A'}</div>
                    </div>
                    <div>
                      <label className="text-muted-foreground text-[10px] uppercase tracking-wider font-semibold block mb-1.5">Library</label>
                      <div className="text-muted-foreground">{selectedItem.library || 'N/A'}</div>
                    </div>
                  </div>

                  <div>
                    <label className="text-muted-foreground text-[10px] uppercase tracking-wider font-semibold block mb-1.5">Source Evidence</label>
                    <div className="font-mono text-xs text-foreground bg-background p-3 rounded-xl border border-border">
                      {selectedItem.source && selectedItem.source !== 'Unknown:?' ? selectedItem.source : <span className="italic text-muted-foreground">Source location not available from current scanner evidence.</span>}
                    </div>
                  </div>
                  
                  <div>
                    <label className="text-muted-foreground text-[10px] uppercase tracking-wider font-semibold block mb-1.5">Status</label>
                    <div>
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider ${selectedItem.evidence_status === 'Assessed' ? 'bg-success/15 text-success border border-success/20' : 'bg-muted text-muted-foreground border border-border'}`}>
                        {selectedItem.evidence_status}
                      </span>
                    </div>
                  </div>

                  {selectedItem.risk !== null && (
                    <div className="bg-background p-4 rounded-xl border border-border flex items-center justify-between">
                      <label className="text-muted-foreground text-[10px] uppercase tracking-wider font-semibold">Heuristic Risk</label>
                      <div className={`text-xl font-bold ${selectedItem.risk > 0.5 ? 'text-critical' : 'text-foreground'}`}>
                        {selectedItem.risk.toFixed(3)}
                      </div>
                    </div>
                  )}

                  <div className="mt-2 pt-5 border-t border-border flex flex-col gap-2">
                    <Link to="/risk" className="flex items-center gap-2 text-sm font-semibold p-2.5 bg-primary/10 text-primary rounded-lg border border-primary/20 hover:bg-primary/20 transition-colors">
                      <Shield className="w-4 h-4" /> View Risk Analysis
                    </Link>
                    <Link to="/graph" className="flex items-center gap-2 text-sm font-semibold p-2.5 bg-secondary text-secondary-foreground rounded-lg border border-border hover:bg-secondary/80 transition-colors">
                      <LinkIcon className="w-4 h-4" /> View in Crypto Graph
                    </Link>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Coverage Section */}
      {data && (
        <div className="bg-card rounded-2xl p-6 border border-border shadow-sm mt-2">
          <h3 className="text-base font-semibold mb-4 flex items-center gap-2 text-foreground">
            <CheckCircle className="w-5 h-5 text-success" /> Collection Coverage
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <CoverageItem label="Certificates" status={data.coverage.certificates} />
            <CoverageItem label="Endpoints" status={data.coverage.endpoints} />
            <CoverageItem label="Sensitive data" status={data.coverage.sensitive_data} />
          </div>
          <p className="mt-4 text-[11px] text-muted-foreground italic">
            * Graph reflects node types currently instantiated by the available scanner evidence.
          </p>
        </div>
      )}

      {/* Disclaimers */}
      {data && (
        <div className="flex flex-col gap-1.5 mt-2 p-5 bg-muted/30 rounded-2xl border border-border text-xs text-muted-foreground text-center">
          <p>Inventory reflects cryptographic evidence collected by the current AgileGraph scanners. It is <strong className="text-foreground">not</strong> expert-validated ground truth.</p>
          <p>Risk values shown here are preliminary heuristic assessments; expert validation and GATv2 evaluation are currently pending.</p>
        </div>
      )}

    </div>
  );
}

function StatCard({ label, value }: { label: string, value: any }) {
  return (
    <div className="p-5 rounded-2xl bg-card border border-border shadow-sm flex flex-col">
      <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">{label}</span>
      <span className="text-3xl font-semibold text-foreground">
        {value !== undefined && value !== null ? value : <span className="text-base font-normal text-muted-foreground italic">Not available</span>}
      </span>
    </div>
  );
}

function CoverageItem({ label, status }: { label: string, status: string }) {
  const isNotCollected = status === 'NOT_COLLECTED';
  return (
    <div className="flex flex-col p-4 bg-background rounded-xl border border-border shadow-sm">
      <span className="text-sm font-semibold text-foreground">{label}</span>
      <span className={`text-xs mt-2 flex items-center gap-1.5 font-medium ${isNotCollected ? 'text-warning' : 'text-muted-foreground'}`}>
        {isNotCollected ? (
          <><XCircle className="w-3.5 h-3.5" /> Not collected by current scanner</>
        ) : (
          status
        )}
      </span>
    </div>
  );
}
