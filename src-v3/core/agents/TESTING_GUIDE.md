# OpenCode Test - Output Capture Guide

## Overview

The `opencode_test.py` file has been updated to capture raw JSON events streamed from OpenCode to a file called `output2.txt`. This allows you to analyze the different types of events (tool calls, tasks, etc.) without relying on console output.

## What's Captured

The `output2.txt` file contains **raw JSON events**, one per line, including:

1. **step_start events** - When a new step begins
2. **tool_use events** - When tools are called (e.g., reading files, executing commands)
3. **text events** - When the agent produces text output
4. **step_finish events** - When a step completes
5. **error events** - When errors occur

Each line is a complete JSON object that can be parsed independently.

## Usage

### Running the Test

```bash
python core/opencode_test.py
```

This will:
1. Execute the OpenCode analysis
2. Print formatted output to console (with colors):
   - Green: Messages from the agent
   - Blue: Tool calls
   - Yellow: Subagent calls
3. **Simultaneously** save all raw JSON events to `output2.txt`

### Output Example

Each line in `output2.txt` looks like:
```json
{"type": "tool_use", "timestamp": 1234567890, "sessionID": "session-123", "part": {"tool": "read_file", "state": {"status": "running", "input": {"path": "/some/file.py"}}}}
{"type": "text", "timestamp": 1234567891, "sessionID": "session-123", "part": {"text": "Found important function..."}}
{"type": "step_finish", "timestamp": 1234567892, "sessionID": "session-123", "part": {"reason": "completed"}}
```

## Event Types

### 1. **step_start** - Step Initialization
```json
{
  "type": "step_start",
  "timestamp": 1234567890,
  "sessionID": "session-123",
  "part": {
    "id": "step-1",
    "type": "step-start"
  }
}
```

### 2. **tool_use** - Tool Invocation
```json
{
  "type": "tool_use",
  "timestamp": 1234567891,
  "sessionID": "session-123",
  "part": {
    "tool": "bash",
    "callID": "call-456",
    "state": {
      "status": "running|success|error",
      "input": {
        "command": "ls -la"
      },
      "output": "file1.txt file2.txt",
      "metadata": {}
    }
  }
}
```

### 3. **text** - Text Output
```json
{
  "type": "text",
  "timestamp": 1234567892,
  "sessionID": "session-123",
  "part": {
    "text": "I found the following structure..."
  }
}
```

### 4. **step_finish** - Step Completion
```json
{
  "type": "step_finish",
  "timestamp": 1234567893,
  "sessionID": "session-123",
  "part": {
    "reason": "completed|error|timeout",
    "cost": 0.025
  }
}
```

## Analyzing output2.txt

### Key Differentiators: Tool Calls vs Tasks

The raw JSON allows you to clearly distinguish:

**Tool Calls** (events where `part.tool` is present):
```json
{
  "type": "tool_use",
  "part": {
    "tool": "read_file",  // or "bash", "write_file", etc.
    "state": {
      "status": "running|success|error",
      "input": {...},
      "output": "..."
    }
  }
}
```

**Tasks/Text Output** (events where `part.text` is present):
```json
{
  "type": "text",
  "part": {
    "text": "..."  // The agent's reasoning or analysis
  }
}
```

### Sample Analysis Script

To analyze the events, you can use this Python snippet:

```python
import json
from collections import defaultdict

# Count event types
event_counts = defaultdict(int)
tool_usage = defaultdict(int)

with open("output2.txt", "r") as f:
    for line in f:
        try:
            event = json.loads(line)
            event_counts[event["type"]] += 1

            # Track tool usage
            if event.get("type") == "tool_use" and event.get("part"):
                tool = event["part"].get("tool")
                if tool:
                    tool_usage[tool] += 1

        except json.JSONDecodeError:
            continue

print("Event Type Breakdown:")
for event_type, count in sorted(event_counts.items()):
    print(f"  {event_type}: {count}")

print("\nTool Usage Breakdown:")
for tool, count in sorted(tool_usage.items()):
    print(f"  {tool}: {count}")
```

### Filtering Events by Type

To extract only tool calls:
```bash
grep '"type": "tool_use"' output2.txt | jq '.'
```

To extract only text events:
```bash
grep '"type": "text"' output2.txt | jq '.'
```

To see which tools were used:
```bash
grep '"type": "tool_use"' output2.txt | jq '.part.tool' | sort | uniq -c
```

## File Information

- **Location**: `output2.txt` (created in the current working directory)
- **Format**: Newline-delimited JSON (NDJSON)
- **Size**: Grows with each event streamed from OpenCode
- **Flushing**: Each event is flushed immediately to disk for safety

## Key Changes to opencode_test.py

1. **File Opening** (line 63):
   ```python
   output_file = open("output2.txt", "w")
   ```

2. **Raw Event Capture** (lines 68-70):
   ```python
   # Always write raw JSON to file
   output_file.write(line)
   output_file.flush()
   ```

3. **Safe Cleanup** (lines 105-117):
   ```python
   try:
       # ... execution code
   finally:
       output_file.close()
       print(f"\n✓ Raw JSON events saved to output2.txt")
   ```

## Tips for Debugging

1. **Check event count**:
   ```bash
   wc -l output2.txt
   ```

2. **Validate JSON**:
   ```bash
   jq empty output2.txt && echo "Valid JSON"
   ```

3. **Find errors**:
   ```bash
   grep '"type": "error"' output2.txt | jq '.'
   ```

4. **Check tool status**:
   ```bash
   grep '"status": "error"' output2.txt | jq '.'
   ```

## Next Steps

With this raw event data, you can:
- Build metrics on tool usage patterns
- Identify bottlenecks in task execution
- Analyze the sequence of tool calls vs reasoning steps
- Detect when agents use subagents vs direct tools
- Create performance reports with actual timestamps

This data is the foundation for understanding how agents differ in their approach to tasks.
