/**
 * Utility functions for model selection and analysis
 */

/**
 * Safely extract hostname from URL string
 * @param {string} url - URL to parse (e.g., "http://192.168.1.100:11434")
 * @returns {string} hostname or full URL if parsing fails
 */
export function extractHostname(url) {
  try {
    const parsed = new URL(url);
    return parsed.hostname;
  } catch {
    // Fallback: try to extract after // and before :
    const match = url.match(/\/\/([^:\/]+)/);
    return match ? match[1] : url;
  }
}

export function findModelById(modelId, serverGroups) {
  for (const group of serverGroups) {
    const model = group.models.find(m => m.id === modelId);
    if (model) return model;
  }
  return null;
}

export function analyzeSelectionDiversity(selectedModelIds, serverGroups) {
  const selectedModels = selectedModelIds
    .map(id => findModelById(id, serverGroups))
    .filter(m => m !== null);

  const providers = new Set(selectedModels.map(m => m.provider));
  const categories = new Set(selectedModels.map(m => m.model_category));
  const baseModels = new Set(selectedModels.map(m => m.base_model));

  return {
    providerCount: providers.size,
    categoryCount: categories.size,
    uniqueModelCount: baseModels.size,
    hasDuplicates: selectedModelIds.length > baseModels.size,
    providers: Array.from(providers),
    categories: Array.from(categories)
  };
}

export function getServerStats(serverGroup, selectedModelIds) {
  const selectedOnServer = serverGroup.models.filter(m =>
    selectedModelIds.includes(m.id)
  );

  const totalMemory = selectedOnServer.reduce(
    (sum, m) => sum + m.size.estimated_memory_gb,
    0
  );

  const largeModels = selectedOnServer.filter(m => m.size.size_tier === 'large');
  const mediumModels = selectedOnServer.filter(m => m.size.size_tier === 'medium');

  return {
    selectedCount: selectedOnServer.length,
    totalMemory,
    largeModels,
    mediumModels,
    hasConflict: largeModels.length > 1 || (largeModels.length >= 1 && mediumModels.length >= 1)
  };
}

export function formatResponseTime(ms) {
  if (ms < 1000) {
    return `${Math.round(ms)}ms`;
  } else {
    return `${(ms / 1000).toFixed(1)}s`;
  }
}

export function formatMemory(gb) {
  if (gb < 1) {
    return `${Math.round(gb * 1024)}MB`;
  } else {
    return `${gb}GB`;
  }
}

export function getHealthStatusIcon(status) {
  switch (status) {
    case 'healthy':
      return '✓';
    case 'unhealthy':
      return '✗';
    default:
      return '?';
  }
}

export function getSizeClassName(sizeTier) {
  return `size-${sizeTier}`;
}

export function getSeverityClassName(severity) {
  return `severity-${severity}`;
}
