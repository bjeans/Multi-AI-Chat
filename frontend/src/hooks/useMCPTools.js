import { useState, useEffect, useCallback } from 'react';

export function useMCPTools() {
  const [mcpTools, setMcpTools] = useState([]);
  const [serverLabels, setServerLabels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchTools = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch('/api/config/mcp-tools');
      if (!response.ok) {
        if (response.status === 404) {
          // MCP tools endpoint might not be available
          setMcpTools([]);
          setServerLabels([]);
          return;
        }
        throw new Error('Failed to fetch MCP tools');
      }
      const data = await response.json();
      setMcpTools(data);
      
      // Extract unique server labels
      const labels = [...new Set(data.map(tool => tool.server_label).filter(Boolean))];
      setServerLabels(labels);
    } catch (err) {
      setError(err.message);
      setMcpTools([]);
      setServerLabels([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTools();
  }, [fetchTools]);

  return { 
    mcpTools, 
    serverLabels, 
    loading, 
    error, 
    refetch: fetchTools,
    hasTools: mcpTools.length > 0,
  };
}
