import { useState, useEffect } from 'react';

// Quick prompt examples - moved outside component for performance
const QUICK_PROMPTS = {
  'Web Frameworks': 'What are the pros and cons of different web frameworks for a modern web application?',
  'API Security': 'What are the best practices for securing REST APIs in production environments?',
  'Architecture': 'What are the pros and cons of different database architectures for a high-traffic e-commerce platform?',
};

// Helper function to get model provider label
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

export default function QueryInput({ models, mcpTools = [], serverLabels = [], onSubmit, disabled }) {
  const [query, setQuery] = useState('');
  const [selectedModels, setSelectedModels] = useState([]);
  const [chairman, setChairman] = useState('');
  
  // MCP Tools state
  const [mcpEnabled, setMcpEnabled] = useState(false);
  const [selectedServerLabels, setSelectedServerLabels] = useState([]);
  const [selectedTools, setSelectedTools] = useState([]);
  const [showMcpPanel, setShowMcpPanel] = useState(false);

  // Reset MCP selections when tools change
  useEffect(() => {
    if (mcpTools.length === 0) {
      setMcpEnabled(false);
      setSelectedServerLabels([]);
      setSelectedTools([]);
    }
  }, [mcpTools]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && selectedModels.length >= 2 && chairman) {
      const mcpConfig = mcpEnabled && mcpTools.length > 0 ? {
        enabled: true,
        serverLabels: selectedServerLabels,
        allowedTools: selectedTools,
      } : null;
      onSubmit(query, selectedModels, chairman, mcpConfig);
    }
  };

  const toggleModel = (modelId) => {
    setSelectedModels(prev => {
      if (prev.includes(modelId)) {
        return prev.filter(id => id !== modelId);
      } else {
        return [...prev, modelId];
      }
    });
  };

  const toggleServerLabel = (label) => {
    setSelectedServerLabels(prev => {
      if (prev.includes(label)) {
        return prev.filter(l => l !== label);
      } else {
        return [...prev, label];
      }
    });
  };

  const toggleTool = (toolName) => {
    setSelectedTools(prev => {
      if (prev.includes(toolName)) {
        return prev.filter(t => t !== toolName);
      } else {
        return [...prev, toolName];
      }
    });
  };

  const handleQuickPrompt = (prompt) => {
    setQuery(QUICK_PROMPTS[prompt] || '');
  };

  const handleModelKeyDown = (e, modelId) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      toggleModel(modelId);
    }
  };

  const availableModels = models.filter(m => m.available);

  // Set default chairman to Claude Opus 4.5 if available
  const recommendedChairman = availableModels.find(m =>
    m.id.includes('claude-opus-4') || m.name.includes('Claude Opus')
  );

  return (
    <div className="card">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Research Prompt */}
        <div>
          <label className="block text-sm font-medium mb-3 text-gray-300">
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
            <span className="text-xs text-gray-400 self-center mr-1">Quick prompts:</span>
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

        {/* Council Members */}
        <div>
          <div className="flex justify-between items-center mb-3">
            <label className="block text-sm font-medium text-gray-300">
              Council Members
            </label>
            <span className="text-xs text-gray-400">
              Select 2+ models for best results
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {availableModels.length === 0 ? (
              <p className="text-gray-500 col-span-full">No models available</p>
            ) : (
              availableModels.map(model => {
                const isSelected = selectedModels.includes(model.id);
                return (
                  <div
                    key={model.id}
                    onClick={() => !disabled && toggleModel(model.id)}
                    onKeyDown={(e) => !disabled && handleModelKeyDown(e, model.id)}
                    role="checkbox"
                    aria-checked={isSelected}
                    tabIndex={disabled ? -1 : 0}
                    className={`model-card ${isSelected ? 'model-card-selected' : ''}`}
                  >
                    <div className="flex items-start space-x-3">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => toggleModel(model.id)}
                        disabled={disabled}
                        tabIndex={-1}
                        aria-hidden="true"
                        className="mt-1 rounded text-blue-600 focus:ring-blue-500 bg-transparent border-gray-600"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-gray-100 truncate">
                          {model.name}
                        </div>
                        <div className="text-xs text-gray-400 mt-1">
                          {getModelProviderLabel(model.id)}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Chairman Model */}
        <div>
          <label className="block text-sm font-medium mb-3 text-gray-300">
            Chairman Model <span className="text-xs text-gray-400 font-normal">Synthesizes the final answer</span>
          </label>
          <select
            value={chairman}
            onChange={(e) => setChairman(e.target.value)}
            className="input-field"
            disabled={disabled}
          >
            <option value="">Select chairman...</option>
            {availableModels.map(model => {
              const isRecommended = recommendedChairman && model.id === recommendedChairman.id;
              return (
                <option key={model.id} value={model.id}>
                  {model.name}{isRecommended ? ' (Recommended)' : ''}
                </option>
              );
            })}
          </select>
        </div>

        {/* MCP Tools Section */}
        {mcpTools.length > 0 && (
          <div className="border-t border-gray-700 pt-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={mcpEnabled}
                    onChange={(e) => setMcpEnabled(e.target.checked)}
                    disabled={disabled}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-blue-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
                <span className="text-sm font-medium text-gray-300">
                  Enable MCP Tools
                </span>
                <span className="text-xs text-gray-500">
                  ({mcpTools.length} tools available)
                </span>
              </div>
              {mcpEnabled && (
                <button
                  type="button"
                  onClick={() => setShowMcpPanel(!showMcpPanel)}
                  className="text-xs text-blue-400 hover:text-blue-300"
                >
                  {showMcpPanel ? 'Hide configuration' : 'Configure tools'}
                </button>
              )}
            </div>

            {/* MCP Configuration Panel */}
            {mcpEnabled && showMcpPanel && (
              <div className="bg-gray-800/50 rounded-lg p-4 space-y-4">
                {/* Server Labels */}
                {serverLabels.length > 0 && (
                  <div>
                    <label className="block text-xs font-medium text-gray-400 mb-2">
                      MCP Servers (leave empty for all)
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {serverLabels.map(label => (
                        <button
                          key={label}
                          type="button"
                          onClick={() => toggleServerLabel(label)}
                          disabled={disabled}
                          className={`px-3 py-1 text-xs rounded-full transition-colors ${
                            selectedServerLabels.includes(label)
                              ? 'bg-blue-600 text-white'
                              : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                          }`}
                        >
                          {label}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Available Tools */}
                <div>
                  <label className="block text-xs font-medium text-gray-400 mb-2">
                    Available Tools (leave empty for all)
                  </label>
                  <div className="max-h-48 overflow-y-auto space-y-2">
                    {mcpTools
                      .filter(tool => 
                        selectedServerLabels.length === 0 || 
                        selectedServerLabels.includes(tool.server_label)
                      )
                      .map(tool => (
                        <div
                          key={tool.name}
                          className={`p-2 rounded-lg border cursor-pointer transition-colors ${
                            selectedTools.includes(tool.name)
                              ? 'border-blue-500 bg-blue-900/30'
                              : 'border-gray-700 bg-gray-800/50 hover:border-gray-600'
                          }`}
                          onClick={() => !disabled && toggleTool(tool.name)}
                        >
                          <div className="flex items-center gap-2">
                            <input
                              type="checkbox"
                              checked={selectedTools.includes(tool.name)}
                              onChange={() => toggleTool(tool.name)}
                              disabled={disabled}
                              className="rounded text-blue-600 focus:ring-blue-500 bg-transparent border-gray-600"
                            />
                            <div className="flex-1 min-w-0">
                              <div className="text-sm font-medium text-gray-200 truncate">
                                {tool.name}
                              </div>
                              {tool.description && (
                                <div className="text-xs text-gray-500 truncate">
                                  {tool.description}
                                </div>
                              )}
                            </div>
                            {tool.server_label && (
                              <span className="text-xs text-gray-500 bg-gray-700 px-2 py-0.5 rounded">
                                {tool.server_label}
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                  </div>
                </div>

                {/* Selection summary */}
                <div className="text-xs text-gray-500 pt-2 border-t border-gray-700">
                  {selectedServerLabels.length === 0 && selectedTools.length === 0 ? (
                    <span>All MCP tools will be available to models</span>
                  ) : (
                    <span>
                      {selectedServerLabels.length > 0 && `${selectedServerLabels.length} server(s) selected`}
                      {selectedServerLabels.length > 0 && selectedTools.length > 0 && ', '}
                      {selectedTools.length > 0 && `${selectedTools.length} tool(s) selected`}
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={disabled || !query.trim() || selectedModels.length < 2 || !chairman}
          className="btn-primary w-full"
        >
          {disabled ? 'Researching...' : 'Start Research'}
        </button>
      </form>
    </div>
  );
}
