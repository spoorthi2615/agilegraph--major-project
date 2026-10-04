// @ts-nocheck
import type { ReactNode } from 'react';
import { NavLink } from 'react-router-dom';
import { Shield, Home, Search, Activity, Map, List, Database, AlertTriangle, Network, PieChart } from 'lucide-react';

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex font-sans">
      <aside className="w-64 bg-slate-800 border-r border-slate-700 flex flex-col">
        <div className="p-4 border-b border-slate-700 flex items-center gap-2">
          <Shield className="text-emerald-400 w-8 h-8" />
          <h1 className="text-xl font-bold tracking-tight text-white">AgileGraph</h1>
        </div>
        <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
          <NavLink to="/" className={({isActive}: {isActive: boolean}) => `flex items-center gap-2 p-2 rounded-md ${isActive ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-700'}`}><Home className="w-5 h-5"/> Overview</NavLink>
          <NavLink to="/inventory" className={({isActive}: {isActive: boolean}) => `flex items-center gap-2 p-2 rounded-md ${isActive ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-700'}`}><Database className="w-5 h-5"/> Crypto Inventory</NavLink>
          <NavLink to="/risk" className={({isActive}: {isActive: boolean}) => `flex items-center gap-2 p-2 rounded-md ${isActive ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-700'}`}><AlertTriangle className="w-5 h-5"/> Risk Analysis</NavLink>
          <NavLink to="/pqc-readiness" className={({isActive}: {isActive: boolean}) => `flex items-center gap-2 p-2 rounded-md ${isActive ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-700'}`}><Activity className="w-5 h-5"/> PQC Readiness</NavLink>
          <NavLink to="/mosca" className={({isActive}: {isActive: boolean}) => `flex items-center gap-2 p-2 rounded-md ${isActive ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-700'}`}><Search className="w-5 h-5"/> Mosca Readiness</NavLink>
          <NavLink to="/priority" className={({isActive}: {isActive: boolean}) => `flex items-center gap-2 p-2 rounded-md ${isActive ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-700'}`}><List className="w-5 h-5"/> Migration Priority</NavLink>
          <NavLink to="/roadmap" className={({isActive}: {isActive: boolean}) => `flex items-center gap-2 p-2 rounded-md ${isActive ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-700'}`}><Map className="w-5 h-5"/> Migration Roadmap</NavLink>
          <NavLink to="/graph" className={({isActive}: {isActive: boolean}) => `flex items-center gap-2 p-2 rounded-md ${isActive ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-700'}`}><Network className="w-5 h-5"/> Crypto Graph</NavLink>
          <NavLink to="/reports" className={({isActive}: {isActive: boolean}) => `flex items-center gap-2 p-2 rounded-md ${isActive ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-700'}`}><PieChart className="w-5 h-5"/> Reports</NavLink>
        </nav>
      </aside>
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="bg-slate-800 border-b border-slate-700 p-4 shadow-md flex items-center justify-end">
          <div className="flex items-center gap-4 text-sm font-mono text-slate-400 bg-slate-900 px-3 py-1 rounded-md border border-slate-700">
            <span>GATv2: <span className="text-amber-400">BLOCKED</span></span>
            <span className="text-slate-600">|</span>
            <span>Expert Validation: <span className="text-amber-400">PENDING_EXPERT_LABELS</span></span>
          </div>
        </header>
        <main className="flex-1 p-6 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
