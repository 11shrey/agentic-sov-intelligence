import React, { useState } from 'react';
import { UploadCloud, FileText, CheckCircle2, AlertCircle, Play, Loader2 } from 'lucide-react';

export default function UploadSection({ onUploadSuccess, loading, setLoading, setError, error }) {
  const [dragActive, setDragActive] = useState(false);

  const handleFileUpload = async (file) => {
    if (!file) return;
    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
      setError("Invalid file format. Please upload an Excel workbook (.xlsx).");
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Analysis failed.");
      }

      const data = await res.json();
      onUploadSuccess(data, file.name);
    } catch (err) {
      setError(err.message || "Failed to analyze Excel file.");
    } finally {
      setLoading(false);
    }
  };

  const handleSampleDemo = async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch sample messy_sov file or call analyze endpoint directly
      const res = await fetch('/api/map', { method: 'POST' }); // triggers default sample load if needed or POST /analyze
      // Actually fetch sample file from backend sample directory if available or call analyze endpoint with Blob
      const blobRes = await fetch('/api/schema'); // Test backend connection
      
      // Send sample file upload simulation via POST /analyze
      const formData = new FormData();
      const sampleBlob = new Blob(["sample"], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      formData.append('file', new File([sampleBlob], 'messy_sov.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }));

      const analyzeRes = await fetch('/api/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!analyzeRes.ok) {
        throw new Error("Backend sample load error.");
      }

      const data = await analyzeRes.json();
      onUploadSuccess(data, 'messy_sov.xlsx (Demo Sample)');
    } catch (err) {
      setError("Sample demo trigger failed. Please upload a file manually.");
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="glass-card rounded-2xl p-6 sm:p-8 shadow-xl border border-slate-800">
      <div className="flex flex-col md:flex-row items-center justify-between gap-6 mb-6">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <UploadCloud className="w-5 h-5 text-teal-400" /> Upload Statement of Values (SOV)
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Upload client property schedules in Excel format (.xlsx). Agents 1-3 will analyze sheets, map schema, and detect quality issues.
          </p>
        </div>

        <button
          onClick={handleSampleDemo}
          disabled={loading}
          className="btn-secondary flex items-center gap-2 text-xs font-semibold whitespace-nowrap text-teal-300 border-teal-500/30 hover:bg-teal-500/10"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin text-teal-400" /> : <Play className="w-4 h-4 text-teal-400" />}
          Load Demo Sample (messy_sov.xlsx)
        </button>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center gap-3">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Drag & Drop Zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 ${
          dragActive ? 'border-teal-400 bg-teal-500/10' : 'border-slate-800 bg-slate-900/50 hover:border-slate-700'
        }`}
      >
        <input
          type="file"
          id="file-input"
          accept=".xlsx, .xls"
          onChange={(e) => e.target.files && handleFileUpload(e.target.files[0])}
          className="hidden"
        />
        <label htmlFor="file-input" className="cursor-pointer flex flex-col items-center">
          <div className="p-4 rounded-full bg-slate-800/80 mb-3 text-teal-400">
            {loading ? <Loader2 className="w-8 h-8 animate-spin" /> : <UploadCloud className="w-8 h-8" />}
          </div>
          <span className="text-sm font-semibold text-slate-200">
            {loading ? "Analyzing SOV Workbook with AI Agents..." : "Click to upload or drag & drop Excel workbook"}
          </span>
          <span className="text-xs text-slate-500 mt-1">Supported format: Microsoft Excel (.xlsx)</span>
        </label>
      </div>
    </div>
  );
}
