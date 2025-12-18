import asyncio
import time
import json
from typing import List, Dict, AsyncGenerator, Optional, Any
from services.litellm_client import LiteLLMClient
from services.synthesis import SynthesisService
from services.db import DecisionService, get_db


class CouncilOrchestrator:
    """Orchestrates concurrent LLM council debates with streaming responses"""

    def __init__(self):
        self.litellm_client = LiteLLMClient()
        self.synthesis_service = SynthesisService(self.litellm_client)

    async def run_council_debate(
        self,
        query: str,
        council_members: List[str],
        chairman: str,
        mcp_config: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Run a council debate with streaming responses
        Yields SSE events as JSON strings
        
        Args:
            query: The question to debate
            council_members: List of model IDs
            chairman: Model ID for synthesis
            mcp_config: Optional MCP tools configuration
        """
        # Validate minimum council size
        if len(council_members) < 2:
            yield self._create_event("error", {"message": "Need at least 2 council members for debate"})
            return

        # Chairman is separate and only used for synthesis
        # Don't add chairman to council_members

        # Create decision in database
        async with get_db() as db:
            decision = await DecisionService.create_decision(db, query, chairman)
            decision_id = decision.id

        # Yield debate start event with MCP info
        debate_start_data = {
            "decision_id": decision_id,
            "query": query,
            "council_members": council_members,
            "chairman": chairman,
        }
        if mcp_config and mcp_config.get("enabled"):
            debate_start_data["mcp_enabled"] = True
        yield self._create_event("debate_start", debate_start_data)

        # Create a queue for streaming events
        event_queue = asyncio.Queue()

        # Track completed models
        completed_models = set()

        # Start all model tasks
        tasks = []
        for model_id in council_members:
            task = asyncio.create_task(
                self._stream_model_response(model_id, query, decision_id, event_queue, mcp_config)
            )
            tasks.append((model_id, task))

        # Stream events from queue while models are running
        all_tasks_done = False
        while not all_tasks_done or not event_queue.empty():
            try:
                # Wait for event with timeout
                event = await asyncio.wait_for(event_queue.get(), timeout=0.1)
                yield event
            except asyncio.TimeoutError:
                # Check if all tasks are done
                all_tasks_done = all(task.done() for _, task in tasks)
                continue

        # Wait for all tasks to complete and collect any errors
        for model_id, task in tasks:
            try:
                await task
                completed_models.add(model_id)
            except Exception as e:
                yield self._create_event("model_error", {
                    "model_id": model_id,
                    "error": str(e),
                })

        # Get all responses from database for synthesis
        async with get_db() as db:
            responses = await DecisionService.get_responses_for_decision(db, decision_id)
            if len(responses) < 2:
                yield self._create_event("error", {
                    "message": "Not enough models responded successfully for synthesis"
                })
                return

            responses_dict = {
                resp.model_name: resp.response_text
                for resp in responses
            }

        # Generate synthesis
        yield self._create_event("synthesis_start", {"chairman": chairman})

        try:
            consensus_items, debates, synthesis_text = await self.synthesis_service.generate_synthesis(
                query, responses_dict, chairman
            )

            # Save synthesis to database
            async with get_db() as db:
                await DecisionService.add_synthesis(
                    db,
                    decision_id,
                    consensus_items,
                    debates,
                    synthesis_text,
                )

            yield self._create_event("synthesis_complete", {
                "consensus_items": consensus_items,
                "debates": debates,
                "synthesis_text": synthesis_text,
            })

        except Exception as e:
            yield self._create_event("synthesis_error", {
                "error": f"Synthesis failed: {str(e)}"
            })

        # Final event
        yield self._create_event("debate_complete", {"decision_id": decision_id})

    async def _stream_model_response(
        self,
        model_id: str,
        query: str,
        decision_id: int,
        event_queue: asyncio.Queue,
        mcp_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Stream response from a single model in real-time
        Puts events into the queue as they happen
        
        Args:
            model_id: The model to query
            query: The user's question
            decision_id: Database decision ID
            event_queue: Queue for streaming events
            mcp_config: Optional MCP tools configuration
        """
        start_time = time.time()
        full_response = ""
        token_count = 0

        # Send start event
        await event_queue.put(self._create_event("model_start", {"model_id": model_id}))

        messages = [{"role": "user", "content": query}]

        try:
            async for chunk in self.litellm_client.stream_chat_completion(
                model_id=model_id,
                messages=messages,
                mcp_config=mcp_config,
            ):
                full_response += chunk
                token_count += 1

                # Stream chunk event immediately
                await event_queue.put(self._create_event("model_chunk", {
                    "model_id": model_id,
                    "chunk": chunk,
                }))

            response_time = time.time() - start_time

            # Save response to database
            async with get_db() as db:
                await DecisionService.add_response(
                    db,
                    decision_id,
                    model_id,
                    full_response,
                    token_count,
                    response_time,
                )

            # Send completion event
            await event_queue.put(self._create_event("model_complete", {
                "model_id": model_id,
                "response_time": response_time,
                "tokens": token_count,
            }))

        except Exception as e:
            await event_queue.put(self._create_event("model_error", {
                "model_id": model_id,
                "error": str(e),
            }))

    def _create_event(self, event_type: str, data: dict) -> str:
        """Create an SSE event string"""
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
