import { useState, useCallback } from 'react';

export function useStreamingDebate() {
  const [debating, setDebating] = useState(false);
  const [decisionId, setDecisionId] = useState(null);
  const [modelResponses, setModelResponses] = useState({});
  const [synthesis, setSynthesis] = useState(null);
  const [error, setError] = useState(null);

  const startDebate = useCallback(async (query, councilMembers, chairman, mcpConfig = null) => {
    setDebating(true);
    setError(null);
    setModelResponses({});
    setSynthesis(null);
    setDecisionId(null);

    // Initialize model responses
    const initialResponses = {};
    councilMembers.forEach(model => {
      initialResponses[model] = {
        model_id: model,
        text: '',
        status: 'pending',
        tokens: 0,
        responseTime: 0,
      };
    });
    setModelResponses(initialResponses);

    try {
      const requestBody = {
        query,
        council_members: councilMembers,
        chairman,
      };

      // Add MCP config if provided and enabled
      if (mcpConfig && mcpConfig.enabled) {
        requestBody.mcp_config = {
          enabled: true,
          server_labels: mcpConfig.serverLabels || [],
          allowed_tools: mcpConfig.allowedTools || [],
        };
      }

      const response = await fetch('/api/council/debate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) throw new Error('Failed to start debate');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.trim()) continue;

          const eventMatch = line.match(/event: (\w+)\ndata: (.+)/);
          if (!eventMatch) continue;

          const [, eventType, dataStr] = eventMatch;
          const data = JSON.parse(dataStr);

          handleEvent(eventType, data);
        }
      }

      setDebating(false);
    } catch (err) {
      setError(err.message);
      setDebating(false);
    }
  }, []);

  const handleEvent = (eventType, data) => {
    switch (eventType) {
      case 'debate_start':
        setDecisionId(data.decision_id);
        break;

      case 'model_start':
        setModelResponses(prev => ({
          ...prev,
          [data.model_id]: {
            ...prev[data.model_id],
            status: 'streaming',
          },
        }));
        break;

      case 'model_chunk':
        setModelResponses(prev => ({
          ...prev,
          [data.model_id]: {
            ...prev[data.model_id],
            text: prev[data.model_id].text + data.chunk,
          },
        }));
        break;

      case 'model_complete':
        setModelResponses(prev => ({
          ...prev,
          [data.model_id]: {
            ...prev[data.model_id],
            status: 'complete',
            tokens: data.tokens,
            responseTime: data.response_time,
          },
        }));
        break;

      case 'model_error':
        setModelResponses(prev => ({
          ...prev,
          [data.model_id]: {
            ...prev[data.model_id],
            status: 'error',
            error: data.error,
          },
        }));
        break;

      case 'synthesis_start':
        setSynthesis({ status: 'generating' });
        break;

      case 'synthesis_complete':
        setSynthesis({
          status: 'complete',
          consensus: data.consensus_items,
          debates: data.debates,
          text: data.synthesis_text,
        });
        break;

      case 'synthesis_error':
        setSynthesis({
          status: 'error',
          error: data.error,
        });
        break;

      case 'error':
        setError(data.message);
        break;

      default:
        break;
    }
  };

  return {
    debating,
    decisionId,
    modelResponses,
    synthesis,
    error,
    startDebate,
  };
}
