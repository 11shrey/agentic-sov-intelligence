import React from 'react';
import { Layers, CheckCircle, FileText, Info, HelpCircle } from 'lucide-react';

export default function SheetIntelligenceView({ result }) {
  if (!result) return null;

  const { selected_sheet, header_row, confidence, reasoning, sheets, all_sheets } = result;
  const sheetList = sheets || all_sheets || [];

  return (
    <div className="glass-card rounded-2xl p-6 shadow-xl border border-slate-800">
      <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-teal-500/10 text-teal-400 border border-teal-500/20">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Agent 1 — Sheet Intelligence</h3>
            <p className="text-xs text-slate-400">Automated SOV Sheet Identification & Header Detection</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-medium">Confidence:</span>
          <span className="bg-teal-500/20 text-teal-300 font-bold text-xs px-2.5 py-1 rounded-full border border-teal-500/30">
            {Math.round(confidence * 100)}%
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-800">
          <span className="text-xs text-slate-500 block uppercase font-medium">Selected SOV Sheet</span>
          <span className="text-base font-bold text-teal-300 mt-1 flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-400" /> {selected_sheet}
          </span>
        </div>

        <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-800">
          <span className="text-xs text-slate-500 block uppercase font-medium">Header Row Detected</span>
          <span className="text-base font-bold text-slate-200 mt-1">
            Row {header_row}
          </span>
        </div>

        <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-800">
          <span className="text-xs text-slate-500 block uppercase font-medium">Total Workbook Sheets</span>
          <span className="text-base font-bold text-slate-200 mt-1">
            {sheetList.length} Sheets Inspected
          </span>
        </div>
      </div>

      {/* Reasoning Box */}
      <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800/80 text-xs text-slate-300 flex items-start gap-3">
        <Info className="w-4 h-4 text-sky-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-sky-300 block mb-0.5">Agent 1 Reasoning Rationale:</span>
          <p>{reasoning}</p>
        </div>
      </div>

      {/* Sheets Table Overview */}
      {sheetList.length > 0 && (
        <div className="mt-6">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-3">Inspected Workbook Sheets</span>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {sheetList.map((s, idx) => (
              <div
                key={idx}
                className={`p-3 rounded-lg border text-xs flex items-center justify-between ${
                  s.sheet_name === selected_sheet
                    ? 'border-teal-500/50 bg-teal-950/20 text-teal-200'
                    : 'border-slate-800 bg-slate-900/40 text-slate-400'
                }`}
              >
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-slate-500" />
                  <span className="font-semibold">{s.sheet_name}</span>
                </div>
                <span className="text-slate-500">{s.row_count} rows × {s.column_count} cols</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
