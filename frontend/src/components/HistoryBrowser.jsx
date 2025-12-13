import { useState, useEffect } from 'react';

export default function HistoryBrowser({ onSelectDecision }) {
  const [decisions, setDecisions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/history/');
      if (!response.ok) throw new Error('Failed to fetch history');
      const data = await response.json();
      setDecisions(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleString();
  };

  if (loading) {
    return (
      <div className="card">
        <h3 className="text-xl font-bold mb-4">Decision History</h3>
        <p className="text-gray-500">Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <h3 className="text-xl font-bold mb-4">Decision History</h3>
        <p className="text-red-600">{error}</p>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-bold">Decision History</h3>
        <button onClick={fetchHistory} className="btn-secondary text-sm">
          Refresh
        </button>
      </div>

      {decisions.length === 0 ? (
        <p className="text-gray-500 italic">No decisions yet. Start a debate to create one!</p>
      ) : (
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {decisions.map(decision => (
            <div
              key={decision.id}
              className="border border-gray-200 dark:border-gray-700 rounded-lg p-3 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer transition-colors"
              onClick={() => onSelectDecision(decision.id)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate" title={decision.query}>
                    {decision.query}
                  </p>
                  <div className="flex items-center space-x-2 mt-1 text-xs text-gray-500">
                    <span>Chairman: {decision.chairman_model}</span>
                    <span>•</span>
                    <span>{decision.response_count} responses</span>
                  </div>
                </div>
                <span className="text-xs text-gray-400 whitespace-nowrap ml-2">
                  {formatDate(decision.created_at)}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
