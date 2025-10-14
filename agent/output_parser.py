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

        # Use a more specific regex to find the action and action input.
        # This looks for "Action:" followed by the tool name on the same line.
        includes_answer = "Final Answer:" in text
        if includes_answer:
            return AgentFinish({"output": text.split("Final Answer:")[-1].strip()}, text)

        action_match = re.search(r"Action:\s*([a-zA-Z0-9_]+)", text)
        if not action_match:
            print("DEBUG: No 'Action:' found. Falling back to default parser.")
            return super().parse(text)

        action = action_match.group(1).strip()
        action_input_start = text.find("Action Input:")
        if action_input_start == -1:
            print("DEBUG: No 'Action Input:' found. Falling back to default parser.")
            return super().parse(text)

        action_input_str = text[action_input_start + len("Action Input:"):].strip()
        print(f"DEBUG: Found Action: '{action}'")
        print(f"DEBUG: Found Raw Action Input: '{action_input_str}'")

        # Regex to find the JSON block. It looks for the first '{' and the last '}'
        json_match = re.search(r"\{.*\}", action_input_str, re.DOTALL)
        if not json_match:
            print("DEBUG: No JSON object found in Action Input. Assuming it's a string.")
            return AgentAction(tool=action, tool_input=action_input_str, log=text)

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