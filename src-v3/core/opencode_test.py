from pathlib import Path
import json
from typing import Literal, Dict, Any, Optional, Union, TextIO
from pydantic import BaseModel, Field

from core.agents import OpencodeProjectConfig, AgentType
from core.agents.opencode_wrapper import OpenCodeWrapper, OpenCodeConfig


class ToolState(BaseModel):
    model_config = {"extra": "ignore"}
    status: str
    input: Dict[str, Any]
    output: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    time: Optional[Dict[str, int]] = None


class OpenCodePart(BaseModel):
    model_config = {"extra": "ignore"}
    id: Optional[str] = None
    sessionID: Optional[str] = None
    messageID: Optional[str] = None
    type: str  # "step-start", "tool", "text", "step-finish"
    snapshot: Optional[str] = None

    # Tool specific
    tool: Optional[str] = None
    callID: Optional[str] = None
    state: Optional[ToolState] = None

    # Text specific
    text: Optional[str] = None

    # Step finish specific
    reason: Optional[str] = None
    cost: Optional[float] = None


class OpenCodeEvent(BaseModel):
    model_config = {"extra": "ignore"}
    type: str  # "step_start", "tool_use", "text", "step_finish", "error"
    timestamp: int
    sessionID: str
    part: Optional[OpenCodePart] = None
    error: Optional[Dict[str, Any]] = None


# Default: all agents, all skills
config = OpencodeProjectConfig()
config.apply(Path("./tmp/kubernetes"))

wrapper = OpenCodeWrapper(
    working_dir=Path("./tmp/kubernetes"),
    config=OpenCodeConfig(
        model="openrouter/google/gemini-3-flash-preview",
        verbose=True,
    ),
    project_config=config,
)

# Open output file for raw JSON events
output_file = open("output2.txt", "w")


def stream_callback(line: str) -> None:
    try:
        # Always write raw JSON to file
        output_file.write(line)
        output_file.flush()

        data = json.loads(line)
        event = OpenCodeEvent(**data)

        # 1. Log Messages (in green, full line)
        if event.type == "text" and event.part and event.part.text:
            print(f"\n\033[92m[MESSAGE] {event.part.text}\033[0m")

        # 2. Log Tool Calls (in blue), Subagent Calls (in yellow) (full line)
        elif event.type == "tool_use" and event.part and event.part.tool:
            tool_name = event.part.tool
            tool_input = event.part.state.input if (
                event.part.state and event.part.state.input) else {}

            # Subagent Calls (in yellow)
            if "agent" in tool_name.lower() or tool_name == "task":
                display_name = tool_name
                if tool_name == "task" and "subagent_type" in tool_input:
                    display_name = f"{tool_name} ({tool_input['subagent_type']})"

                print(f"\n\033[93m[SUBAGENT CALL] {display_name}\033[0m")
                print(
                    f"\033[93mParams: {json.dumps(tool_input, indent=2)}\033[0m"
                )
            else:
                # Tool Calls (in blue)
                print(f"\n\033[94m[TOOL CALL] {tool_name}\033[0m")
                print(
                    f"\033[94mParams: {json.dumps(tool_input, indent=2)}\033[0m"
                )

    except Exception as e:
        # Fallback for non-JSON lines or parsing errors
        print(f"\033[91mError parsing line: {e}\033[0m")
        pass


# Uncomment to run live
try:
    print("Starting execution...\n")
    print(
        f"Raw JSON events will be saved to: {Path('output2.txt').resolve()}\n")

    response = wrapper.execute(
        prompt="Analyze this repository and provide a comprehensive markdown summary of its structure, then, generate a documentation for the repository, use a subagent for this, and write the summary in a file called docs.md",
        agent_type=AgentType.EXPLORATION,
        stream_output=False,
        stream_callback=stream_callback,
    )
finally:
    output_file.close()
    print(f"\n✓ Raw JSON events saved to output2.txt")


# # Parse the output file for testing
# if Path("output.txt").exists():
#     print("Reading from output.txt...")
#     with open("output.txt", "r") as f:
#         for line in f:
#             stream_callback(line)
