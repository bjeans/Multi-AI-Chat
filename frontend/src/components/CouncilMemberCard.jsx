export default function CouncilMemberCard({ modelId, response, isChairman }) {
  const getStatusColor = () => {
    switch (response.status) {
      case 'pending':
        return 'bg-gray-700 text-gray-400';
      case 'streaming':
        return 'bg-blue-900/30 text-blue-300';
      case 'complete':
        return 'bg-green-900/30 text-green-300';
      case 'error':
        return 'bg-red-900/30 text-red-300';
      default:
        return 'bg-gray-700 text-gray-400';
    }
  };

  const getStatusText = () => {
    switch (response.status) {
      case 'pending':
        return 'Waiting...';
      case 'streaming':
        return 'Streaming...';
      case 'complete':
        return `Complete (${response.tokens} tokens, ${response.responseTime.toFixed(2)}s)`;
      case 'error':
        return 'Error';
      default:
        return 'Unknown';
    }
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <h3 className="font-semibold text-lg text-gray-100 truncate" title={modelId}>
            {modelId}
          </h3>
          {isChairman && (
            <span className="px-2 py-1 bg-purple-900/30 text-purple-300 text-xs rounded-full">
              Chairman
            </span>
          )}
        </div>
        <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor()}`}>
          {getStatusText()}
        </span>
      </div>

      <div className="bg-[#0f1623] rounded-lg p-3 min-h-[150px] max-h-[400px] overflow-y-auto">
        {response.status === 'error' ? (
          <p className="text-red-400">{response.error}</p>
        ) : response.text ? (
          <div className="text-gray-300 max-w-none text-sm whitespace-pre-wrap leading-relaxed">
            {response.text}
            {response.status === 'streaming' && (
              <span className="inline-block w-2 h-4 bg-blue-500 ml-1 animate-pulse"></span>
            )}
          </div>
        ) : (
          <p className="text-gray-400 italic">Waiting for response...</p>
        )}
      </div>
    </div>
  );
}
