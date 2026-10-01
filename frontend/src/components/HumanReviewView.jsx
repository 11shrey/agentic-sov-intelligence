import React, { useState } from 'react';
import { UserCheck, Check, X, Edit3, Save, Sparkles, CheckCircle2 } from 'lucide-react';

export default function HumanReviewView({ mappings, onSubmitDecisions, isSubmitted }) {
  const [decisions, setDecisions] = useState({});
  const [editingField, setEditingField] = useState(null);
  const [editInputValue, setEditInputValue] = useState('');

  if (!mappings || mappings.length === 0) return null;

  const handleDecision = (recId, decisionType, editedVal = null) => {
    setDecisions((prev) => ({
      ...prev,
      [recId]: {
        recommendation_id: recId,
        decision: decisionType,
        edited_value: editedVal,
      }
    }));
  };

  const handleOpenEdit = (recId, currentVal) => {
    setEditingField(recId);
    setEditInputValue(currentVal || '');
  };

  const handleSaveEdit = (recId) => {
    if (!editInputValue.trim()) return;
    handleDecision(recId, 'edit', editInputValue.trim());
    setEditingField(null);
    setEditInputValue('');
  };

  const handleAcceptAllHighConfidence = () => {
    const newDecs = { ...decisions };
    mappings.forEach((m) => {
      if (!newDecs[m.source_column]) {
        newDecs[m.source_column] = {
          recommendation_id: m.source_column,
          decision: 'accept',
          edited_value: null,
        };
      }
    });
    setDecisions(newDecs);
  };

  const handleSubmit = () => {
    const decisionList = Object.values(decisions);
    onSubmitDecisions(decisionList);
  };

  return (
    <div className="glass-card rounded-2xl p-6 shadow-xl border border-teal-500/30">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 border-b border-slate-800 pb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-teal-500/10 text-teal-400 border border-teal-500/20">
            <UserCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-white uppercase tracking-wider">Human Review & Decision Center</h3>
              <span className="bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs font-semibold px-2.5 py-0.5 rounded-full">
                Human-in-the-Loop
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Review AI recommendations. Every change must be explicitly approved, rejected, or edited before transformation.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleAcceptAllHighConfidence}
            className="btn-secondary text-xs"
          >
            Accept Remaining Default
          </button>
          <button
            onClick={handleSubmit}
            className="btn-primary text-xs flex items-center gap-1.5"
          >
            <CheckCircle2 className="w-4 h-4" /> Save & Submit Review Decisions
          </button>
        </div>
      </div>

      {isSubmitted && (
        <div className="mb-6 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs flex items-center gap-3">
          <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
          <div>
            <span className="font-bold">Human Review Decisions Saved & Validated!</span>
            <p className="text-slate-400 mt-0.5">Decisions locked into pipeline state. Ready for Agent 4 Controlled Transformation.</p>
          </div>
        </div>
      )}

      {/* Recommendations Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {mappings.map((m, idx) => {
          const recId = m.source_column;
          const currentDec = decisions[recId];
          const decisionStatus = currentDec ? currentDec.decision : 'pending';

          return (
            <div
              key={idx}
              className={`p-4 rounded-xl border transition-all ${
                decisionStatus === 'accept'
                  ? 'bg-emerald-950/20 border-emerald-500/40'
                  : decisionStatus === 'reject'
                  ? 'bg-rose-950/20 border-rose-500/40'
                  : decisionStatus === 'edit'
                  ? 'bg-amber-950/20 border-amber-500/40'
                  : 'bg-slate-900/60 border-slate-800'
              }`}
            >
              <div className="flex items-start justify-between gap-3 mb-2">
                <div>
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Source Column</span>
                  <span className="text-sm font-bold text-amber-300 font-mono">{m.source_column}</span>
                </div>
                <div className="text-right">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Target 17 Field</span>
                  <span className="text-sm font-bold text-teal-300 font-mono">{m.target_field}</span>
                </div>
              </div>

              <div className="text-xs text-slate-400 mb-3 bg-slate-950/40 p-2.5 rounded-lg border border-slate-800/80">
                <span className="text-slate-300 font-medium block mb-1">AI Rationale:</span>
                {m.reasoning}
              </div>

              {/* Edit Input Modal / Inline Field */}
              {editingField === recId && (
                <div className="mb-3 p-3 bg-slate-950 rounded-lg border border-amber-500/40 flex items-center gap-2">
                  <input
                    type="text"
                    value={editInputValue}
                    onChange={(e) => setEditInputValue(e.target.value)}
                    placeholder="Enter custom target value..."
                    className="bg-slate-900 border border-slate-700 text-xs text-white px-2.5 py-1.5 rounded w-full focus:outline-none focus:border-amber-400"
                  />
                  <button
                    onClick={() => handleSaveEdit(recId)}
                    className="btn-primary py-1.5 text-xs flex items-center gap-1 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold"
                  >
                    <Save className="w-3.5 h-3.5" /> Save
                  </button>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex items-center justify-between pt-2 border-t border-slate-800/60">
                <div className="flex items-center gap-1.5">
                  <button
                    onClick={() => handleDecision(recId, 'accept')}
                    className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1 transition-colors ${
                      decisionStatus === 'accept'
                        ? 'bg-emerald-500 text-slate-950 shadow-md shadow-emerald-500/20'
                        : 'bg-slate-800 text-slate-300 hover:bg-emerald-500/20 hover:text-emerald-300'
                    }`}
                  >
                    <Check className="w-3.5 h-3.5" /> Accept
                  </button>

                  <button
                    onClick={() => handleDecision(recId, 'reject')}
                    className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1 transition-colors ${
                      decisionStatus === 'reject'
                        ? 'bg-rose-500 text-slate-950 shadow-md shadow-rose-500/20'
                        : 'bg-slate-800 text-slate-300 hover:bg-rose-500/20 hover:text-rose-300'
                    }`}
                  >
                    <X className="w-3.5 h-3.5" /> Reject
                  </button>

                  <button
                    onClick={() => handleOpenEdit(recId, m.target_field)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1 transition-colors ${
                      decisionStatus === 'edit'
                        ? 'bg-amber-500 text-slate-950 shadow-md shadow-amber-500/20'
                        : 'bg-slate-800 text-slate-300 hover:bg-amber-500/20 hover:text-amber-300'
                    }`}
                  >
                    <Edit3 className="w-3.5 h-3.5" /> Edit
                  </button>
                </div>

                {/* Status Indicator */}
                <span className={`text-[11px] font-bold px-2 py-0.5 rounded ${
                  decisionStatus === 'accept' ? 'text-emerald-400 bg-emerald-500/10 border border-emerald-500/20' :
                  decisionStatus === 'reject' ? 'text-rose-400 bg-rose-500/10 border border-rose-500/20' :
                  decisionStatus === 'edit' ? 'text-amber-400 bg-amber-500/10 border border-amber-500/20' :
                  'text-slate-500 bg-slate-800'
                }`}>
                  {decisionStatus.toUpperCase()}
                  {decisionStatus === 'edit' && currentDec.edited_value ? `: ${currentDec.edited_value}` : ''}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
