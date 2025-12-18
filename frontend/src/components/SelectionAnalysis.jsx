import { getSeverityClassName } from '../utils/modelSelection';

export function SelectionAnalysis({ analysis }) {
  if (!analysis || analysis.total_models_selected === 0) {
    return null;
  }

  const hasHighWarnings = analysis.warnings.some(w => w.severity === 'high');
  const hasMediumWarnings = analysis.warnings.some(w => w.severity === 'medium');

  return (
    <div className={`selection-analysis ${hasHighWarnings ? 'has-high-warnings' : hasMediumWarnings ? 'has-medium-warnings' : 'good'}`}>
      <h3>Selection Analysis</h3>

      <div className="summary">
        <div className="summary-item">
          <span className="label">Models:</span>
          <span className="value">{analysis.total_models_selected}</span>
        </div>
        <div className="summary-item">
          <span className="label">Servers:</span>
          <span className="value">{analysis.servers_used}</span>
        </div>
        <div className="summary-item">
          <span className="label">Diversity:</span>
          <span className={`value diversity-${getDiversityLevel(analysis.diversity_score)}`}>
            {analysis.diversity_score}/100
          </span>
        </div>
      </div>

      {/* Warnings */}
      {analysis.warnings.length > 0 && (
        <div className="warnings-section">
          <h4>⚠️ Warnings</h4>
          <div className="warnings-list">
            {analysis.warnings.map((warning, idx) => (
              <div key={idx} className={`warning-item ${getSeverityClassName(warning.severity)}`}>
                <div className="warning-message">{warning.message}</div>
                {warning.models && warning.models.length > 0 && (
                  <div className="warning-models">
                    Models: {warning.models.join(', ')}
                  </div>
                )}
                {warning.estimated_total_memory && (
                  <div className="warning-memory">
                    Total memory: {warning.estimated_total_memory}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {analysis.recommendations.length > 0 && (
        <div className="recommendations-section">
          <h4>💡 Recommendations</h4>
          <div className="recommendations-list">
            {analysis.recommendations.map((rec, idx) => (
              <div key={idx} className="recommendation-item">
                <div className="recommendation-action">
                  Move <strong>{rec.model}</strong> from{' '}
                  {rec.from_server.split('//')[1]} to{' '}
                  {rec.to_server.split('//')[1]}
                </div>
                <div className="recommendation-reason">{rec.reason}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No warnings - positive message */}
      {analysis.warnings.length === 0 && analysis.total_models_selected >= 2 && (
        <div className="positive-message">
          ✓ Great selection! No resource conflicts detected.
        </div>
      )}
    </div>
  );
}

function getDiversityLevel(score) {
  if (score >= 70) return 'good';
  if (score >= 40) return 'fair';
  return 'poor';
}
