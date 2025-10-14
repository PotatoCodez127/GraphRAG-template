import json
import re
from langchain.agents.output_parsers import ReActSingleInputOutputParser
from langchain.schema import AgentAction, AgentFinish, OutputParserException

class CustomOutputParser(ReActSingleInputOutputParser):
    """
    A custom output parser that extracts the JSON from the Action Input
    and ignores any trailing text. This makes the agent more robust to
    LLM formatting errors.
    """
    def parse(self, text: str) -> AgentAction | AgentFinish:
        # Use a regex to find the action and the action input
        action_match = re.search(r"Action:\s*(.*?)\s*Action Input:", text, re.DOTALL)
        if not action_match:
            # If the standard ReAct format isn't present, let the default parser handle it
            return super().parse(text)

        action = action_match.group(1).strip()
        action_input_str = text[action_match.end():].strip()

        # Regex to find the JSON block. It looks for the first '{' and the last '}'
        json_match = re.search(r"\{.*\}", action_input_str, re.DOTALL)
        if not json_match:
            raise OutputParserException(f"Could not parse a valid JSON object from the Action Input: {action_input_str}")

        try:
            # Extract and parse the JSON
            json_str = json_match.group(0)
            tool_input = json.loads(json_str)
            return AgentAction(tool=action, tool_input=tool_input, log=text)
        except json.JSONDecodeError as e:
            raise OutputParserException(f"Failed to decode JSON: {e}")

        return super().parse(text)