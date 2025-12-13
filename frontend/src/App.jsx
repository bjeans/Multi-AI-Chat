import { useState } from 'react';
import { useLLMModels } from './hooks/useLLMModels';
import { useStreamingDebate } from './hooks/useStreamingDebate';
import QueryInput from './components/QueryInput';
import CouncilMemberCard from './components/CouncilMemberCard';
import SynthesisPanel from './components/SynthesisPanel';
import HistoryBrowser from './components/HistoryBrowser';

export default function App() {
  const { models, loading: modelsLoading } = useLLMModels();
  const {
    debating,
    decisionId,
    modelResponses,
    synthesis,
    error,
    startDebate,
  } = useStreamingDebate();

  const [showHistory, setShowHistory] = useState(false);
  const [selectedChairman, setSelectedChairman] = useState('');
  const [historicalData, setHistoricalData] = useState(null);

  const handleStartDebate = (query, councilMembers, chairman) => {
    // Clear any historical data when starting a new debate
    setHistoricalData(null);
    setSelectedChairman(chairman);
    startDebate(query, councilMembers, chairman);
  };

  const handleSelectDecision = async (decisionId) => {
    try {
      const response = await fetch(`/api/history/${decisionId}`);
      if (!response.ok) throw new Error('Failed to fetch decision');
      const data = await response.json();

      // Transform historical data to match streaming format
      const transformedResponses = {};
      data.responses.forEach(resp => {
        transformedResponses[resp.model_name] = {
          model_id: resp.model_name,
          text: resp.response_text,
          status: 'complete',
          tokens: resp.tokens_used,
          responseTime: resp.response_time,
        };
      });

      const transformedSynthesis = data.synthesis ? {
        status: 'complete',
        consensus: data.synthesis.consensus_items || [],
        debates: data.synthesis.debates || [],
        text: data.synthesis.synthesis_text,
      } : null;

      setHistoricalData({
        decisionId: data.id,
        query: data.query,
        chairman: data.chairman_model,
        responses: transformedResponses,
        synthesis: transformedSynthesis,
      });

      setSelectedChairman(data.chairman_model);
      setShowHistory(false); // Close history panel after selection
    } catch (err) {
      console.error('Error fetching decision:', err);
      alert('Failed to load decision: ' + err.message);
    }
  };

  // Use historical data if available, otherwise use streaming data
  const displayDecisionId = historicalData?.decisionId || decisionId;
  const displayResponses = historicalData?.responses || modelResponses;
  const displaySynthesis = historicalData?.synthesis || synthesis;
  const councilMembersList = Object.keys(displayResponses);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                LLM Council
              </h1>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Multi-Model AI Decision Framework
              </p>
            </div>
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="btn-secondary"
            >
              {showHistory ? 'Hide History' : 'Show History'}
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Error Display */}
        {error && (
          <div className="mb-4 p-4 bg-red-100 dark:bg-red-900/20 border border-red-400 dark:border-red-700 rounded-lg">
            <p className="text-red-700 dark:text-red-400">Error: {error}</p>
          </div>
        )}

        {/* Decision ID Display */}
        {displayDecisionId && (
          <div className="mb-4 p-3 bg-blue-100 dark:bg-blue-900/20 border border-blue-400 dark:border-blue-700 rounded-lg">
            <p className="text-blue-700 dark:text-blue-400 text-sm">
              {historicalData ? '📜 Historical ' : ''}Decision ID: <span className="font-mono font-bold">#{displayDecisionId}</span>
              {historicalData && (
                <button
                  onClick={() => setHistoricalData(null)}
                  className="ml-4 text-xs underline hover:no-underline"
                >
                  Clear
                </button>
              )}
            </p>
          </div>
        )}

        {/* History Browser */}
        {showHistory && (
          <div className="mb-6">
            <HistoryBrowser onSelectDecision={handleSelectDecision} />
          </div>
        )}

        {/* Query Input */}
        <div className="mb-6">
          <QueryInput
            models={models}
            onSubmit={handleStartDebate}
            disabled={debating || modelsLoading}
          />
        </div>

        {/* Council Responses and Synthesis */}
        {councilMembersList.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Council Member Responses - Left Column (2/3) */}
            <div className="lg:col-span-2 space-y-4">
              <h2 className="text-2xl font-bold">Council Responses</h2>
              {councilMembersList.map(modelId => (
                <CouncilMemberCard
                  key={modelId}
                  modelId={modelId}
                  response={displayResponses[modelId]}
                  isChairman={modelId === selectedChairman}
                />
              ))}
            </div>

            {/* Synthesis Panel - Right Column (1/3) */}
            <div className="lg:col-span-1">
              <div className="sticky top-4">
                <SynthesisPanel synthesis={displaySynthesis} />
              </div>
            </div>
          </div>
        )}

        {/* Loading State */}
        {modelsLoading && (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">Loading models...</p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-12 py-6 border-t border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 text-center text-sm text-gray-600 dark:text-gray-400">
          <p>Multi-Model AI Decision Framework • LLM Council v1.0.0</p>
        </div>
      </footer>
    </div>
  );
}
