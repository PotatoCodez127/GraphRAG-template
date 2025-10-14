import json
import re
from typing import Union
from langchain.agents.output_parsers import ReActSingleInputOutputParser
from langchain.schema import AgentAction, AgentFinish, OutputParserException

class CustomOutputParser(ReActSingleInputOutputParser):
    """
    A custom output parser that extracts the JSON from the Action Input,
    ignores any trailing text, and adds detailed logging for debugging.
    """
    def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        print("\n--- PARSER INPUT ---\n")
        print(text)
        print("\n--------------------\n")

        # Use a regex to find the action and the start of the action input
        action_match = re.search(r"Action:\s*(.*?)\s*Action Input:", text, re.DOTALL)
        if not action_match:
            print("DEBUG: No 'Action:' or 'Action Input:' found. Falling back to default parser.")
            return super().parse(text)

        action = action_match.group(1).strip()
        action_input_str = text[action_match.end():].strip()
        print(f"DEBUG: Found Action: '{action}'")
        print(f"DEBUG: Found Raw Action Input: '{action_input_str}'")

        # Regex to find the JSON block. It looks for the first '{' and the last '}'
        json_match = re.search(r"\{.*\}", action_input_str, re.DOTALL)
        if not json_match:
            print("DEBUG: No JSON object found in Action Input. Falling back to default parser.")
            return super().parse(text)

        try:
            # Extract and parse only the JSON part
            json_str = json_match.group(0)
            print(f"DEBUG: Extracted JSON string: '{json_str}'")
            tool_input = json.loads(json_str)
            print(f"DEBUG: Successfully parsed JSON: {tool_input}")
            
            print("\n--- PARSER OUTPUT: SUCCESS ---\n")
            return AgentAction(tool=action, tool_input=tool_input, log=text)
        except json.JSONDecodeError as e:
            raise OutputParserException(f"Failed to decode JSON from Action Input: {e}")

        return super().parse(text)