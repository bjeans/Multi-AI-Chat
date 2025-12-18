import { useState } from 'react';
import { ModelCard } from './ModelCard';
import { getServerStats } from '../utils/modelSelection';

export function ServerGroup({
  serverGroup,
  selectedModels,
  onModelSelect
}) {
  const [expanded, setExpanded] = useState(true);
  const { server, models } = serverGroup;

  // Calculate server usage stats
  const stats = getServerStats(serverGroup, selectedModels);

  return (
    <div className="server-group">
      <div
        className="server-header"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="server-title">
          <span className="server-icon">🖥️</span>
          <span className="server-host">Server: {server.host}</span>
          <span className={`health-badge ${server.health_status}`}>
            {server.health_status === 'healthy' ? '● Healthy' : '⚠ Issues'}
          </span>
        </div>

        <div className="server-stats">
          <span className="stat">TPM: {(server.tpm / 1000).toFixed(0)}K</span>
          <span className="stat">RPM: {server.rpm}</span>
          <span className="stat">{server.model_count} models</span>
          {server.performance_tier === 'high' && (
            <span className="badge-high">High Performance</span>
          )}
          <span className={`expand-icon ${expanded ? 'expanded' : ''}`}>▼</span>
        </div>
      </div>

      {/* Resource warnings for this server */}
      {expanded && stats.selectedCount > 0 && (
        <div className="server-usage">
          <div className="usage-summary">
            {stats.selectedCount} model(s) selected
            {stats.totalMemory > 0 && ` • ~${stats.totalMemory}GB memory`}
          </div>

          {stats.hasConflict && stats.largeModels.length > 1 && (
            <div className="warning severity-high">
              ⚠️ {stats.largeModels.length} large models selected. Expect significant delays during model swapping!
            </div>
          )}

          {stats.hasConflict && stats.largeModels.length === 1 && stats.mediumModels.length >= 1 && (
            <div className="warning severity-medium">
              ⚠️ Large model + medium model selected. May cause delays.
            </div>
          )}

          {!stats.hasConflict && stats.selectedCount > 0 && (
            <div className="warning severity-info">
              ✓ Good selection: {stats.selectedCount === 1 ? 'Single model' : 'Small models only'}
            </div>
          )}
        </div>
      )}

      {/* Models list */}
      {expanded && (
        <div className="models-list">
          {models.map(model => (
            <ModelCard
              key={model.id}
              model={model}
              isSelected={selectedModels.includes(model.id)}
              onSelect={() => onModelSelect(model.id, !selectedModels.includes(model.id))}
            />
          ))}
        </div>
      )}
    </div>
  );
}
