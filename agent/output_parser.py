# agent/output_parser.py
import json
import re
import sys
from typing import Union
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.exceptions import OutputParserException
from langchain.agents.output_parsers.react_single_input import ReActSingleInputOutputParser

class CustomOutputParser(ReActSingleInputOutputParser):
    """A robust parser for ReAct agents that handles malformed JSON and trailing text."""
    def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        sys.stdout.write("\n\n✅✅✅ ROBUST PARSER EXECUTED ✅✅✅\n\n")
        sys.stdout.write(f"--- RAW AGENT OUTPUT ---\n{text}\n----------------------\n")
        sys.stdout.flush()

        if "Final Answer:" in text:
            output = text.split("Final Answer:")[-1].strip()
            return AgentFinish(return_values={"output": output}, log=text)

        action_match = re.search(r"Action:\s*([a-zA-Z0-9_]+)", text)
        action_input_match = re.search(r"Action Input:(.*)", text, re.DOTALL)

        if not action_match or not action_input_match:
            raise OutputParserException(f"Could not parse action or action input from text: {text}")

        action = action_match.group(1).strip()
        action_input_raw = action_input_match.group(1).strip()

        json_match = re.search(r"\{.*\}", action_input_raw, re.DOTALL)
        if not json_match:
            raise OutputParserException(f"Could not find a JSON object in the action input: {action_input_raw}")

        json_str = json_match.group(0)
        try:
            tool_input = json.loads(json_str)
            return AgentAction(tool=action, tool_input=tool_input, log=text)
        except json.JSONDecodeError as e:
            raise OutputParserException(f"Failed to decode JSON: {e}. Raw JSON: {json_str}")