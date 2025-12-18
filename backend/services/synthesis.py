from typing import List, Dict, Tuple
from services.litellm_client import LiteLLMClient


class SynthesisService:
    """Service for generating synthesis from council responses"""

    def __init__(self, litellm_client: LiteLLMClient):
        self.client = litellm_client

    async def generate_synthesis(
        self,
        query: str,
        responses: Dict[str, str],
        chairman_model: str,
    ) -> Tuple[List[str], List[dict], str]:
        """
        Generate synthesis using the chairman model
        Returns: (consensus_items, debates, synthesis_text)
        """
        # Build prompt for chairman to analyze responses
        synthesis_prompt = self._build_synthesis_prompt(query, responses)

        # Get chairman's synthesis
        messages = [{"role": "user", "content": synthesis_prompt}]
        full_synthesis_text = await self.client.get_chat_completion(
            model_id=chairman_model,
            messages=messages,
            temperature=0.3,  # Lower temperature for more focused synthesis
        )

        # Parse synthesis to extract consensus, debates, and synthesis-only text
        consensus_items, debates, synthesis_only_text = self._parse_synthesis(full_synthesis_text)

        return consensus_items, debates, synthesis_only_text

    def _build_synthesis_prompt(self, query: str, responses: Dict[str, str]) -> str:
        """Build the prompt for chairman synthesis"""
        prompt = f"""You are the Chairman of a council of AI models. The council was asked to debate the following question:

QUESTION: {query}

The council members provided the following responses:

"""
        for model_name, response in responses.items():
            prompt += f"\n--- {model_name} ---\n{response}\n"

        prompt += """
As Chairman, your task is to synthesize these responses. Please provide:

1. **CONSENSUS**: List the key points where all or most council members agree. Start each point with "• "

2. **DEBATES**: List the key points where council members disagree or take different approaches. For each debate, explain the different positions. Start each point with "• "

3. **SYNTHESIS**: Provide your final synthesis that incorporates the council's collective wisdom, acknowledges the debates, and offers a balanced conclusion.

Format your response EXACTLY as follows:

CONSENSUS:
• [consensus point 1]
• [consensus point 2]
...

DEBATES:
• [debate topic]: [model A's position] vs [model B's position]
• [debate topic]: [different perspectives]
...

SYNTHESIS:
[Your final synthesis statement incorporating the above]
"""
        return prompt

    def _parse_synthesis(self, synthesis_text: str) -> Tuple[List[str], List[dict], str]:
        """
        Parse synthesis text to extract consensus items, debates, and synthesis-only text
        Returns: (consensus_items, debates, synthesis_only_text)
        """
        consensus_items = []
        debates = []
        synthesis_lines = []

        lines = synthesis_text.split("\n")
        current_section = None

        for line in lines:
            line_stripped = line.strip()

            # Detect sections
            if line_stripped.upper().startswith("CONSENSUS"):
                current_section = "consensus"
                continue
            elif line_stripped.upper().startswith("DEBATES"):
                current_section = "debates"
                continue
            elif line_stripped.upper().startswith("SYNTHESIS"):
                current_section = "synthesis"
                continue

            # Parse consensus items
            if current_section == "consensus" and line_stripped.startswith("•"):
                item = line_stripped[1:].strip()
                if item:
                    consensus_items.append(item)

            # Parse debate items
            elif current_section == "debates" and line_stripped.startswith("•"):
                item = line_stripped[1:].strip()
                if item:
                    # Try to split debate into topic and positions
                    if ":" in item:
                        topic, positions = item.split(":", 1)
                        debates.append({"topic": topic.strip(), "positions": positions.strip()})
                    else:
                        debates.append({"topic": item, "positions": ""})

            # Collect synthesis section lines (preserve original line for markdown formatting, including blank lines)
            elif current_section == "synthesis":
                synthesis_lines.append(line)

        # Join synthesis lines, preserving formatting
        synthesis_only_text = "\n".join(synthesis_lines).strip()

        return consensus_items, debates, synthesis_only_text
