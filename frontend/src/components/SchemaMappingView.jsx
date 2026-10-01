import React from 'react';
import { GitMerge, CheckCircle, AlertTriangle, ArrowRight } from 'lucide-react';

export default function SchemaMappingView({ mappings }) {
  if (!mappings || mappings.length === 0) return null;

  return (
    <div className="glass-card rounded-2xl p-6 shadow-xl border border-slate-800">
      <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-sky-500/10 text-sky-400 border border-sky-500/20">
            <GitMerge className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Agent 2 — Schema Mapping</h3>
            <p className="text-xs text-slate-400">Map Client Columns to Standard 17 SOV Schema</p>
          </div>
        </div>
        <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
          {mappings.length} Columns Mapped
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-800 text-xs text-slate-400 uppercase tracking-wider bg-slate-900/50">
              <th className="py-3 px-4">Client Source Column</th>
              <th className="py-3 px-4">Standardized 17 Field</th>
              <th className="py-3 px-4">Method</th>
              <th className="py-3 px-4">Confidence</th>
              <th className="py-3 px-4">AI Rationale</th>
              <th className="py-3 px-4">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-xs text-slate-200 font-mono">
            {mappings.map((m, idx) => (
              <tr key={idx} className="hover:bg-slate-900/40 transition-colors">
                <td className="py-3 px-4 font-semibold text-amber-300">{m.source_column}</td>
                <td className="py-3 px-4 font-semibold text-teal-300 flex items-center gap-1.5">
                  <ArrowRight className="w-3 h-3 text-slate-500" />
                  {m.target_field}
                </td>
                <td className="py-3 px-4">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                    m.matching_method === 'exact' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
                    m.matching_method === 'alias' ? 'bg-teal-500/20 text-teal-300 border border-teal-500/30' :
                    m.matching_method === 'fuzzy' ? 'bg-sky-500/20 text-sky-300 border border-sky-500/30' :
                    'bg-slate-800 text-slate-400'
                  }`}>
                    {m.matching_method}
                  </span>
                </td>
                <td className="py-3 px-4">
                  <div className="flex items-center gap-2">
                    <div className="w-16 bg-slate-800 h-1.5 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          m.confidence >= 0.85 ? 'bg-teal-400' : 'bg-amber-400'
                        }`}
                        style={{ width: `${m.confidence * 100}%` }}
                      ></div>
                    </div>
                    <span className="font-semibold text-slate-300">{Math.round(m.confidence * 100)}%</span>
                  </div>
                </td>
                <td className="py-3 px-4 font-sans text-slate-400 max-w-xs truncate" title={m.reasoning}>
                  {m.reasoning}
                </td>
                <td className="py-3 px-4">
                  {m.status === 'approved' ? (
                    <span className="badge-success flex items-center gap-1 w-fit">
                      <CheckCircle className="w-3 h-3" /> Approved
                    </span>
                  ) : (
                    <span className="badge-warning flex items-center gap-1 w-fit">
                      <AlertTriangle className="w-3 h-3" /> Needs Review
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
