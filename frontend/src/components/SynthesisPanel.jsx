import ReactMarkdown from 'react-markdown';

export default function SynthesisPanel({ synthesis }) {
  if (!synthesis) {
    return (
      <div className="card">
        <h3 className="text-xl font-bold mb-4 text-gray-900 dark:text-gray-100">Synthesis</h3>
        <p className="text-gray-500 dark:text-gray-400 italic">
          Synthesis will appear here after all council members respond...
        </p>
      </div>
    );
  }

  if (synthesis.status === 'generating') {
    return (
      <div className="card">
        <h3 className="text-xl font-bold mb-4 text-gray-900 dark:text-gray-100">Synthesis</h3>
        <div className="flex items-center space-x-2">
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
          <p className="text-blue-600 dark:text-blue-400">Chairman is synthesizing responses...</p>
        </div>
      </div>
    );
  }

  if (synthesis.status === 'error') {
    return (
      <div className="card">
        <h3 className="text-xl font-bold mb-4 text-gray-900 dark:text-gray-100">Synthesis</h3>
        <p className="text-red-600 dark:text-red-400">{synthesis.error}</p>
      </div>
    );
  }

  return (
    <div className="card space-y-6">
      <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100">Synthesis</h3>

      {/* Consensus Section */}
      {synthesis.consensus && synthesis.consensus.length > 0 && (
        <div>
          <h4 className="text-lg font-semibold text-green-600 dark:text-green-400 mb-2">
            ✓ Consensus
          </h4>
          <ul className="space-y-2">
            {synthesis.consensus.map((item, idx) => (
              <li
                key={idx}
                className="bg-green-100 dark:bg-green-900/20 border-l-4 border-green-500 p-3 rounded"
              >
                <div className="text-sm text-gray-700 dark:text-gray-300 prose dark:prose-invert prose-sm max-w-none">
                  <ReactMarkdown>{item}</ReactMarkdown>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Debates Section */}
      {synthesis.debates && synthesis.debates.length > 0 && (
        <div>
          <h4 className="text-lg font-semibold text-orange-600 dark:text-orange-400 mb-2">
            ⚡ Debates
          </h4>
          <ul className="space-y-2">
            {synthesis.debates.map((debate, idx) => (
              <li
                key={idx}
                className="bg-orange-100 dark:bg-orange-900/20 border-l-4 border-orange-500 p-3 rounded"
              >
                <div className="font-medium text-sm mb-1 text-gray-800 dark:text-gray-200 prose dark:prose-invert prose-sm max-w-none">
                  <ReactMarkdown>{debate.topic}</ReactMarkdown>
                </div>
                {debate.positions && (
                  <div className="text-sm text-gray-700 dark:text-gray-300 prose dark:prose-invert prose-sm max-w-none">
                    <ReactMarkdown>{debate.positions}</ReactMarkdown>
                  </div>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Chairman's Synthesis */}
      <div>
        <h4 className="text-lg font-semibold text-purple-600 dark:text-purple-400 mb-2">
          Chairman's Synthesis
        </h4>
        <div className="bg-purple-100 dark:bg-purple-900/20 border-l-4 border-purple-500 p-4 rounded">
          <div className="prose dark:prose-invert prose-sm max-w-none text-gray-900 dark:text-gray-100">
            <ReactMarkdown>{synthesis.text}</ReactMarkdown>
          </div>
        </div>
      </div>
    </div>
  );
}
