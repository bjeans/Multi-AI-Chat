import httpx
import json
import os
from typing import List, AsyncGenerator, Dict, Optional, Any
from dotenv import load_dotenv

load_dotenv()

LITELLM_PROXY_URL = os.getenv("LITELLM_PROXY_URL", "http://localhost:4000")
LITELLM_API_KEY = os.getenv("LITELLM_API_KEY", "")


class MCPTool:
    """Represents an MCP tool from LiteLLM proxy"""
    def __init__(self, name: str, description: str, server_label: str, input_schema: Optional[Dict] = None):
        self.name = name
        self.description = description
        self.server_label = server_label
        self.input_schema = input_schema or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "server_label": self.server_label,
            "input_schema": self.input_schema,
        }


class LiteLLMClient:
    """Client for interacting with LiteLLM proxy"""

    def __init__(self, base_url: str = LITELLM_PROXY_URL, api_key: str = LITELLM_API_KEY):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = httpx.Timeout(120.0, connect=10.0)

    def _get_headers(self) -> Dict[str, str]:
        """Get headers including authorization if API key is set"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            # Also include x-litellm-api-key for MCP endpoints
            headers["x-litellm-api-key"] = self.api_key
        return headers

    async def get_mcp_tools(self) -> List[MCPTool]:
        """Fetch available MCP tools from LiteLLM proxy"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                # Use specific headers for MCP endpoint - try both auth methods
                headers = {"accept": "application/json"}
                if self.api_key:
                    # LiteLLM MCP endpoints use x-litellm-api-key header
                    headers["x-litellm-api-key"] = self.api_key
                    # Also try Authorization header as fallback
                    headers["Authorization"] = f"Bearer {self.api_key}"
                    print(f"MCP tools request: API key present (length: {len(self.api_key)})")
                else:
                    print("MCP tools request: No API key configured")
                
                print(f"MCP tools request URL: {self.base_url}/v1/mcp/tools")
                response = await client.get(
                    f"{self.base_url}/v1/mcp/tools",
                    headers=headers
                )
                response.raise_for_status()
                data = response.json()
                
                tools = []
                # Parse the MCP tools response
                tool_list = data if isinstance(data, list) else data.get("tools", data.get("data", []))
                
                for tool_data in tool_list:
                    tool_name = tool_data.get("name", "")
                    
                    # Extract server label from tool name (format: "ServerLabel-toolname")
                    # or use explicit server_label field if present
                    server_label = tool_data.get("server_label", tool_data.get("mcp_server_name", ""))
                    if not server_label and "-" in tool_name:
                        # Extract server label from tool name prefix
                        server_label = tool_name.split("-", 1)[0]
                    
                    tool = MCPTool(
                        name=tool_name,
                        description=tool_data.get("description", ""),
                        server_label=server_label,
                        input_schema=tool_data.get("input_schema", tool_data.get("inputSchema", {})),
                    )
                    tools.append(tool)
                
                print(f"MCP get_mcp_tools: Found {len(tools)} tools")
                return tools
        except httpx.HTTPStatusError as e:
            print(f"Error fetching MCP tools (HTTP {e.response.status_code}): {e}")
            return []
        except Exception as e:
            print(f"Error fetching MCP tools: {e}")
            return []

    def _build_mcp_tools_payload(self, mcp_config: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build the MCP tools configuration for API requests (type: mcp format)
        
        Note: This format has issues with Ollama models - they output text instead of tool_calls.
        Use _build_function_tools_from_mcp() instead for better compatibility.
        """
        if not mcp_config or not mcp_config.get("enabled"):
            return []
        
        tools = []
        server_labels = mcp_config.get("server_labels", [])
        allowed_tools = mcp_config.get("allowed_tools", [])
        
        if server_labels:
            for label in server_labels:
                tool_config = {
                    "type": "mcp",
                    "server_label": label,
                    "server_url": f"litellm_proxy/mcp/{label}",
                    "require_approval": "never",
                }
                if allowed_tools:
                    tool_config["allowed_tools"] = allowed_tools
                tools.append(tool_config)
        else:
            tool_config = {
                "type": "mcp",
                "server_label": "*",
                "server_url": "litellm_proxy",
                "require_approval": "never",
            }
            if allowed_tools:
                tool_config["allowed_tools"] = allowed_tools
            tools.append(tool_config)
        
        return tools
    
    async def _fetch_mcp_tool_schemas(self, server_labels: List[str]) -> List[Dict[str, Any]]:
        """Fetch actual tool schemas from MCP servers and convert to function format.
        
        This converts MCP tools to OpenAI-compatible function tools format,
        which works properly with all Ollama models.
        """
        tools = []
        try:
            # Fetch tools from /v1/mcp/tools endpoint
            mcp_tools = await self.get_mcp_tools()
            
            print(f"MCP _fetch_mcp_tool_schemas: Processing {len(mcp_tools)} tools, filtering by: {server_labels}")
            
            for tool in mcp_tools:
                # Filter by server label if specified
                if server_labels and tool.server_label not in server_labels:
                    print(f"  Skipping tool {tool.name} (server: {tool.server_label})")
                    continue
                
                # Tool name already includes server label prefix from API
                # (e.g., "MSLearn-microsoft_docs_search")
                tool_name = tool.name
                
                # Ensure input_schema has required structure
                input_schema = tool.input_schema or {}
                if "type" not in input_schema:
                    input_schema["type"] = "object"
                if "properties" not in input_schema:
                    input_schema["properties"] = {}
                
                func_tool = {
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "description": tool.description or f"Tool from {tool.server_label}",
                        "parameters": input_schema,
                    }
                }
                tools.append(func_tool)
                print(f"  Added tool: {tool_name}")
                
            print(f"Fetched {len(tools)} MCP tools as function definitions")
            
        except Exception as e:
            print(f"Error fetching MCP tool schemas: {e}")
        
        return tools
    
    async def _execute_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute an MCP tool via the LiteLLM proxy REST API.
        
        Tool names are formatted as "{server_label}-{tool_name}".
        Uses the /mcp-rest/tools/call endpoint which properly executes MCP tools.
        """
        try:
            # Parse server label from tool name
            if "-" in tool_name:
                parts = tool_name.split("-", 1)
                server_label = parts[0]
                actual_tool_name = parts[1]
            else:
                # Fallback - try to find the tool
                server_label = None
                actual_tool_name = tool_name
            
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                # Use the MCP REST API endpoint for tool execution
                headers = self._get_headers()
                
                # Build payload for /mcp-rest/tools/call endpoint
                payload = {
                    "name": actual_tool_name,
                    "arguments": arguments,
                }
                
                # Add server_name if we have a server label
                if server_label:
                    payload["server_name"] = server_label
                
                url = f"{self.base_url}/mcp-rest/tools/call"
                
                print(f"Executing MCP tool: {tool_name}")
                print(f"  Server: {server_label}, Tool: {actual_tool_name}")
                print(f"  Endpoint: {url}")
                print(f"  Arguments: {json.dumps(arguments)}")
                
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                
                result = response.json()
                
                # Extract result content from MCP response format
                # MCP REST API returns: {"content": [{"type": "text", "text": "..."}], ...}
                if isinstance(result, dict):
                    # Check for structuredContent first (parsed JSON)
                    if "structuredContent" in result:
                        return json.dumps(result["structuredContent"], indent=2)
                    
                    # Otherwise extract from content array
                    if "content" in result:
                        content = result["content"]
                        if isinstance(content, list):
                            # Extract text from content array
                            texts = []
                            for item in content:
                                if isinstance(item, dict) and "text" in item:
                                    texts.append(item["text"])
                                elif isinstance(item, str):
                                    texts.append(item)
                            return "\n".join(texts) if texts else json.dumps(result)
                        return str(content)
                    elif "result" in result:
                        return str(result["result"])
                    return json.dumps(result)
                return str(result)
                
        except httpx.HTTPStatusError as e:
            error_msg = f"Tool execution failed (HTTP {e.response.status_code})"
            try:
                error_detail = e.response.json()
                error_msg += f": {error_detail}"
            except:
                error_msg += f": {e.response.text[:200]}"
            print(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"Tool execution error: {str(e)}"
            print(error_msg)
            return error_msg

    async def get_available_models(self) -> List[Dict[str, any]]:
        """Fetch available models from LiteLLM proxy"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers=self._get_headers()
                )
                response.raise_for_status()
                data = response.json()

                # LiteLLM proxy returns models in OpenAI format
                if "data" in data:
                    return [
                        {
                            "id": model.get("id"),
                            "name": model.get("id"),
                            "available": True,
                            "provider": model.get("owned_by", "unknown"),
                        }
                        for model in data["data"]
                    ]
                return []
        except Exception as e:
            print(f"Error fetching models: {e}")
            return []

    async def test_model(self, model_id: str) -> bool:
        """Test if a model is available and responding"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._get_headers(),
                    json={
                        "model": model_id,
                        "messages": [{"role": "user", "content": "Hi"}],
                        "max_tokens": 5,
                    },
                )
                return response.status_code == 200
        except Exception:
            return False

    async def _stream_responses_api(
        self,
        model_id: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: Optional[int],
        mcp_config: Dict[str, Any],
    ) -> AsyncGenerator[str, None]:
        """
        Stream using /v1/chat/completions with MCP tools converted to function format.
        
        This approach works around LiteLLM's /v1/responses API issues with Ollama models
        by using the standard chat completions endpoint with proper function tools.
        We handle tool execution manually via the MCP server endpoints.
        """
        try:
            # Get server labels from config
            server_labels = mcp_config.get("server_labels", [])
            
            # Fetch MCP tools as function definitions
            function_tools = await self._fetch_mcp_tool_schemas(server_labels)
            
            if not function_tools:
                yield "⚠️ No MCP tools available. Check MCP server configuration.\n\n"
                # Fall back to regular chat
                async for chunk in self._stream_chat_completions(
                    model_id, messages, temperature, max_tokens
                ):
                    yield chunk
                return
            
            # Build conversation messages
            conversation = list(messages)
            max_tool_iterations = 5  # Prevent infinite loops
            iteration = 0
            
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                while iteration < max_tool_iterations:
                    iteration += 1
                    print(f"MCP iteration {iteration}/{max_tool_iterations}")
                    
                    # Use non-streaming for tool detection
                    # (LiteLLM streaming doesn't properly return tool_calls for Ollama models)
                    payload = {
                        "model": model_id,
                        "messages": conversation,
                        "temperature": temperature,
                        "tools": function_tools,
                        "tool_choice": "auto",
                        "stream": False,  # Non-streaming for reliable tool_calls detection
                    }
                    if max_tokens:
                        payload["max_tokens"] = max_tokens
                    
                    print(f"  Sending request to {self.base_url}/v1/chat/completions")
                    response = await client.post(
                        f"{self.base_url}/v1/chat/completions",
                        headers=self._get_headers(),
                        json=payload,
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    if "choices" not in data or len(data["choices"]) == 0:
                        print("  No choices in response")
                        yield "[No response from model]"
                        break
                    
                    choice = data["choices"][0]
                    message = choice.get("message", {})
                    content = message.get("content")
                    tool_calls = message.get("tool_calls", [])
                    finish_reason = choice.get("finish_reason")
                    
                    print(f"  Finish reason: {finish_reason}, has_content: {bool(content)}, tool_calls: {len(tool_calls)}")
                    
                    # Output any content
                    if content:
                        yield content
                    
                    # Check if we have tool calls to execute
                    # Note: Some models return finish_reason="stop" even with tool_calls
                    if tool_calls:
                        print(f"  Executing {len(tool_calls)} tool calls")
                        # Add assistant message with tool calls to conversation
                        assistant_msg = {
                            "role": "assistant",
                            "content": content,
                            "tool_calls": tool_calls,
                        }
                        conversation.append(assistant_msg)
                        
                        # Execute each tool call
                        for tc in tool_calls:
                            func = tc.get("function", {})
                            tool_name = func.get("name", "")
                            tool_id = tc.get("id", "")
                            
                            if not tool_name:
                                continue
                            
                            # Parse arguments
                            try:
                                args_str = func.get("arguments", "{}")
                                arguments = json.loads(args_str) if args_str else {}
                            except json.JSONDecodeError:
                                print(f"  Failed to parse arguments: {args_str}")
                                arguments = {}
                            
                            yield f"\n🔧 **Tool:** `{tool_name}`\n"
                            print(f"  Calling tool: {tool_name} with args: {arguments}")
                            
                            # Execute the tool
                            result = await self._execute_mcp_tool(tool_name, arguments)
                            print(f"  Tool result length: {len(result)}")
                            
                            # Truncate very long results for display
                            display_result = result
                            if len(display_result) > 1500:
                                display_result = display_result[:1500] + "...(truncated)"
                            
                            yield f"📋 **Result:**\n```\n{display_result}\n```\n\n"
                            
                            # Add tool result to conversation
                            tool_msg = {
                                "role": "tool",
                                "tool_call_id": tool_id,
                                "content": result,
                            }
                            conversation.append(tool_msg)
                        
                        # Continue the loop to let the model process tool results
                        continue
                    
                    else:
                        # No tool calls - we're done
                        break
                
                if iteration >= max_tool_iterations:
                    yield "\n⚠️ Maximum tool iterations reached.\n"

        except httpx.HTTPStatusError as e:
            yield f"\n[Error: HTTP {e.response.status_code}]"
        except Exception as e:
            yield f"\n[Error: {str(e)}]"

    async def _stream_chat_completions(
        self,
        model_id: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: Optional[int],
    ) -> AsyncGenerator[str, None]:
        """
        Stream using standard /chat/completions API endpoint (no MCP tools)
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                payload = {
                    "model": model_id,
                    "messages": messages,
                    "temperature": temperature,
                    "stream": True,
                }
                if max_tokens:
                    payload["max_tokens"] = max_tokens

                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers=self._get_headers(),
                    json=payload,
                ) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]

                            if data_str.strip() == "[DONE]":
                                break

                            try:
                                data = json.loads(data_str)
                                if "choices" in data and len(data["choices"]) > 0:
                                    choice = data["choices"][0]
                                    delta = choice.get("delta", {})
                                    if "content" in delta and delta["content"]:
                                        yield delta["content"]
                            except json.JSONDecodeError:
                                continue

        except httpx.HTTPStatusError as e:
            yield f"\n[Error: HTTP {e.response.status_code}]"
        except Exception as e:
            yield f"\n[Error: {str(e)}]"

    async def stream_chat_completion(
        self,
        model_id: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        mcp_config: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat completion from LiteLLM proxy
        Yields individual token chunks as they arrive
        
        Args:
            model_id: The model to use
            messages: Chat messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            mcp_config: MCP tools configuration dict with:
                - enabled: bool - whether to enable MCP tools
                - server_labels: List[str] - specific server labels to use
                - allowed_tools: List[str] - specific tool names to allow
        """
        # Check if MCP is enabled
        mcp_enabled = mcp_config and mcp_config.get("enabled", False)
        
        # Use MCP tool flow if enabled, otherwise regular chat
        if mcp_enabled and mcp_config:
            async for chunk in self._stream_responses_api(
                model_id, messages, temperature, max_tokens, mcp_config
            ):
                yield chunk
        else:
            async for chunk in self._stream_chat_completions(
                model_id, messages, temperature, max_tokens
            ):
                yield chunk

    async def get_chat_completion(
        self,
        model_id: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        mcp_config: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Get complete chat response (non-streaming)
        Used for chairman synthesis
        """
        full_response = ""
        async for chunk in self.stream_chat_completion(
            model_id, messages, temperature, max_tokens, mcp_config
        ):
            full_response += chunk
        return full_response
