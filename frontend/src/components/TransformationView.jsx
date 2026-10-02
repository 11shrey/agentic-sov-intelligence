import React, { useState } from 'react';
import { Cpu, Download, CheckCircle2, FileSpreadsheet, Loader2, Sparkles, ArrowDown } from 'lucide-react';

export default function TransformationView({ onTransformSuccess, transformResult, isTransforming }) {
  const [downloadingCleaned, setDownloadingCleaned] = useState(false);
  const [downloadingAudit, setDownloadingAudit] = useState(false);

  const handleDownload = (url, filename, setLoader) => {
    setLoader(true);
    const link = document.createElement('a');
    link.href = `/api${url}`;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    setTimeout(() => setLoader(false), 1000);
  };

  return (
    <div className="glass-card rounded-2xl p-6 shadow-xl border border-teal-500/30">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 border-b border-slate-800 pb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <Cpu className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white uppercase tracking-wider">Agent 4 — Controlled Transformation</h3>
            <p className="text-xs text-slate-400">Apply Approved Human Decisions & Deterministic Standardization</p>
          </div>
        </div>

        {!transformResult && (
          <button
            onClick={onTransformSuccess}
            disabled={isTransforming}
            className="btn-primary text-xs font-bold flex items-center gap-2 bg-gradient-to-r from-emerald-500 to-teal-600"
          >
            {isTransforming ? <Loader2 className="w-4 h-4 animate-spin text-slate-950" /> : <Sparkles className="w-4 h-4 text-slate-950" />}
            Run Controlled Transformation
          </button>
        )}
      </div>

      {transformResult && (
        <div>
          {/* Transformation Completed Banner */}
          <div className="p-5 rounded-2xl bg-gradient-to-r from-emerald-950/40 via-teal-950/30 to-slate-900 border border-emerald-500/40 mb-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-emerald-500 text-slate-950 rounded-xl font-bold shadow-lg shadow-emerald-500/20">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <div>
                <h4 className="text-base font-bold text-white flex items-center gap-2">
                  ✓ Controlled Transformation Completed
                </h4>
                <p className="text-xs text-emerald-300 mt-0.5">
                  Only approved changes transformed. Original workbook preserved separately.
                </p>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-3">
              <button
                onClick={() => handleDownload(transformResult.cleaned_sov_download_url, transformResult.cleaned_sov_filename, setDownloadingCleaned)}
                disabled={downloadingCleaned}
                className="btn-primary text-xs flex items-center gap-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold"
              >
                {downloadingCleaned ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                Download Cleaned SOV (.xlsx)
              </button>

              <button
                onClick={() => handleDownload(transformResult.audit_log_download_url, transformResult.audit_log_filename, setDownloadingAudit)}
                disabled={downloadingAudit}
                className="btn-secondary text-xs flex items-center gap-2 text-teal-300 border-teal-500/30 hover:bg-teal-500/10"
              >
                {downloadingAudit ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileSpreadsheet className="w-4 h-4 text-teal-400" />}
                Download Audit Log (.xlsx)
              </button>
            </div>
          </div>

          {/* Metrics Overview Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3 mb-6">
            <div className="bg-slate-900/80 p-3.5 rounded-xl border border-slate-800 text-center">
              <span className="text-[10px] font-bold text-slate-500 uppercase block">Records Processed</span>
              <span className="text-lg font-bold text-teal-300 mt-1 block">{transformResult.metrics.total_records}</span>
            </div>
            <div className="bg-slate-900/80 p-3.5 rounded-xl border border-slate-800 text-center">
              <span className="text-[10px] font-bold text-slate-500 uppercase block">Standard Fields</span>
              <span className="text-lg font-bold text-emerald-400 mt-1 block">17 Fields</span>
            </div>
            <div className="bg-slate-900/80 p-3.5 rounded-xl border border-slate-800 text-center">
              <span className="text-[10px] font-bold text-slate-500 uppercase block">Approved</span>
              <span className="text-lg font-bold text-emerald-400 mt-1 block">{transformResult.metrics.accepted}</span>
            </div>
            <div className="bg-slate-900/80 p-3.5 rounded-xl border border-slate-800 text-center">
              <span className="text-[10px] font-bold text-slate-500 uppercase block">Rejected</span>
              <span className="text-lg font-bold text-rose-400 mt-1 block">{transformResult.metrics.rejected}</span>
            </div>
            <div className="bg-slate-900/80 p-3.5 rounded-xl border border-slate-800 text-center">
              <span className="text-[10px] font-bold text-slate-500 uppercase block">Edited</span>
              <span className="text-lg font-bold text-amber-400 mt-1 block">{transformResult.metrics.edited}</span>
            </div>
            <div className="bg-slate-900/80 p-3.5 rounded-xl border border-slate-800 text-center">
              <span className="text-[10px] font-bold text-slate-500 uppercase block">Transformations</span>
              <span className="text-lg font-bold text-sky-400 mt-1 block">{transformResult.metrics.transformations_applied}</span>
            </div>
          </div>

          {/* Standardized 17-Field Cleaned SOV Data Preview */}
          {transformResult.preview_rows && transformResult.preview_rows.length > 0 && (
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                  <FileSpreadsheet className="w-4 h-4 text-teal-400" /> Standardized 17-Field Cleaned SOV Output Preview
                </span>
                <span className="text-[11px] text-slate-500">First 10 sample records shown</span>
              </div>

              <div className="overflow-x-auto rounded-xl border border-slate-800">
                <table className="w-full text-left border-collapse text-[11px]">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider bg-slate-900/80">
                      <th className="py-2.5 px-3 whitespace-nowrap">#</th>
                      {Object.keys(transformResult.preview_rows[0]).map((colKey, idx) => (
                        <th key={idx} className="py-2.5 px-3 whitespace-nowrap font-mono text-teal-300">{colKey}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                    {transformResult.preview_rows.map((row, rowIdx) => (
                      <tr key={rowIdx} className="hover:bg-slate-900/40">
                        <td className="py-2.5 px-3 text-slate-500 font-bold">{rowIdx + 1}</td>
                        {Object.values(row).map((val, cellIdx) => (
                          <td key={cellIdx} className="py-2.5 px-3 whitespace-nowrap">
                            {val !== null && val !== undefined ? String(val) : <span className="text-slate-600 italic">null</span>}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
