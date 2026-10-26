import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  Shield, 
  ArrowRight, 
  Database, 
  Network, 
  AlertTriangle, 
  Activity, 
  Search, 
  Map, 
  ChevronRight, 
  CheckCircle, 
  Code, 
  Terminal, 
  BookOpen, 
  Layers,
  Scale,
  Sparkles
} from 'lucide-react';

export default function LandingPage() {
  const { isAuthenticated, user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-blue-600 selection:text-white">
      {/* Sticky Header */}
      <header className="sticky top-0 z-50 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/20 group-hover:scale-105 transition-transform">
              <Shield className="h-5 w-5" />
            </div>
            <div className="flex flex-col">
              <span className="text-lg font-bold tracking-tight text-white font-mono">AgileGraph</span>
            </div>
          </Link>

          <nav className="hidden items-center gap-8 md:flex text-sm font-medium text-slate-300">
            <a href="#platform" className="hover:text-blue-400 transition-colors">Platform Capabilities</a>
            <a href="#how" className="hover:text-blue-400 transition-colors">How It Works</a>
            <a href="#research" className="hover:text-blue-400 transition-colors">Research & Methodology</a>
            <a href="#tech" className="hover:text-blue-400 transition-colors">Technology Stack</a>
          </nav>

          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <>
                <Link
                  to="/app"
                  className="inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-4 py-2 rounded-lg transition-colors shadow-lg shadow-blue-600/25"
                >
                  Dashboard <ArrowRight className="h-3.5 w-3.5" />
                </Link>
                <button
                  onClick={() => logout()}
                  className="text-xs text-slate-400 hover:text-slate-200 border border-slate-800 hover:bg-slate-900 px-3 py-2 rounded-lg transition-colors"
                >
                  Sign Out ({user?.username})
                </button>
              </>
            ) : (
              <>
                <Link
                  to="/login"
                  className="text-xs font-semibold text-slate-300 hover:text-white px-3 py-2 rounded-lg hover:bg-slate-900 transition-colors"
                >
                  Sign In
                </Link>
                <Link
                  to="/register"
                  className="inline-flex items-center justify-center gap-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-4 py-2 rounded-lg transition-colors shadow-lg shadow-blue-600/25"
                >
                  Get Started <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-20 pb-24 md:pt-28 md:pb-32 border-b border-slate-900">
        {/* Subtle background glow */}
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[450px] bg-blue-600/10 rounded-full blur-3xl pointer-events-none -z-10"></div>
        <div className="absolute top-1/4 right-1/4 w-[400px] h-[300px] bg-indigo-600/10 rounded-full blur-3xl pointer-events-none -z-10"></div>

        <div className="mx-auto max-w-7xl px-6">
          <div className="grid items-center gap-12 lg:grid-cols-12">
            <div className="lg:col-span-7 flex flex-col items-start">
              <div className="inline-flex items-center gap-2 rounded-full border border-blue-500/30 bg-blue-950/40 px-3.5 py-1 text-xs font-medium text-blue-300 shadow-sm mb-6">
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
                Final-Year B.Tech Cyber Security Project · NIST PQC Aligned
              </div>

              <h1 className="text-4xl font-extrabold tracking-tight text-white md:text-5xl lg:text-6xl leading-[1.1]">
                Accelerate Your{' '}
                <span className="bg-gradient-to-r from-blue-400 via-indigo-300 to-purple-400 bg-clip-text text-transparent">
                  Post-Quantum Migration
                </span>
              </h1>

              <p className="mt-6 text-base md:text-lg leading-relaxed text-slate-300 max-w-2xl">
                AgileGraph discovers cryptographic assets across Python, Java, and Go repositories, constructs a multi-relational software dependency graph, and evaluates post-quantum migration risk using a 7-factor composite heuristic engine and an experimental GATv2 neural model.
              </p>

              <div className="mt-8 flex flex-wrap items-center gap-4">
                <Link
                  to={isAuthenticated ? "/app" : "/register"}
                  className="inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold px-6 py-3 rounded-xl text-sm transition-all shadow-lg shadow-blue-600/25 hover:shadow-blue-600/40"
                >
                  {isAuthenticated ? "Open Dashboard" : "Get Started"} <ArrowRight className="h-4 w-4" />
                </Link>
                <a
                  href="#how"
                  className="inline-flex items-center justify-center gap-2 bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 font-semibold px-6 py-3 rounded-xl text-sm transition-colors"
                >
                  Learn More
                </a>
              </div>

              {/* Research Disclosure Notice */}
              <div className="mt-8 p-3.5 bg-slate-900/80 border border-slate-800 rounded-xl text-xs text-slate-400 flex items-start gap-2.5 max-w-xl">
                <Scale className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                <span>
                  <strong>Academic Research Notice:</strong> Weak-label distillation evaluated; expert-label validation blocked. GATv2 is an exploratory research prototype; runtime discoveries and composite risk scores are computed deterministically with zero suppression.
                </span>
              </div>
            </div>

            {/* Hero Interactive Topology Preview */}
            <div className="lg:col-span-5 relative">
              <div className="relative rounded-2xl border border-slate-800 bg-slate-900/90 p-5 shadow-2xl backdrop-blur-md">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
                  <div className="flex items-center gap-2">
                    <span className="h-2.5 w-2.5 rounded-full bg-red-500/80"></span>
                    <span className="h-2.5 w-2.5 rounded-full bg-amber-500/80"></span>
                    <span className="h-2.5 w-2.5 rounded-full bg-emerald-500/80"></span>
                    <span className="ml-2 font-mono text-xs text-slate-400">agilegraph:property_graph</span>
                  </div>
                  <span className="text-[11px] font-mono text-blue-400 bg-blue-950/60 border border-blue-800/50 px-2 py-0.5 rounded">
                    NetworkX MultiDiGraph
                  </span>
                </div>

                {/* SVG Graph Visualizer Graphic */}
                <div className="relative h-64 w-full bg-slate-950/60 rounded-xl border border-slate-800/80 p-2 overflow-hidden flex items-center justify-center">
                  <svg viewBox="0 0 460 250" className="w-full h-full">
                    <defs>
                      <linearGradient id="edgeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.4" />
                        <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0.1" />
                      </linearGradient>
                    </defs>
                    {/* Edges */}
                    <line x1="230" y1="125" x2="110" y2="60" stroke="#3b82f6" strokeWidth="1.5" strokeDasharray="3,3" opacity="0.6" />
                    <line x1="230" y1="125" x2="350" y2="60" stroke="#3b82f6" strokeWidth="1.5" opacity="0.6" />
                    <line x1="230" y1="125" x2="110" y2="190" stroke="#8b5cf6" strokeWidth="1.5" opacity="0.6" />
                    <line x1="230" y1="125" x2="350" y2="190" stroke="#10b981" strokeWidth="1.5" opacity="0.6" />
                    <line x1="110" y1="60" x2="50" y2="125" stroke="#64748b" strokeWidth="1" opacity="0.4" />
                    <line x1="350" y1="60" x2="410" y2="125" stroke="#64748b" strokeWidth="1" opacity="0.4" />

                    {/* Central Scored File Node */}
                    <circle cx="230" cy="125" r="28" fill="#1e293b" stroke="#3b82f6" strokeWidth="2.5" />
                    <text x="230" y="129" fill="#e2e8f0" fontSize="10" fontWeight="bold" textAnchor="middle" fontFamily="monospace">signer.py</text>

                    {/* Connected Nodes */}
                    <circle cx="110" cy="60" r="20" fill="#1e293b" stroke="#ef4444" strokeWidth="2" />
                    <text x="110" y="64" fill="#fca5a5" fontSize="9" fontWeight="bold" textAnchor="middle" fontFamily="monospace">SHA-1</text>

                    <circle cx="350" cy="60" r="20" fill="#1e293b" stroke="#10b981" strokeWidth="2" />
                    <text x="350" y="64" fill="#6ee7b7" fontSize="9" fontWeight="bold" textAnchor="middle" fontFamily="monospace">hashlib</text>

                    <circle cx="110" cy="190" r="20" fill="#1e293b" stroke="#8b5cf6" strokeWidth="2" />
                    <text x="110" y="194" fill="#c4b5fd" fontSize="8" fontWeight="bold" textAnchor="middle" fontFamily="monospace">CryptoCall</text>

                    <circle cx="350" cy="190" r="20" fill="#1e293b" stroke="#06b6d4" strokeWidth="2" />
                    <text x="350" y="194" fill="#67e8f9" fontSize="8" fontWeight="bold" textAnchor="middle" fontFamily="monospace">Endpoint</text>

                    <circle cx="50" cy="125" r="14" fill="#0f172a" stroke="#64748b" strokeWidth="1.5" />
                    <text x="50" y="128" fill="#94a3b8" fontSize="7" textAnchor="middle" fontFamily="monospace">conf.py</text>

                    <circle cx="410" cy="125" r="14" fill="#0f172a" stroke="#64748b" strokeWidth="1.5" />
                    <text x="410" y="128" fill="#94a3b8" fontSize="7" textAnchor="middle" fontFamily="monospace">reqs.txt</text>
                  </svg>
                </div>

                {/* Live Stats Breakdown */}
                <div className="mt-4 grid grid-cols-3 gap-2.5 text-center font-mono text-xs">
                  <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                    <span className="text-slate-400 block text-[10px] uppercase">Node Ontology</span>
                    <span className="text-white font-bold text-sm">6 Types</span>
                  </div>
                  <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                    <span className="text-slate-400 block text-[10px] uppercase">Risk Factors</span>
                    <span className="text-blue-400 font-bold text-sm">7 Factors</span>
                  </div>
                  <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                    <span className="text-slate-400 block text-[10px] uppercase">LOPO Corpus</span>
                    <span className="text-emerald-400 font-bold text-sm">520 Assets</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Platform Capabilities Section */}
      <section id="platform" className="py-24 border-b border-slate-900 bg-slate-950/50">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mx-auto max-w-2xl text-center">
            <span className="text-xs font-semibold uppercase tracking-widest text-blue-400 font-mono">Platform Capabilities</span>
            <h2 className="mt-3 text-3xl font-bold tracking-tight text-white md:text-4xl">
              End-to-End Cryptographic Agility & Migration
            </h2>
            <p className="mt-4 text-slate-400 text-base">
              Engineered for post-quantum preparedness: from AST source code discovery and multi-relational graphs to composite risk triage and roadmap tracking.
            </p>
          </div>

          <div className="mt-14 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {/* Card 1 */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 hover:border-slate-700 transition-colors">
              <div className="grid h-10 w-10 place-items-center rounded-xl bg-blue-950 border border-blue-800 text-blue-400 mb-4">
                <Database className="h-5 w-5" />
              </div>
              <h3 className="text-lg font-semibold text-white">Automated AST Discovery</h3>
              <p className="mt-2 text-sm text-slate-400 leading-relaxed">
                AST-driven source scanners traverse Python, Java, and Go repositories to extract ciphers, hash functions, key sizes, digital signatures, manifests, and certificates.
              </p>
            </div>

            {/* Card 2 */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 hover:border-slate-700 transition-colors">
              <div className="grid h-10 w-10 place-items-center rounded-xl bg-indigo-950 border border-indigo-800 text-indigo-400 mb-4">
                <Network className="h-5 w-5" />
              </div>
              <h3 className="text-lg font-semibold text-white">Multi-Relational Software Graph</h3>
              <p className="mt-2 text-sm text-slate-400 leading-relaxed">
                Constructs a typed NetworkX property graph with 6 node categories (File, Library, CryptoUsage, Algorithm, Certificate, Endpoint) modeling callers, dependencies, and exposure.
              </p>
            </div>

            {/* Card 3 */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 hover:border-slate-700 transition-colors">
              <div className="grid h-10 w-10 place-items-center rounded-xl bg-amber-950 border border-amber-800 text-amber-400 mb-4">
                <AlertTriangle className="h-5 w-5" />
              </div>
              <h3 className="text-lg font-semibold text-white">7-Factor Heuristic Risk Engine</h3>
              <p className="mt-2 text-sm text-slate-400 leading-relaxed">
                Calculates composite base risk [0.0–1.0] across Weakness, Criticality, Sensitivity, Exposure, Centrality, Migration Difficulty, and CVE Risk with explicit missing-evidence handling.
              </p>
            </div>

            {/* Card 4 */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 hover:border-slate-700 transition-colors">
              <div className="grid h-10 w-10 place-items-center rounded-xl bg-emerald-950 border border-emerald-800 text-emerald-400 mb-4">
                <Activity className="h-5 w-5" />
              </div>
              <h3 className="text-lg font-semibold text-white">PQC Readiness Accounting</h3>
              <p className="mt-2 text-sm text-slate-400 leading-relaxed">
                Audits primitives against NIST FIPS 203 (ML-KEM), 204 (ML-DSA), and 205 (SLH-DSA) to quantify classical cryptographic exposure and identify immediate migration candidates.
              </p>
            </div>

            {/* Card 5 */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 hover:border-slate-700 transition-colors">
              <div className="grid h-10 w-10 place-items-center rounded-xl bg-purple-950 border border-purple-800 text-purple-400 mb-4">
                <Search className="h-5 w-5" />
              </div>
              <h3 className="text-lg font-semibold text-white">Mosca Theorem Analysis</h3>
              <p className="mt-2 text-sm text-slate-400 leading-relaxed">
                Calculates urgency index $U = (X + Y) / Z$ evaluating data retention duration ($X$), migration timeline ($Y$), and quantum capability planning horizon ($Z$).
              </p>
            </div>

            {/* Card 6 */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 hover:border-slate-700 transition-colors">
              <div className="grid h-10 w-10 place-items-center rounded-xl bg-cyan-950 border border-cyan-800 text-cyan-400 mb-4">
                <Map className="h-5 w-5" />
              </div>
              <h3 className="text-lg font-semibold text-white">Migration Roadmap & Prioritization</h3>
              <p className="mt-2 text-sm text-slate-400 leading-relaxed">
                Tracks assets through an audited 6-state lifecycle (DISCOVERED $\to$ EVALUATED $\to$ IN_PLANNING $\to$ IN_MIGRATION $\to$ VALIDATED $\to$ DECOMMISSIONED) backed by SQLite persistence.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how" className="py-24 border-b border-slate-900 bg-slate-900/30">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mx-auto max-w-2xl text-center">
            <span className="text-xs font-semibold uppercase tracking-widest text-blue-400 font-mono">Workflow Architecture</span>
            <h2 className="mt-3 text-3xl font-bold tracking-tight text-white md:text-4xl">
              From Source Code to Migration Roadmap in Four Steps
            </h2>
          </div>

          <div className="mt-16 grid gap-6 md:grid-cols-4">
            {/* Step 1 */}
            <div className="rounded-2xl border border-slate-800 bg-slate-950 p-6 relative flex flex-col justify-between">
              <div>
                <div className="grid h-10 w-10 place-items-center rounded-lg bg-blue-600 text-white font-mono font-bold text-sm mb-4">
                  01
                </div>
                <h3 className="text-base font-semibold text-white">Scan Infrastructure</h3>
                <p className="mt-2 text-xs text-slate-400 leading-relaxed">
                  Provide a local repository path. AST scanners parse Python ASTs, Java source, and Go manifests to locate every cryptographic call site.
                </p>
              </div>
              <ChevronRight className="hidden md:block absolute -right-3.5 top-1/2 -translate-y-1/2 text-slate-700 w-6 h-6 z-10" />
            </div>

            {/* Step 2 */}
            <div className="rounded-2xl border border-slate-800 bg-slate-950 p-6 relative flex flex-col justify-between">
              <div>
                <div className="grid h-10 w-10 place-items-center rounded-lg bg-blue-600 text-white font-mono font-bold text-sm mb-4">
                  02
                </div>
                <h3 className="text-base font-semibold text-white">Construct Graph</h3>
                <p className="mt-2 text-xs text-slate-400 leading-relaxed">
                  GraphBuilder maps call hierarchies, library imports, network endpoints, and data sensitivity into a multi-relational property graph.
                </p>
              </div>
              <ChevronRight className="hidden md:block absolute -right-3.5 top-1/2 -translate-y-1/2 text-slate-700 w-6 h-6 z-10" />
            </div>

            {/* Step 3 */}
            <div className="rounded-2xl border border-slate-800 bg-slate-950 p-6 relative flex flex-col justify-between">
              <div>
                <div className="grid h-10 w-10 place-items-center rounded-lg bg-blue-600 text-white font-mono font-bold text-sm mb-4">
                  03
                </div>
                <h3 className="text-base font-semibold text-white">Evaluate 7 Factors</h3>
                <p className="mt-2 text-xs text-slate-400 leading-relaxed">
                  FactorExtractor evaluates each file asset against 7 factors and calculates composite risk using configurable heuristic weights.
                </p>
              </div>
              <ChevronRight className="hidden md:block absolute -right-3.5 top-1/2 -translate-y-1/2 text-slate-700 w-6 h-6 z-10" />
            </div>

            {/* Step 4 */}
            <div className="rounded-2xl border border-slate-800 bg-slate-950 p-6 relative flex flex-col justify-between">
              <div>
                <div className="grid h-10 w-10 place-items-center rounded-lg bg-blue-600 text-white font-mono font-bold text-sm mb-4">
                  04
                </div>
                <h3 className="text-base font-semibold text-white">Prioritize & Export</h3>
                <p className="mt-2 text-xs text-slate-400 leading-relaxed">
                  Downstream triage incorporates Mosca timeline bands. Export defensible Markdown dossiers, CSV matrices, and structured JSON.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Research & Methodology Section */}
      <section id="research" className="py-24 border-b border-slate-900 bg-slate-950">
        <div className="mx-auto max-w-7xl px-6">
          <div className="grid items-center gap-12 lg:grid-cols-12">
            <div className="lg:col-span-7 flex flex-col">
              <span className="text-xs font-semibold uppercase tracking-widest text-blue-400 font-mono">Academic Research & Methodology</span>
              <h2 className="mt-3 text-3xl font-bold tracking-tight text-white md:text-4xl">
                Deterministic Heuristics with Experimental Graph Attention
              </h2>
              <p className="mt-4 text-slate-300 text-base leading-relaxed">
                AgileGraph was conceived as a final-year B.Tech Cyber Security project investigating whether graph representation learning can capture structural risk propagation across software dependencies during post-quantum migration.
              </p>

              <div className="mt-6 space-y-4 text-sm text-slate-400">
                <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
                  <h4 className="text-white font-semibold flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-blue-400" /> Canonical Heuristic Scoring Engine
                  </h4>
                  <p className="mt-1.5 text-xs text-slate-400 leading-relaxed">
                    Production evaluations rely strictly on the 7-factor composite heuristic scoring engine: Weakness (25%), Criticality (15%), Sensitivity (15%), Exposure (15%), Centrality (10%), Migration Difficulty (10%), and CVE Risk (10%). All factor weights sum to strictly 1.0.
                  </p>
                </div>

                <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
                  <h4 className="text-white font-semibold flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-purple-400" /> Experimental GATv2 Architecture
                  </h4>
                  <p className="mt-1.5 text-xs text-slate-400 leading-relaxed">
                    The HeteroGATv2 model (2 layers, 4 attention heads) was evaluated across 8 benchmark repositories (520 file assets) using Leave-One-Repository-Out (LOPO) cross-validation, achieving 66.73% accuracy and 0.5560 macro-F1 over static rule baselines (42.12%).
                  </p>
                </div>
              </div>

              {/* Explicit Research Disclosure */}
              <div className="mt-6 p-4 bg-amber-950/40 border border-amber-600/40 rounded-xl text-xs text-amber-200/90 leading-relaxed">
                <strong>Explicit Research Limitations:</strong> Weak-label distillation evaluated; expert-label validation blocked. The GATv2 neural model operates under weak supervision from discretized heuristic labels rather than confirmed real-world cryptographic exploitation incidents. AgileGraph guarantees that AST discoveries and heuristic risk vectors are never suppressed or discarded by machine learning predictions.
              </div>
            </div>

            {/* Benchmark Table Card */}
            <div className="lg:col-span-5">
              <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-6 shadow-xl">
                <h3 className="text-base font-bold text-white mb-1">LOPO Empirical Evaluation</h3>
                <p className="text-xs text-slate-400 mb-4">Leave-One-Repository-Out Cross-Validation (8 Repositories, 520 Files)</p>

                <div className="overflow-x-auto font-mono text-xs">
                  <table className="w-full text-left">
                    <thead>
                      <tr className="border-b border-slate-800 text-slate-400">
                        <th className="pb-2">Model / Baseline</th>
                        <th className="pb-2 text-right">Accuracy</th>
                        <th className="pb-2 text-right">Macro-F1</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 text-slate-300">
                      <tr>
                        <td className="py-2.5">Majority Baseline</td>
                        <td className="py-2.5 text-right text-slate-400">22.69%</td>
                        <td className="py-2.5 text-right text-slate-400">0.1233</td>
                      </tr>
                      <tr>
                        <td className="py-2.5">Static Rule Baseline</td>
                        <td className="py-2.5 text-right text-slate-400">42.12%</td>
                        <td className="py-2.5 text-right text-slate-400">0.4119</td>
                      </tr>
                      <tr className="text-blue-400 font-bold bg-blue-950/30">
                        <td className="py-2.5 pl-2 rounded-l">HeteroGATv2 (Proposed)</td>
                        <td className="py-2.5 text-right">66.73%</td>
                        <td className="py-2.5 text-right pr-2 rounded-r">0.5560</td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                <div className="mt-4 pt-4 border-t border-slate-800 text-[11px] text-slate-500 font-mono">
                  Runtime status: <span className="text-slate-300">ARCHITECTURAL_PROTOTYPE</span> · Zero AST suppression guaranteed.
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Technology Stack Section */}
      <section id="tech" className="py-24 border-b border-slate-900 bg-slate-900/30">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mx-auto max-w-2xl text-center">
            <span className="text-xs font-semibold uppercase tracking-widest text-blue-400 font-mono">Implementation</span>
            <h2 className="mt-3 text-3xl font-bold tracking-tight text-white md:text-4xl">
              Technology Stack
            </h2>
            <p className="mt-4 text-slate-400 text-sm">
              Constructed with modern high-performance libraries across graph analytics, machine learning, and frontend interaction.
            </p>
          </div>

          <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-4 font-mono text-xs">
            <div className="bg-slate-950 p-5 rounded-xl border border-slate-800">
              <div className="flex items-center gap-2 text-blue-400 font-bold text-sm mb-3">
                <Terminal className="w-4 h-4" /> Core Backend
              </div>
              <ul className="space-y-2 text-slate-400">
                <li>• Python 3.13</li>
                <li>• FastAPI 0.115+</li>
                <li>• Pydantic v2 (Strict Schema)</li>
                <li>• SQLite3 (ACID Persistence)</li>
              </ul>
            </div>

            <div className="bg-slate-950 p-5 rounded-xl border border-slate-800">
              <div className="flex items-center gap-2 text-indigo-400 font-bold text-sm mb-3">
                <Network className="w-4 h-4" /> Graph & ML
              </div>
              <ul className="space-y-2 text-slate-400">
                <li>• NetworkX MultiDiGraph</li>
                <li>• PyTorch Geometric (PyG)</li>
                <li>• HeteroGATv2 Architecture</li>
                <li>• Scikit-learn (LOPO Audit)</li>
              </ul>
            </div>

            <div className="bg-slate-950 p-5 rounded-xl border border-slate-800">
              <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm mb-3">
                <Code className="w-4 h-4" /> Static Scanners
              </div>
              <ul className="space-y-2 text-slate-400">
                <li>• Python AST Visitor</li>
                <li>• Java Javalang Parser</li>
                <li>• Go Mod Manifest Parser</li>
                <li>• X.509 Certificate Parser</li>
              </ul>
            </div>

            <div className="bg-slate-950 p-5 rounded-xl border border-slate-800">
              <div className="flex items-center gap-2 text-purple-400 font-bold text-sm mb-3">
                <Layers className="w-4 h-4" /> Dashboard UI
              </div>
              <ul className="space-y-2 text-slate-400">
                <li>• React 18 + TypeScript</li>
                <li>• Vite Build Pipeline</li>
                <li>• Tailwind CSS Design System</li>
                <li>• Force-directed Canvas 2D</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Call to Action Banner */}
      <section className="py-20 bg-slate-950">
        <div className="mx-auto max-w-7xl px-6">
          <div className="relative overflow-hidden rounded-3xl border border-blue-500/30 bg-gradient-to-r from-blue-950/80 via-slate-900 to-indigo-950/80 p-10 md:p-14 shadow-2xl">
            <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-8">
              <div>
                <h3 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
                  Ready to audit your repository for PQC readiness?
                </h3>
                <p className="mt-2 text-sm text-slate-300 max-w-xl">
                  Log in or create a user account to run AST scans, inspect multi-relational software graphs, and prioritize cryptographic migrations.
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-3 shrink-0">
                <Link
                  to={isAuthenticated ? "/app" : "/register"}
                  className="bg-blue-600 hover:bg-blue-500 text-white font-semibold px-6 py-3 rounded-xl text-sm transition-colors shadow-lg shadow-blue-600/30"
                >
                  {isAuthenticated ? "Go to Dashboard" : "Create Account"}
                </Link>
                {!isAuthenticated && (
                  <Link
                    to="/login"
                    className="bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 font-semibold px-6 py-3 rounded-xl text-sm transition-colors"
                  >
                    Sign In
                  </Link>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-12 text-xs text-slate-400">
        <div className="mx-auto max-w-7xl px-6 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="grid h-7 w-7 place-items-center rounded-lg bg-blue-600 text-white font-bold">
              <Shield className="w-4 h-4" />
            </div>
            <div>
              <span className="font-bold text-slate-200 font-mono">AgileGraph</span>
              <span className="text-slate-400 ml-2">Post-Quantum Cryptographic Migration Platform</span>
            </div>
          </div>

          <div className="flex items-center gap-6">
            <a href="https://csrc.nist.gov/projects/post-quantum-cryptography" target="_blank" rel="noreferrer" className="hover:text-blue-400 transition-colors flex items-center gap-1">
              <BookOpen className="w-3.5 h-3.5" /> NIST PQC Standard
            </a>
            <a href="https://github.com/spoorthi2615/Agilegraph" target="_blank" rel="noreferrer" className="hover:text-blue-400 transition-colors flex items-center gap-1">
              <Code className="w-3.5 h-3.5" /> GitHub Repository
            </a>
          </div>

          <div className="text-slate-400 font-mono">
            Final-Year B.Tech Cyber Security Project · 2026
          </div>
        </div>
      </footer>
    </div>
  );
}
