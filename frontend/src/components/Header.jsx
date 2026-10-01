import React from 'react';
import { ShieldCheck, UserCheck, Sparkles, FileSpreadsheet } from 'lucide-react';

export default function Header({ reviewer, setReviewer }) {
  return (
    <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-gradient-to-br from-teal-500 to-emerald-600 rounded-xl shadow-lg shadow-teal-500/20">
              <FileSpreadsheet className="w-6 h-6 text-slate-950" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-xl font-bold tracking-tight text-white">Agentic SOV Intelligence</h1>
                <span className="bg-teal-500/10 text-teal-400 border border-teal-500/20 text-xs font-semibold px-2 py-0.5 rounded-md flex items-center gap-1">
                  <Sparkles className="w-3 h-3" /> PS3 Enterprise
                </span>
              </div>
              <p className="text-xs text-slate-400">Statement of Values Data Intelligence & Controlled Transformation</p>
            </div>
          </div>

          {/* Principle Banner */}
          <div className="hidden lg:flex items-center space-x-2 px-3 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-xs text-slate-300">
            <ShieldCheck className="w-4 h-4 text-teal-400" />
            <span><strong className="text-teal-400">AI recommends. Humans decide.</strong> Only approved changes are transformed.</span>
          </div>

          {/* Reviewer Identity */}
          <div className="flex items-center space-x-2 bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800">
            <UserCheck className="w-4 h-4 text-emerald-400" />
            <span className="text-xs font-medium text-slate-400">Approver:</span>
            <input
              type="text"
              value={reviewer}
              onChange={(e) => setReviewer(e.target.value)}
              className="bg-transparent text-xs font-semibold text-teal-300 focus:outline-none w-36 border-b border-slate-700 focus:border-teal-400"
              placeholder="Reviewer Name"
            />
          </div>
        </div>
      </div>
    </header>
  );
}
