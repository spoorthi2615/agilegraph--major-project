// @ts-nocheck
import React from 'react';
import { Shield, LayoutDashboard, Database, AlertTriangle, GitPullRequest, Activity, List, Map, PieChart } from 'lucide-react';

export default function Reports() {
  return (
    <div className="flex flex-col gap-6 w-full">
      <h2 className="text-2xl font-semibold flex items-center gap-2">
        <PieChart className="text-blue-400 w-6 h-6" /> Reports
      </h2>
      <div className="bg-slate-800 rounded-xl p-6 shadow-lg border border-slate-700 h-64 flex items-center justify-center text-slate-500">
        Reports placeholder
      </div>
    </div>
  );
}
