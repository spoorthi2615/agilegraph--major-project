// @ts-nocheck
import type { ReactNode } from 'react';
import { NavLink } from 'react-router-dom';
import { Shield, Home, Search, Activity, Map, List, Database, AlertTriangle, Network, PieChart } from 'lucide-react';

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-background text-foreground flex font-sans">
      <aside className="w-64 bg-card border-r border-border flex flex-col">
        <div className="p-4 border-b border-border flex items-center gap-2">
          <div className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-primary to-blue-500 text-white shadow-glow">
            <Shield className="w-4.5 h-4.5" />
          </div>
          <h1 className="text-xl font-bold tracking-tight text-foreground">AgileGraph</h1>
        </div>
        <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
          <NavLink to="/" className={({isActive}: {isActive: boolean}) => `flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:bg-muted hover:text-foreground'}`}><Home className="w-4 h-4"/> Overview</NavLink>
          <NavLink to="/inventory" className={({isActive}: {isActive: boolean}) => `flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:bg-muted hover:text-foreground'}`}><Database className="w-4 h-4"/> Crypto Inventory</NavLink>
          <NavLink to="/risk" className={({isActive}: {isActive: boolean}) => `flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:bg-muted hover:text-foreground'}`}><AlertTriangle className="w-4 h-4"/> Risk Analysis</NavLink>
          <NavLink to="/pqc-readiness" className={({isActive}: {isActive: boolean}) => `flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:bg-muted hover:text-foreground'}`}><Activity className="w-4 h-4"/> PQC Readiness</NavLink>
          <NavLink to="/mosca" className={({isActive}: {isActive: boolean}) => `flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:bg-muted hover:text-foreground'}`}><Search className="w-4 h-4"/> Mosca Readiness</NavLink>
          <NavLink to="/priority" className={({isActive}: {isActive: boolean}) => `flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:bg-muted hover:text-foreground'}`}><List className="w-4 h-4"/> Migration Priority</NavLink>
          <NavLink to="/roadmap" className={({isActive}: {isActive: boolean}) => `flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:bg-muted hover:text-foreground'}`}><Map className="w-4 h-4"/> Migration Roadmap</NavLink>
          <NavLink to="/graph" className={({isActive}: {isActive: boolean}) => `flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:bg-muted hover:text-foreground'}`}><Network className="w-4 h-4"/> Crypto Graph</NavLink>
          <NavLink to="/reports" className={({isActive}: {isActive: boolean}) => `flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:bg-muted hover:text-foreground'}`}><PieChart className="w-4 h-4"/> Reports</NavLink>
        </nav>
      </aside>
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="bg-background/70 backdrop-blur-xl border-b border-border p-4 sticky top-0 z-40 flex items-center justify-end">
          <div className="flex items-center gap-4 text-xs font-mono text-muted-foreground bg-card px-3 py-1.5 rounded-full border border-border shadow-sm">
            <span>GATv2: <span className="text-muted-foreground font-semibold">ARCHITECTURAL_PROTOTYPE</span></span>
            <span className="text-border">|</span>
            <span>Evaluation: <span className="text-emerald-500 font-semibold">DETERMINISTIC_HEURISTIC</span></span>
          </div>
        </header>
        <main className="flex-1 p-6 md:p-8 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
