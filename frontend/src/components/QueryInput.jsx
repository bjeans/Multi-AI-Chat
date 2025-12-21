import { useState } from 'react';
import { ServerGroup } from './ServerGroup';
import { SelectionAnalysis } from './SelectionAnalysis';

// Quick prompt examples - moved outside component for performance
const QUICK_PROMPTS = {
  'Web Frameworks': 'What are the pros and cons of different web frameworks for a modern web application?',
  'API Security': 'What are the best practices for securing REST APIs in production environments?',
  'Architecture': 'What are the pros and cons of different database architectures for a high-traffic e-commerce platform?',
};

// Helper function to get model provider label (for legacy flat view)
const getModelProviderLabel = (modelId) => {
  if (modelId.includes('gpt')) return 'OpenAI Flagship';
  if (modelId.includes('claude')) return 'Anthropic Flagship';
  if (modelId.includes('gemini')) return 'Google Flagship';
  if (modelId.includes('llama')) return 'Meta Flagship';
  if (modelId.includes('mistral')) return 'Mistral AI Flagship';
  if (modelId.includes('deepseek')) return 'DeepSeek Reasoning';
  if (modelId.includes('grok')) return 'xAI Flagship';
  return 'AI Model';
};

export default function QueryInput({
  models,
  serverGroups = [],
  selectedModels = [],
  selectionAnalysis = null,
  onModelSelect,
  onSubmit,
  disabled,
  useServerGrouping = true
}) {
  const [query, setQuery] = useState('');
  const [chairman, setChairman] = useState('');

  // For backward compatibility - local state if not using hook
  const [localSelectedModels, setLocalSelectedModels] = useState([]);

  // Use provided or local state
  const activeSelectedModels = onModelSelect ? selectedModels : localSelectedModels;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && activeSelectedModels.length >= 2 && chairman) {
      // Extract model display names for submission
      const modelNames = activeSelectedModels.map(id => {
        // id format is "model_name_host", so extract just the model name
        return id.split('_').slice(0, -1).join('_');
      });
      onSubmit(query, modelNames, chairman.split('_').slice(0, -1).join('_'));
    }
  };

  const handleLocalModelSelect = (modelId, isSelected) => {
    if (onModelSelect) {
      onModelSelect(modelId, isSelected);
    } else {
      setLocalSelectedModels(prev => {
        if (isSelected) {
          return [...prev, modelId];
        } else {
          return prev.filter(id => id !== modelId);
        }
      });
    }
  };

  const handleQuickPrompt = (prompt) => {
    setQuery(QUICK_PROMPTS[prompt] || '');
  };

  // Get all available models (flatten from serverGroups or use models)
  const availableModels = useServerGrouping && serverGroups.length > 0
    ? serverGroups.flatMap(group => group.models)
    : models.filter(m => m.available);

  // Set default chairman to Claude Opus 4.5 if available
  const recommendedChairman = availableModels.find(m =>
    m.display_name?.includes('claude-opus-4') || m.name?.includes('Claude Opus')
  );

  return (
    <div className="card">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Research Prompt */}
        <div>
          <label className="block text-sm font-medium mb-3 text-gray-700 dark:text-gray-300">
            Research Prompt
          </label>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="input-field resize-none"
            rows="4"
            placeholder='Enter your research question or topic... e.g., "What are the pros and cons of different database architectures for a high-traffic e-commerce platform?"'
            disabled={disabled}
          />

          {/* Quick Prompts */}
          <div className="flex gap-2 mt-3">
            <span className="text-xs text-gray-500 dark:text-gray-400 self-center mr-1">Quick prompts:</span>
            {Object.keys(QUICK_PROMPTS).map(prompt => (
              <button
                key={prompt}
                type="button"
                onClick={() => handleQuickPrompt(prompt)}
                className="quick-prompt-pill"
                disabled={disabled}
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>

        {/* Selection Analysis */}
        {selectionAnalysis && activeSelectedModels.length > 0 && (
          <SelectionAnalysis analysis={selectionAnalysis} />
        )}

        {/* Council Members */}
        <div>
          <div className="flex justify-between items-center mb-3">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Council Members
            </label>
            <span className="text-xs text-gray-500 dark:text-gray-400">
              Select 2+ models for best results ({activeSelectedModels.length} selected)
            </span>
          </div>

          {/* Server-grouped or flat layout */}
          {useServerGrouping && serverGroups.length > 0 ? (
            <div className="server-groups-container">
              {serverGroups.map(group => (
                <ServerGroup
                  key={group.server.api_base}
                  serverGroup={group}
                  selectedModels={activeSelectedModels}
                  onModelSelect={handleLocalModelSelect}
                />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {availableModels.length === 0 ? (
                <p className="text-gray-500 dark:text-gray-400 col-span-full">No models available</p>
              ) : (
                availableModels.map(model => {
                  const modelId = model.id || model.name;
                  const isSelected = activeSelectedModels.includes(modelId);
                  return (
                    <div
                      key={modelId}
                      onClick={() => !disabled && handleLocalModelSelect(modelId, !isSelected)}
                      role="checkbox"
                      aria-checked={isSelected}
                      tabIndex={disabled ? -1 : 0}
                      className={`model-card ${isSelected ? 'model-card-selected' : ''}`}
                    >
                      <div className="flex items-start space-x-3">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => handleLocalModelSelect(modelId, !isSelected)}
                          disabled={disabled}
                          tabIndex={-1}
                          aria-hidden="true"
                          className="mt-1 rounded text-blue-600 focus:ring-blue-500 bg-white dark:bg-transparent border-gray-300 dark:border-gray-600"
                        />
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                            {model.name || model.display_name}
                          </div>
                          <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                            {getModelProviderLabel(modelId)}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          )}
        </div>

        {/* Chairman Model */}
        <div>
          <label className="block text-sm font-medium mb-3 text-gray-700 dark:text-gray-300">
            Chairman Model <span className="text-xs text-gray-500 dark:text-gray-400 font-normal">Synthesizes the final answer</span>
          </label>
          <select
            value={chairman}
            onChange={(e) => setChairman(e.target.value)}
            className="input-field"
            disabled={disabled}
          >
            <option value="">Select chairman...</option>
            {availableModels.map(model => {
              const modelId = model.id || model.name;
              const modelName = model.name || model.display_name;
              const isRecommended = recommendedChairman && modelId === recommendedChairman.id;
              return (
                <option key={modelId} value={modelId}>
                  {modelName}{isRecommended ? ' (Recommended)' : ''}
                </option>
              );
            })}
          </select>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={disabled || !query.trim() || activeSelectedModels.length < 2 || !chairman}
          className="btn-primary w-full"
        >
          {disabled ? 'Researching...' : 'Start Research'}
        </button>
      </form>
    </div>
  );
}
