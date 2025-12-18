import { useState } from 'react';
import {
  formatResponseTime,
  formatMemory,
  getHealthStatusIcon,
  getSizeClassName
} from '../utils/modelSelection';

export function ModelCard({ model, isSelected, onSelect }) {
  const [showDetails, setShowDetails] = useState(false);

  const handleKeyDown = (e) => {
    if (e.key === ' ' || e.key === 'Enter') {
      e.preventDefault();
      onSelect();
    }
  };

  return (
    <div
      className={`model-card ${isSelected ? 'selected' : ''} ${getSizeClassName(model.size.size_tier)}`}
      tabIndex={0}
      onKeyDown={handleKeyDown}
    >
      <div className="model-main" onClick={onSelect}>
        <input
          type="checkbox"
          checked={isSelected}
          onChange={onSelect}
          onClick={(e) => e.stopPropagation()}
        />

        <div className="model-info">
          <div className="model-name">
            {model.display_name}

            {/* Badges */}
            {model.is_latest_alias && (
              <span className="badge latest">
                Latest → {model.actual_tag}
              </span>
            )}
            <span className={`badge size-${model.size.size_tier}`}>
              {model.size.parameters}
            </span>
            {model.is_duplicate && (
              <span className="badge duplicate">
                {model.duplicate_count} servers
              </span>
            )}
          </div>

          <div className="model-meta">
            <span className="provider">{model.provider}</span>
            <span className="category-badge">{model.model_category}</span>
            <span className="memory">{formatMemory(model.size.estimated_memory_gb)}</span>

            {/* Health status */}
            {model.health && (
              <span className={`health ${model.health.status}`}>
                {getHealthStatusIcon(model.health.status)}
                {' '}
                {formatResponseTime(model.health.response_time_ms)}
              </span>
            )}
          </div>

          {/* Better server recommendation */}
          {model.is_duplicate && model.better_server && (
            <div className="recommendation">
              💡 Also on {model.better_server.split('//')[1]} (better performance)
            </div>
          )}
        </div>

        {/* Details toggle */}
        {model.health && (
          <button
            className="details-toggle"
            onClick={(e) => {
              e.stopPropagation();
              setShowDetails(!showDetails);
            }}
          >
            {showDetails ? '▲' : '▼'}
          </button>
        )}
      </div>

      {/* Health details */}
      {showDetails && model.health && (
        <div className="model-details">
          <div className="detail-row">
            <span>Health:</span>
            <span>{model.health.healthy_count} healthy, {model.health.unhealthy_count} unhealthy</span>
          </div>
          {model.health.last_checked && (
            <div className="detail-row">
              <span>Last checked:</span>
              <span>{new Date(model.health.last_checked).toLocaleString()}</span>
            </div>
          )}
          {model.health.error_message && (
            <div className="detail-row error">
              <span>Error:</span>
              <span>{model.health.error_message}</span>
            </div>
          )}
          <div className="detail-row">
            <span>Max tokens:</span>
            <span>{model.max_tokens.toLocaleString()}</span>
          </div>
          <div className="detail-row">
            <span>Function calling:</span>
            <span>{model.supports_function_calling ? 'Yes' : 'No'}</span>
          </div>
        </div>
      )}
    </div>
  );
}
