#!/usr/bin/env python3
"""
Repository Documentation TUI

A terminal user interface for documenting repositories using the multi-agent
documentation system powered by OpenCode.

Usage:
    python src-v3/document_repo.py /path/to/repository
    python src-v3/document_repo.py /path/to/repository --model sonnet
    python src-v3/document_repo.py /path/to/repository --verbose
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, TextIO

from pydantic import BaseModel

from core.agents import AgentType
from core.documentation_pipeline import DocumentationPipeline
from core.utils.clone_repo import clone_repo, is_github_url


# ============================================================================
# Event Models
# ============================================================================


class ToolState(BaseModel):
    model_config = {"extra": "ignore"}
    status: str
    input: dict
    output: Optional[str] = None
    metadata: Optional[dict] = None
    time: Optional[dict] = None


class OpenCodePart(BaseModel):
    model_config = {"extra": "ignore"}
    id: Optional[str] = None
    sessionID: Optional[str] = None
    messageID: Optional[str] = None
    type: str
    snapshot: Optional[str] = None
    tool: Optional[str] = None
    callID: Optional[str] = None
    state: Optional[ToolState] = None
    text: Optional[str] = None
    reason: Optional[str] = None
    cost: Optional[float] = None


class OpenCodeEvent(BaseModel):
    model_config = {"extra": "ignore"}
    type: str
    timestamp: int
    sessionID: str
    part: Optional[OpenCodePart] = None
    error: Optional[dict] = None


# ============================================================================
# ANSI Color Codes
# ============================================================================


class Colors:
    """ANSI color codes for terminal output."""

    # Text colors
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"

    # Background colors
    BG_RED = "\033[101m"
    BG_GREEN = "\033[102m"
    BG_YELLOW = "\033[103m"
    BG_BLUE = "\033[104m"
    BG_MAGENTA = "\033[105m"
    BG_CYAN = "\033[106m"

    @staticmethod
    def strip(text: str) -> str:
        """Remove ANSI color codes from text."""
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)


# ============================================================================
# TUI Logger
# ============================================================================


class DocumentationTUI:
    """Terminal UI for repository documentation."""

    def __init__(self, repo_path: Path, log_file: TextIO, verbose: bool = False):
        self.repo_path = repo_path
        self.log_file = log_file
        self.verbose = verbose
        self.event_count = 0
        self.tool_count = 0
        self.subagent_count = 0
        self.message_count = 0
        self.current_step = ""

    def print_header(self):
        """Print TUI header."""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}   Multi-Agent Repository Documentation System{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}\n")
        print(f"{Colors.BOLD}Repository:{Colors.RESET} {self.repo_path}")
        print(f"{Colors.BOLD}Log File:{Colors.RESET}   {self.log_file.name}")
        print(f"{Colors.BOLD}Started:{Colors.RESET}    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        print(f"{Colors.CYAN}{'─'*80}{Colors.RESET}\n")

    def print_footer(self, pipeline_result: Optional[dict] = None):
        """Print TUI footer with statistics."""
        print(f"\n{Colors.CYAN}{'─'*80}{Colors.RESET}\n")
        print(f"{Colors.BOLD}{Colors.GREEN}✓ Documentation Complete{Colors.RESET}\n")
        print(f"{Colors.BOLD}Statistics:{Colors.RESET}")
        print(f"  • Total Events:   {self.event_count}")
        print(f"  • Messages:       {self.message_count}")
        print(f"  • Tool Calls:     {self.tool_count}")
        print(f"  • Subagent Calls: {self.subagent_count}")

        # Check if docs directories exist - everything is in planning/
        main_index = self.repo_path / 'planning' / 'index.md'
        component_docs_path = self.repo_path / 'planning' / 'docs'
        planning_overview = self.repo_path / 'planning' / 'overview.md'

        # HTML output is in build/site (from post-processor)
        build_site_dir = self.repo_path / 'build' / 'site'

        # Get HTML path from pipeline result if available
        html_output_dir = None
        if pipeline_result and 'steps' in pipeline_result:
            post_process = pipeline_result['steps'].get('post_process', {})
            if post_process.get('html_output_dir'):
                html_output_dir = Path(post_process['html_output_dir'])

        # Fall back to default location
        if not html_output_dir:
            html_output_dir = build_site_dir

        print(f"\n{Colors.BOLD}Generated Documentation:{Colors.RESET}")
        print(f"  • Main Index:     {main_index} {'✓' if main_index.exists() else '(not created)'}")
        print(f"  • Overview:       {planning_overview} {'✓' if planning_overview.exists() else '(not created)'}")
        print(f"  • Component Docs: {component_docs_path}/")
        print(f"  • HTML Site:      {html_output_dir}/ {'✓' if html_output_dir.exists() else '(not built)'}")
        print(f"  • Event Log:      {self.log_file.name}")

        # Display component documentation structure using tree
        if component_docs_path.exists():
            print(f"\n{Colors.BOLD}Component Documentation:{Colors.RESET}")
            print(f"{Colors.DIM}Location: {component_docs_path}{Colors.RESET}\n")

            import subprocess
            try:
                # Try to run tree command on component docs
                tree_output = subprocess.run(
                    ['tree', '-L', '2', '-F', '--dirsfirst', str(component_docs_path)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if tree_output.returncode == 0:
                    # Colorize the tree output
                    for line in tree_output.stdout.split('\n'):
                        if line.strip():
                            print(f"{Colors.DIM}{line}{Colors.RESET}")
                else:
                    # Fallback: use ls if tree fails
                    self._print_simple_tree(component_docs_path)

            except (subprocess.TimeoutExpired, FileNotFoundError):
                # tree command not available - use simple fallback
                self._print_simple_tree(component_docs_path)

        # Display main index if created
        if main_index.exists():
            print(f"\n{Colors.BOLD}{Colors.GREEN}✓ Main Index Created:{Colors.RESET}")
            print(f"{Colors.DIM}  {main_index}{Colors.RESET}")
        else:
            print(f"\n{Colors.YELLOW}⚠ Main index (planning/index.md) not created{Colors.RESET}")
            print(f"{Colors.DIM}  Browse component docs at: {component_docs_path}/{Colors.RESET}")

        # Display site info if built
        if html_output_dir and html_output_dir.exists():
            print(f"\n{Colors.BOLD}{Colors.GREEN}✓ HTML Site Built:{Colors.RESET}")
            print(f"  {Colors.BOLD}Path:{Colors.RESET} {html_output_dir}")
            print(f"{Colors.DIM}  To view: cd {html_output_dir} && python3 -m http.server 8080{Colors.RESET}")
            print(f"{Colors.DIM}  Then open: http://localhost:8080{Colors.RESET}")

        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}\n")

    def _print_simple_tree(self, docs_path: Path):
        """Simple fallback for displaying directory structure when tree is not available."""
        print(f"{docs_path.name}/")

        # List directories first, then files
        items = list(docs_path.iterdir())
        dirs = sorted([item for item in items if item.is_dir()])
        files = sorted([item for item in items if item.is_file()])

        for item in dirs:
            print(f"├── {item.name}/")
            # Show first level of subdirectories
            subitems = list(item.iterdir())
            subdirs = sorted([si for si in subitems if si.is_dir()])
            subfiles = sorted([si for si in subitems if si.is_file()])

            count = len(subdirs) + len(subfiles)
            for i, subitem in enumerate(subdirs + subfiles):
                is_last = i == count - 1
                prefix = "└──" if is_last else "├──"
                suffix = "/" if subitem.is_dir() else ""
                print(f"│   {prefix} {subitem.name}{suffix}")

        for i, item in enumerate(files):
            is_last = i == len(files) - 1 and not dirs
            prefix = "└──" if is_last else "├──"
            print(f"{prefix} {item.name}")

    def log_event(self, event_type: str, message: str, color: str = Colors.RESET):
        """Log a single-line event with color coding."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        # Create single-line output
        event_line = f"{Colors.GRAY}[{timestamp}]{Colors.RESET} {color}{event_type:15s}{Colors.RESET} {message}"
        print(event_line)

    def handle_event(self, line: str) -> None:
        """
        Handle a single event from OpenCode stream.

        Args:
            line: JSON string from OpenCode event stream
        """
        # Always write raw line to log file (even if not JSON)
        self.log_file.write(line)
        if not line.endswith('\n'):
            self.log_file.write('\n')
        self.log_file.flush()

        # In verbose mode, also print raw line to console
        if self.verbose:
            print(f"{Colors.DIM}RAW: {line[:120]}{Colors.RESET}")

        try:
            # Try to parse as JSON event
            data = json.loads(line)
            event = OpenCodeEvent(**data)
            self.event_count += 1

            # Handle different event types
            if event.type == "step_start":
                self._handle_step_start(event)
            elif event.type == "text" and event.part and event.part.text:
                self._handle_message(event)
            elif event.type == "tool_use" and event.part and event.part.tool:
                self._handle_tool_call(event)
            elif event.type == "step_finish":
                self._handle_step_finish(event)
            elif event.type == "error":
                self._handle_error(event)
            else:
                # Log other event types in verbose mode
                if self.verbose:
                    self.log_event("OTHER EVENT", f"type={event.type}", Colors.GRAY)

        except json.JSONDecodeError:
            # Not JSON - log non-JSON output to console for debugging
            stripped = line.strip()
            if stripped and self.verbose:
                self.log_event("NON-JSON", stripped[:80], Colors.YELLOW)
        except Exception as e:
            # Log parsing errors
            if self.verbose:
                self.log_event("PARSE ERROR", f"{str(e)[:50]}", Colors.RED)

    def _handle_step_start(self, event: OpenCodeEvent) -> None:
        """Handle step start event."""
        if event.part and event.part.snapshot:
            self.current_step = event.part.snapshot
            self.log_event(
                "STEP START",
                f"{Colors.BOLD}{event.part.snapshot}{Colors.RESET}",
                Colors.MAGENTA
            )

    def _handle_message(self, event: OpenCodeEvent) -> None:
        """Handle text message event."""
        if not event.part or not event.part.text:
            return

        self.message_count += 1

        # Truncate long messages to single line
        message = event.part.text.replace('\n', ' ').strip()
        if len(message) > 65:
            message = message[:62] + "..."

        self.log_event("MESSAGE", message, Colors.GREEN)

    def _handle_tool_call(self, event: OpenCodeEvent) -> None:
        """Handle tool use event."""
        if not event.part or not event.part.tool:
            return

        tool_name = event.part.tool
        tool_input = event.part.state.input if event.part.state and event.part.state.input else {}

        # Check if this is a subagent call
        is_subagent = "agent" in tool_name.lower() or tool_name == "task"

        if is_subagent:
            self.subagent_count += 1
            self._handle_subagent_call(tool_name, tool_input)
        else:
            self.tool_count += 1
            self._handle_regular_tool(tool_name, tool_input)

    def _handle_subagent_call(self, tool_name: str, tool_input: dict) -> None:
        """Handle subagent spawn event."""
        # Extract subagent type
        if tool_name == "task" and "subagent_type" in tool_input:
            subagent_type = tool_input["subagent_type"]
            description = tool_input.get("description", "")

            # Truncate description
            if len(description) > 50:
                description = description[:47] + "..."

            message = f"{Colors.BOLD}{subagent_type}{Colors.RESET} - {description}"
        else:
            message = f"{Colors.BOLD}{tool_name}{Colors.RESET}"

        self.log_event("SUBAGENT", message, Colors.YELLOW)

    def _handle_regular_tool(self, tool_name: str, tool_input: dict) -> None:
        """Handle regular tool call event."""
        # Build concise tool description
        params = []

        # Common parameter patterns
        if "file_path" in tool_input:
            path = Path(tool_input["file_path"])
            params.append(f"file={path.name}")
        elif "path" in tool_input:
            path = Path(tool_input["path"])
            params.append(f"path={path.name}")

        if "pattern" in tool_input:
            params.append(f"pattern={tool_input['pattern'][:20]}")

        if "command" in tool_input:
            cmd = tool_input["command"]
            if len(cmd) > 30:
                cmd = cmd[:27] + "..."
            params.append(f"cmd={cmd}")

        # Build message
        param_str = ", ".join(params) if params else ""
        message = f"{Colors.BOLD}{tool_name}{Colors.RESET}"
        if param_str:
            message += f" ({param_str})"

        self.log_event("TOOL", message, Colors.BLUE)

    def _handle_step_finish(self, event: OpenCodeEvent) -> None:
        """Handle step finish event."""
        if event.part and event.part.reason:
            reason = event.part.reason
            cost = event.part.cost

            message = f"Reason: {reason}"
            if cost:
                message += f", Cost: ${cost:.4f}"

            self.log_event("STEP FINISH", message, Colors.MAGENTA)

    def _handle_error(self, event: OpenCodeEvent) -> None:
        """Handle error event."""
        error_msg = "Unknown error"
        if event.error:
            error_msg = str(event.error).replace('\n', ' ')[:60]

        self.log_event("ERROR", f"{Colors.BOLD}{error_msg}{Colors.RESET}", Colors.RED)


# ============================================================================
# Main Entry Point
# ============================================================================


def show_subagent_logs(repo_path_or_name: str):
    """Show recent subagent activity from log files."""
    import glob
    import re

    # Find log files
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # Try to find log file based on repo name
    repo_name = Path(repo_path_or_name).name.replace("https://github.com/", "").split("/")[-1]

    log_patterns = [
        project_root / f"{repo_name}.log.txt",
        project_root / "src-v3" / f"{repo_name}.log.txt",
        project_root / "tmp" / repo_name / repo_name / f"{repo_name}.log.txt",
    ]

    log_file = None
    for pattern in log_patterns:
        if pattern.exists():
            log_file = pattern
            break

    # Also check for any recent log files
    if not log_file:
        all_logs = list(project_root.glob("*.log.txt")) + list((project_root / "src-v3").glob("*.log.txt"))
        if all_logs:
            log_file = max(all_logs, key=lambda p: p.stat().st_mtime)

    if not log_file:
        print(f"{Colors.RED}No log files found{Colors.RESET}")
        print(f"Searched in: {project_root}")
        return

    print(f"{Colors.BOLD}Log file:{Colors.RESET} {log_file}")
    print(f"{Colors.BOLD}Last modified:{Colors.RESET} {datetime.fromtimestamp(log_file.stat().st_mtime)}")
    print(f"{Colors.CYAN}{'─'*80}{Colors.RESET}\n")

    # Parse log file and show subagent activity
    sessions = {}
    subagent_calls = []

    with open(log_file) as f:
        for line in f:
            try:
                event = json.loads(line.strip())

                # Track sessions
                session_id = event.get("sessionID", "")
                if session_id not in sessions:
                    sessions[session_id] = {
                        "start": event.get("timestamp"),
                        "events": 0,
                        "tools": [],
                        "status": "running"
                    }
                sessions[session_id]["events"] += 1

                # Track subagent calls
                if event.get("type") == "tool_use":
                    part = event.get("part", {})
                    if part.get("tool") == "task":
                        state = part.get("state", {})
                        input_data = state.get("input", {})
                        subagent_calls.append({
                            "timestamp": event.get("timestamp"),
                            "session": session_id[-8:],
                            "type": input_data.get("subagent_type", "unknown"),
                            "description": input_data.get("description", "")[:50],
                            "status": state.get("status", "unknown")
                        })

                # Track step finishes
                if event.get("type") == "step_finish":
                    part = event.get("part", {})
                    sessions[session_id]["status"] = part.get("reason", "unknown")

            except json.JSONDecodeError:
                continue

    # Show sessions summary
    print(f"{Colors.BOLD}Sessions ({len(sessions)}):{Colors.RESET}")
    for sid, info in sorted(sessions.items(), key=lambda x: x[1].get("start", 0)):
        status_color = Colors.GREEN if info["status"] == "stop" else Colors.YELLOW
        print(f"  {sid[-12:]}: {info['events']} events, status: {status_color}{info['status']}{Colors.RESET}")

    # Show subagent calls
    if subagent_calls:
        print(f"\n{Colors.BOLD}Subagent Calls ({len(subagent_calls)}):{Colors.RESET}")
        for call in subagent_calls[-20:]:  # Show last 20
            status_color = Colors.GREEN if call["status"] == "completed" else Colors.YELLOW
            print(f"  [{call['session']}] {Colors.CYAN}{call['type']}{Colors.RESET}: {call['description']} - {status_color}{call['status']}{Colors.RESET}")

    # Show component docs status
    planning_docs = project_root / "tmp" / repo_name / repo_name / "planning" / "docs"
    if not planning_docs.exists():
        # Try other locations
        for p in project_root.glob(f"tmp/*/{repo_name}/planning/docs"):
            planning_docs = p
            break

    if planning_docs.exists():
        components = [d.name for d in planning_docs.iterdir() if d.is_dir()]
        file_count = sum(1 for d in planning_docs.iterdir() if d.is_dir() for f in d.iterdir() if f.is_file())
        print(f"\n{Colors.BOLD}Component Docs:{Colors.RESET} {len(components)} components, {file_count} files")
        print(f"  {Colors.DIM}{', '.join(sorted(components))}{Colors.RESET}")


def main():
    """Main entry point for repository documentation TUI."""

    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Document a repository using multi-agent system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src-v3/document_repo.py /path/to/repo
  python src-v3/document_repo.py https://github.com/owner/repo
  python src-v3/document_repo.py /path/to/repo --model sonnet
  python src-v3/document_repo.py https://github.com/owner/repo --model sonnet --verbose
  python src-v3/document_repo.py /path/to/repo --agent exploration
        """
    )

    parser.add_argument(
        "repository",
        type=str,
        help="Path to the repository to document, or GitHub URL (https://github.com/owner/repo)"
    )

    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model to use (default: OpenCode default model). Note: Many model IDs may not be registered in OpenCode yet."
    )

    parser.add_argument(
        "--agent",
        type=str,
        default="exploration",
        choices=["exploration", "documentation", "delegator", "section_writer", "overview_writer"],
        help="Starting agent type (default: exploration)"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging (shows all events)"
    )

    parser.add_argument(
        "--logs",
        action="store_true",
        help="Show recent subagent activity from log file (doesn't run pipeline)"
    )

    args = parser.parse_args()

    # Handle --logs option first
    if args.logs:
        show_subagent_logs(args.repository)
        sys.exit(0)

    # Handle GitHub URLs by cloning to tmp/
    repo_input = args.repository
    cloned_from_github = False
    repo_url = None  # Track the GitHub URL for link fixing

    if is_github_url(repo_input):
        print(f"{Colors.CYAN}Detected GitHub URL: {repo_input}{Colors.RESET}")
        print(f"{Colors.CYAN}Cloning to tmp/ directory...{Colors.RESET}\n")

        # Store the GitHub URL for post-processing (link fixing)
        repo_url = repo_input

        try:
            # Clone to project root tmp/, not relative to current directory
            # This ensures tmp/ is at the repo root, not in src-v3/
            script_dir = Path(__file__).parent  # src-v3/
            project_root = script_dir.parent     # repo-explainer/
            tmp_dir = project_root / "tmp"

            repo_path = clone_repo(repo_input, base_tmp_dir=str(tmp_dir), force=False)
            repo_path = repo_path.resolve()  # Convert to absolute path
            cloned_from_github = True
            print(f"{Colors.GREEN}✓ Repository cloned to: {repo_path}{Colors.RESET}\n")
        except Exception as e:
            print(f"{Colors.RED}Error cloning repository: {e}{Colors.RESET}")
            sys.exit(1)
    else:
        # Local path - validate it exists
        repo_path = Path(repo_input).resolve()
        if not repo_path.exists():
            print(f"{Colors.RED}Error: Repository path does not exist: {repo_path}{Colors.RESET}")
            sys.exit(1)

        if not repo_path.is_dir():
            print(f"{Colors.RED}Error: Path is not a directory: {repo_path}{Colors.RESET}")
            sys.exit(1)

        # Try to extract GitHub URL from git remote for local repos
        try:
            import subprocess
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True, text=True, cwd=repo_path, timeout=5
            )
            if result.returncode == 0:
                remote_url = result.stdout.strip()
                # Convert SSH URLs to HTTPS
                if remote_url.startswith("git@github.com:"):
                    remote_url = remote_url.replace("git@github.com:", "https://github.com/")
                if remote_url.endswith(".git"):
                    remote_url = remote_url[:-4]
                if "github.com" in remote_url:
                    repo_url = remote_url
                    print(f"{Colors.DIM}Detected GitHub remote: {repo_url}{Colors.RESET}\n")
        except Exception:
            pass  # Ignore errors - repo_url will remain None

    # Map model shortcuts
    model_map = {
        "sonnet": "anthropic/claude-sonnet-4-5",
        "opus": "anthropic/claude-opus-4-5",
        "haiku": "anthropic/claude-haiku-4-5",
    }
    model = model_map.get(args.model, args.model)

    # Map agent type
    agent_type_map = {
        "exploration": AgentType.EXPLORATION,
        "documentation": AgentType.DOCUMENTATION,
        "delegator": AgentType.DELEGATOR,
        "section_writer": AgentType.SECTION_WRITER,
        "overview_writer": AgentType.OVERVIEW_WRITER,
    }
    agent_type = agent_type_map[args.agent]

    # Setup log file
    repo_name = repo_path.name
    log_file_path = Path(f"{repo_name}.log.txt")
    log_file = open(log_file_path, "w")

    try:
        # Initialize TUI
        tui = DocumentationTUI(repo_path, log_file, verbose=args.verbose)
        tui.print_header()

        # Setup documentation pipeline
        print(f"{Colors.BOLD}Initializing multi-agent system...{Colors.RESET}\n")

        # Create stream callback
        def stream_callback(line: str) -> None:
            tui.handle_event(line)

        # Initialize pipeline
        pipeline = DocumentationPipeline(
            repo_path=repo_path,
            model=model,
            verbose=args.verbose,
            stream_callback=stream_callback,
            repo_url=repo_url
        )

        print(f"{Colors.GREEN}✓ Configuration applied{Colors.RESET}")
        print(f"{Colors.GREEN}✓ Agents initialized{Colors.RESET}")
        print(f"{Colors.GREEN}✓ Starting documentation pipeline...{Colors.RESET}\n")
        print(f"{Colors.CYAN}{'─'*80}{Colors.RESET}\n")

        # Setup and run pipeline
        pipeline.setup()
        result = pipeline.run()

        # Print footer with statistics and pipeline result
        tui.print_footer(pipeline_result=result)

        # Remind user if cloned from GitHub
        if cloned_from_github:
            print(f"{Colors.DIM}Note: Repository was cloned to {repo_path}{Colors.RESET}")
            print(f"{Colors.DIM}To remove: rm -rf {repo_path}{Colors.RESET}\n")

    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⚠ Documentation interrupted by user{Colors.RESET}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n{Colors.RED}✗ Error during documentation: {e}{Colors.RESET}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        log_file.close()
        print(f"{Colors.DIM}Log file closed: {log_file_path}{Colors.RESET}\n")


if __name__ == "__main__":
    main()
