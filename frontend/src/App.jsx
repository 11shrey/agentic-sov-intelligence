import React, { useState } from 'react';
import Header from './components/Header.jsx';
import UploadSection from './components/UploadSection.jsx';
import SheetIntelligenceView from './components/SheetIntelligenceView.jsx';
import SchemaMappingView from './components/SchemaMappingView.jsx';
import DataQualityView from './components/DataQualityView.jsx';
import HumanReviewView from './components/HumanReviewView.jsx';
import TransformationView from './components/TransformationView.jsx';
import DashboardAnalytics from './components/DashboardAnalytics.jsx';
import { Layers, GitMerge, ShieldAlert, UserCheck, Cpu, BarChart3, CheckCircle, RefreshCw } from 'lucide-react';

export default function App() {
  const [reviewer, setReviewer] = useState('Senior Underwriter');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [pipelineData, setPipelineData] = useState(null);
  const [fileName, setFileName] = useState('');
  const [reviewSubmitted, setReviewSubmitted] = useState(false);
  const [transformResult, setTransformResult] = useState(null);
  const [isTransforming, setIsTransforming] = useState(false);
  const [activeTab, setActiveTab] = useState('review'); // 'review' | 'analysis' | 'quality' | 'transform' | 'dashboard'

  const handleUploadSuccess = (data, uploadedFileName) => {
    setPipelineData(data);
    setFileName(uploadedFileName);
    setReviewSubmitted(false);
    setTransformResult(null);
    setActiveTab('review');
  };

  const handleSubmitReviewDecisions = async (decisionList) => {
    setError(null);
    try {
      const res = await fetch('/api/review', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: 'default',
          approver: reviewer,
          decisions: decisionList,
        }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to submit review decisions.');
      }

      setReviewSubmitted(true);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleRunTransformation = async () => {
    setIsTransforming(true);
    setError(null);

    try {
      const res = await fetch('/api/transform', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: 'default' }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Transformation failed.');
      }

      const data = await res.json();
      setTransformResult(data);
      setActiveTab('transform');
    } catch (err) {
      setError(err.message || 'Transformation failed.');
    } finally {
      setIsTransforming(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Header reviewer={reviewer} setReviewer={setReviewer} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Upload Section */}
        <UploadSection
          onUploadSuccess={handleUploadSuccess}
          loading={loading}
          setLoading={setLoading}
          setError={setError}
          error={error}
        />

        {pipelineData && (
          <div className="space-y-6">
            {/* Step Navigation Bar */}
            <div className="flex items-center justify-between glass-card p-2 rounded-xl border border-slate-800 overflow-x-auto">
              <div className="flex items-center space-x-1 sm:space-x-2">
                <button
                  onClick={() => setActiveTab('review')}
                  className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all ${
                    activeTab === 'review'
                      ? 'bg-teal-500 text-slate-950 shadow-md shadow-teal-500/20 font-bold'
                      : 'text-slate-400 hover:text-white hover:bg-slate-900'
                  }`}
                >
                  <UserCheck className="w-4 h-4" /> Human Review
                </button>

                <button
                  onClick={() => setActiveTab('analysis')}
                  className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all ${
                    activeTab === 'analysis'
                      ? 'bg-teal-500 text-slate-950 shadow-md shadow-teal-500/20 font-bold'
                      : 'text-slate-400 hover:text-white hover:bg-slate-900'
                  }`}
                >
                  <Layers className="w-4 h-4" /> Agent 1 Sheet Info
                </button>

                <button
                  onClick={() => setActiveTab('mapping')}
                  className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all ${
                    activeTab === 'mapping'
                      ? 'bg-teal-500 text-slate-950 shadow-md shadow-teal-500/20 font-bold'
                      : 'text-slate-400 hover:text-white hover:bg-slate-900'
                  }`}
                >
                  <GitMerge className="w-4 h-4" /> Agent 2 Mappings
                </button>

                <button
                  onClick={() => setActiveTab('quality')}
                  className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all ${
                    activeTab === 'quality'
                      ? 'bg-teal-500 text-slate-950 shadow-md shadow-teal-500/20 font-bold'
                      : 'text-slate-400 hover:text-white hover:bg-slate-900'
                  }`}
                >
                  <ShieldAlert className="w-4 h-4" /> Agent 3 Quality ({pipelineData.quality_issues?.length || 0})
                </button>

                <button
                  onClick={() => setActiveTab('transform')}
                  className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all ${
                    activeTab === 'transform'
                      ? 'bg-teal-500 text-slate-950 shadow-md shadow-teal-500/20 font-bold'
                      : 'text-slate-400 hover:text-white hover:bg-slate-900'
                  }`}
                >
                  <Cpu className="w-4 h-4" /> Agent 4 Transformation
                </button>

                <button
                  onClick={() => setActiveTab('dashboard')}
                  className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all ${
                    activeTab === 'dashboard'
                      ? 'bg-teal-500 text-slate-950 shadow-md shadow-teal-500/20 font-bold'
                      : 'text-slate-400 hover:text-white hover:bg-slate-900'
                  }`}
                >
                  <BarChart3 className="w-4 h-4" /> Dashboard
                </button>
              </div>

              <span className="text-xs font-mono text-teal-400 px-3 py-1 rounded bg-slate-900 border border-slate-800 hidden md:inline-block">
                File: {fileName}
              </span>
            </div>

            {/* Active Tab Content Views */}
            {activeTab === 'review' && (
              <HumanReviewView
                mappings={pipelineData.mappings}
                onSubmitDecisions={handleSubmitReviewDecisions}
                isSubmitted={reviewSubmitted}
              />
            )}

            {activeTab === 'analysis' && (
              <SheetIntelligenceView result={pipelineData.sheet_analysis} />
            )}

            {activeTab === 'mapping' && (
              <SchemaMappingView mappings={pipelineData.mappings} />
            )}

            {activeTab === 'quality' && (
              <DataQualityView issues={pipelineData.quality_issues} />
            )}

            {activeTab === 'transform' && (
              <TransformationView
                onTransformSuccess={handleRunTransformation}
                transformResult={transformResult}
                isTransforming={isTransforming}
              />
            )}

            {activeTab === 'dashboard' && (
              <DashboardAnalytics
                pipelineData={pipelineData}
                transformMetrics={transformResult?.metrics}
              />
            )}
          </div>
        )}
      </main>

      <footer className="border-t border-slate-900 bg-slate-950 py-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>Agentic SOV Intelligence System &copy; 2026 — Insurance PS3 Demo</span>
          <span>Core Principle: AI recommends. Humans decide. Only approved changes are transformed.</span>
        </div>
      </footer>
    </div>
  );
}
