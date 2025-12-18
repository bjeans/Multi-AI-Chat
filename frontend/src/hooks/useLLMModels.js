import { useState, useEffect, useCallback } from 'react';

export function useLLMModels() {
  const [models, setModels] = useState([]);
  const [serverGroups, setServerGroups] = useState([]);
  const [selectedModels, setSelectedModels] = useState([]);
  const [selectionAnalysis, setSelectionAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [useServerGrouping, setUseServerGrouping] = useState(true);

  useEffect(() => {
    fetchModels();
  }, [useServerGrouping]);

  const fetchModels = async () => {
    try {
      setLoading(true);

      if (useServerGrouping) {
        // Fetch server-grouped models with health info
        const response = await fetch('/api/config/models/by-server');
        if (!response.ok) throw new Error('Failed to fetch models');
        const data = await response.json();
        setServerGroups(data);

        // Also flatten for backward compatibility
        const flatModels = data.flatMap(group => group.models);
        setModels(flatModels);
      } else {
        // Fallback to simple model list
        const response = await fetch('/api/config/models');
        if (!response.ok) throw new Error('Failed to fetch models');
        const data = await response.json();
        setModels(data);
        setServerGroups([]);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const analyzeSelection = useCallback(async (modelIds) => {
    if (modelIds.length === 0) {
      setSelectionAnalysis(null);
      return;
    }

    try {
      const response = await fetch('/api/config/models/analyze-selection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_ids: modelIds })
      });

      if (!response.ok) throw new Error('Failed to analyze selection');
      const analysis = await response.json();
      setSelectionAnalysis(analysis);
    } catch (err) {
      console.error('Error analyzing selection:', err);
      setSelectionAnalysis(null);
    }
  }, []);

  const handleModelSelect = useCallback((modelId, isSelected) => {
    const newSelection = isSelected
      ? [...selectedModels, modelId]
      : selectedModels.filter(id => id !== modelId);

    setSelectedModels(newSelection);
    analyzeSelection(newSelection);
  }, [selectedModels, analyzeSelection]);

  const clearSelection = useCallback(() => {
    setSelectedModels([]);
    setSelectionAnalysis(null);
  }, []);

  return {
    models,
    serverGroups,
    selectedModels,
    selectionAnalysis,
    loading,
    error,
    useServerGrouping,
    setUseServerGrouping,
    handleModelSelect,
    clearSelection,
    refetch: fetchModels
  };
}
