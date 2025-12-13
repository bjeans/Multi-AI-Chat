import { useState } from 'react';

export default function QueryInput({ models, onSubmit, disabled }) {
  const [query, setQuery] = useState('');
  const [selectedModels, setSelectedModels] = useState([]);
  const [chairman, setChairman] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && selectedModels.length >= 2 && chairman) {
      onSubmit(query, selectedModels, chairman);
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

  const availableModels = models.filter(m => m.available);

  return (
    <div className="card">
      <h2 className="text-2xl font-bold mb-4">Council Debate</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Query Input */}
        <div>
          <label className="block text-sm font-medium mb-2">
            Question / Decision
          </label>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="input-field resize-none"
            rows="4"
            placeholder="Enter your question or decision for the council to debate..."
            disabled={disabled}
          />
        </div>

        {/* Model Selection */}
        <div>
          <label className="block text-sm font-medium mb-2">
            Council Members (select at least 2)
          </label>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2 max-h-48 overflow-y-auto p-2 border border-gray-300 dark:border-gray-600 rounded-lg">
            {availableModels.length === 0 ? (
              <p className="text-gray-500 col-span-full">No models available</p>
            ) : (
              availableModels.map(model => (
                <label
                  key={model.id}
                  className="flex items-center space-x-2 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 p-2 rounded"
                >
                  <input
                    type="checkbox"
                    checked={selectedModels.includes(model.id)}
                    onChange={() => toggleModel(model.id)}
                    disabled={disabled}
                    className="rounded text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm truncate" title={model.id}>
                    {model.name}
                  </span>
                </label>
              ))
            )}
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Selected: {selectedModels.length} models
          </p>
        </div>

        {/* Chairman Selection */}
        <div>
          <label className="block text-sm font-medium mb-2">
            Chairman (synthesizes final conclusion - can be different from council)
          </label>
          <select
            value={chairman}
            onChange={(e) => setChairman(e.target.value)}
            className="input-field"
            disabled={disabled}
          >
            <option value="">Select chairman...</option>
            {availableModels.map(model => (
              <option key={model.id} value={model.id}>
                {model.name}
              </option>
            ))}
          </select>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={disabled || !query.trim() || selectedModels.length < 2 || !chairman}
          className="btn-primary w-full"
        >
          {disabled ? 'Debating...' : 'Start Debate'}
        </button>
      </form>
    </div>
  );
}
