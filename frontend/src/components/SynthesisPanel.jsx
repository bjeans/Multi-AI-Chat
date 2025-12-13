export default function SynthesisPanel({ synthesis }) {
  if (!synthesis) {
    return (
      <div className="card">
        <h3 className="text-xl font-bold mb-4">Synthesis</h3>
        <p className="text-gray-500 italic">
          Synthesis will appear here after all council members respond...
        </p>
      </div>
    );
  }

  if (synthesis.status === 'generating') {
    return (
      <div className="card">
        <h3 className="text-xl font-bold mb-4">Synthesis</h3>
        <div className="flex items-center space-x-2">
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
          <p className="text-blue-600">Chairman is synthesizing responses...</p>
        </div>
      </div>
    );
  }

  if (synthesis.status === 'error') {
    return (
      <div className="card">
        <h3 className="text-xl font-bold mb-4">Synthesis</h3>
        <p className="text-red-600">{synthesis.error}</p>
      </div>
    );
  }

  return (
    <div className="card space-y-6">
      <h3 className="text-xl font-bold">Synthesis</h3>

      {/* Consensus Section */}
      {synthesis.consensus && synthesis.consensus.length > 0 && (
        <div>
          <h4 className="text-lg font-semibold text-green-700 dark:text-green-400 mb-2">
            ✓ Consensus
          </h4>
          <ul className="space-y-2">
            {synthesis.consensus.map((item, idx) => (
              <li
                key={idx}
                className="bg-green-50 dark:bg-green-900/20 border-l-4 border-green-500 p-3 rounded"
              >
                <p className="text-sm">{item}</p>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Debates Section */}
      {synthesis.debates && synthesis.debates.length > 0 && (
        <div>
          <h4 className="text-lg font-semibold text-orange-700 dark:text-orange-400 mb-2">
            ⚡ Debates
          </h4>
          <ul className="space-y-2">
            {synthesis.debates.map((debate, idx) => (
              <li
                key={idx}
                className="bg-orange-50 dark:bg-orange-900/20 border-l-4 border-orange-500 p-3 rounded"
              >
                <p className="font-medium text-sm mb-1">{debate.topic}</p>
                {debate.positions && (
                  <p className="text-sm text-gray-700 dark:text-gray-300">
                    {debate.positions}
                  </p>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Chairman's Synthesis */}
      <div>
        <h4 className="text-lg font-semibold text-purple-700 dark:text-purple-400 mb-2">
          Chairman's Synthesis
        </h4>
        <div className="bg-purple-50 dark:bg-purple-900/20 border-l-4 border-purple-500 p-4 rounded">
          <div className="prose dark:prose-invert max-w-none text-sm whitespace-pre-wrap">
            {synthesis.text}
          </div>
        </div>
      </div>
    </div>
  );
}
