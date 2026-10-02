import React from 'react';
import { BarChart3, ShieldCheck, AlertOctagon, CheckCircle2, RefreshCw, FileCheck } from 'lucide-react';

export default function DashboardAnalytics({ pipelineData, transformMetrics }) {
  if (!pipelineData) return null;

  const mappings = pipelineData.mappings || [];
  const qualityIssues = pipelineData.quality_issues || [];
  const sheetInfo = pipelineData.sheet_analysis || {};

  const totalSrcCols = mappings.length;
  const mappedCols = mappings.filter(m => m.target_field !== 'Other').length;
  const highSevIssues = qualityIssues.filter(q => q.severity?.toLowerCase() === 'high').length;

  const accepted = transformMetrics ? transformMetrics.accepted : 0;
  const rejected = transformMetrics ? transformMetrics.rejected : 0;
  const edited = transformMetrics ? transformMetrics.edited : 0;
  const transformations = transformMetrics ? transformMetrics.transformations_applied : 0;

  return (
    <div className="glass-card rounded-2xl p-6 shadow-xl border border-slate-800">
      <div className="flex items-center justify-between mb-6 border-b border-slate-800 pb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <BarChart3 className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Executive Dashboard & Analytics</h3>
            <p className="text-xs text-slate-400">System Performance Metrics & Human-in-the-Loop Audit Summary</p>
          </div>
        </div>

        <span className="badge-info flex items-center gap-1">
          <ShieldCheck className="w-3.5 h-3.5" /> System Status: Operational
        </span>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
        <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-800">
          <span className="text-xs text-slate-500 block uppercase font-medium">SOV Sheet</span>
          <span className="text-sm font-bold text-teal-300 mt-1 truncate block">{sheetInfo.selected_sheet || 'N/A'}</span>
          <span className="text-[10px] text-slate-500 mt-0.5 block">Header Row {sheetInfo.header_row || '-'}</span>
        </div>

        <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-800">
          <span className="text-xs text-slate-500 block uppercase font-medium">Mapped Fields</span>
          <span className="text-lg font-bold text-emerald-400 mt-1 block">{mappedCols} / {totalSrcCols}</span>
          <span className="text-[10px] text-emerald-500/80 mt-0.5 block">{totalSrcCols ? Math.round((mappedCols / totalSrcCols) * 100) : 0}% Schema Match</span>
        </div>

        <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-800">
          <span className="text-xs text-slate-500 block uppercase font-medium">Quality Issues</span>
          <span className="text-lg font-bold text-amber-400 mt-1 block">{qualityIssues.length}</span>
          <span className="text-[10px] text-amber-500/80 mt-0.5 block">{highSevIssues} High Severity</span>
        </div>

        <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-800">
          <span className="text-xs text-slate-500 block uppercase font-medium">Approved Changes</span>
          <span className="text-lg font-bold text-emerald-400 mt-1 block">{accepted}</span>
          <span className="text-[10px] text-slate-500 mt-0.5 block">Human Accepted</span>
        </div>

        <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-800">
          <span className="text-xs text-slate-500 block uppercase font-medium">Rejected</span>
          <span className="text-lg font-bold text-rose-400 mt-1 block">{rejected}</span>
          <span className="text-[10px] text-slate-500 mt-0.5 block">Blanked Out</span>
        </div>

        <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-800">
          <span className="text-xs text-slate-500 block uppercase font-medium">Edited</span>
          <span className="text-lg font-bold text-amber-400 mt-1 block">{edited}</span>
          <span className="text-[10px] text-slate-500 mt-0.5 block">Custom Overrides</span>
        </div>
      </div>

      {/* Decision Distribution Bar */}
      {transformMetrics && (
        <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
          <div className="flex items-center justify-between text-xs text-slate-300 mb-2 font-medium">
            <span>Human Approval Decisions Breakdown</span>
            <span>{transformations} Total Transformations Applied</span>
          </div>
          <div className="w-full bg-slate-800 h-3 rounded-full overflow-hidden flex">
            <div
              className="bg-emerald-500 h-full transition-all"
              style={{ width: `${(accepted / (accepted + rejected + edited || 1)) * 100}%` }}
              title={`Accepted: ${accepted}`}
            ></div>
            <div
              className="bg-amber-500 h-full transition-all"
              style={{ width: `${(edited / (accepted + rejected + edited || 1)) * 100}%` }}
              title={`Edited: ${edited}`}
            ></div>
            <div
              className="bg-rose-500 h-full transition-all"
              style={{ width: `${(rejected / (accepted + rejected + edited || 1)) * 100}%` }}
              title={`Rejected: ${rejected}`}
            ></div>
          </div>
        </div>
      )}
    </div>
  );
}
