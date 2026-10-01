import React, { useState } from 'react';
import { AlertCircle, AlertTriangle, Info, CheckCircle2, ShieldAlert } from 'lucide-react';

export default function DataQualityView({ issues }) {
  const [filterSeverity, setFilterSeverity] = useState('ALL');

  if (!issues || issues.length === 0) {
    return (
      <div className="glass-card rounded-2xl p-6 shadow-xl border border-slate-800 text-center">
        <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
        <h3 className="text-sm font-bold text-white">Agent 3 — No Data Quality Issues Detected</h3>
        <p className="text-xs text-slate-400 mt-1">All mapped property values passed initial validation checks.</p>
      </div>
    );
  }

  const filteredIssues = filterSeverity === 'ALL'
    ? issues
    : issues.filter(i => i.severity.toUpperCase() === filterSeverity);

  return (
    <div className="glass-card rounded-2xl p-6 shadow-xl border border-slate-800">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4 border-b border-slate-800 pb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Agent 3 — Data Quality & Reasoning</h3>
            <p className="text-xs text-slate-400">Automated Data Quality & Anomaly Detection (Read-Only Advice)</p>
          </div>
        </div>

        {/* Severity Filter */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-medium">Filter Severity:</span>
          {['ALL', 'HIGH', 'MEDIUM', 'LOW'].map((sev) => (
            <button
              key={sev}
              onClick={() => setFilterSeverity(sev)}
              className={`px-2.5 py-1 rounded-md text-xs font-semibold transition-colors ${
                filterSeverity === sev
                  ? 'bg-amber-500 text-slate-950 font-bold'
                  : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
              }`}
            >
              {sev}
            </button>
          ))}
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-800 text-xs text-slate-400 uppercase tracking-wider bg-slate-900/50">
              <th className="py-3 px-4">Row</th>
              <th className="py-3 px-4">Field</th>
              <th className="py-3 px-4">Detected Value</th>
              <th className="py-3 px-4">Issue Type</th>
              <th className="py-3 px-4">Severity</th>
              <th className="py-3 px-4">AI Reasoning & Advice</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-xs text-slate-200">
            {filteredIssues.map((issue, idx) => (
              <tr key={idx} className="hover:bg-slate-900/40 transition-colors">
                <td className="py-3 px-4 font-mono font-bold text-slate-400">Row {issue.row}</td>
                <td className="py-3 px-4 font-semibold text-teal-300">{issue.field}</td>
                <td className="py-3 px-4 font-mono text-amber-300 bg-slate-950/50 px-2 py-1 rounded w-fit">
                  {issue.value !== null && issue.value !== undefined ? String(issue.value) : '<empty>'}
                </td>
                <td className="py-3 px-4 font-mono text-xs text-slate-300">{issue.issue_type}</td>
                <td className="py-3 px-4">
                  {issue.severity.toLowerCase() === 'high' ? (
                    <span className="badge-danger flex items-center gap-1 w-fit">
                      <AlertCircle className="w-3 h-3" /> HIGH
                    </span>
                  ) : issue.severity.toLowerCase() === 'medium' ? (
                    <span className="badge-warning flex items-center gap-1 w-fit">
                      <AlertTriangle className="w-3 h-3" /> MEDIUM
                    </span>
                  ) : (
                    <span className="badge-info flex items-center gap-1 w-fit">
                      <Info className="w-3 h-3" /> LOW
                    </span>
                  )}
                </td>
                <td className="py-3 px-4 max-w-sm">
                  <p className="text-slate-300 font-medium">{issue.reasoning}</p>
                  <p className="text-slate-500 text-[11px] mt-0.5">💡 {issue.recommendation}</p>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
