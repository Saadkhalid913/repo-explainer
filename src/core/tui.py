"""
Rich TUI for Repository Documentation

A modern split-panel terminal user interface using the Rich library.
Features:
- Top bar showing repository link/path
- Left panel: Real-time scrolling logs (color-coded)
- Right panel: Live docs tree that updates as files are created
- Bottom bar: Statistics with activity indicator
"""

import json
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from threading import Thread
from typing import Callable, Optional, TextIO

from pydantic import BaseModel, ValidationError
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree


# ============================================================================
# Event Models (shared with document_repo.py)
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
# Rich TUI
# ============================================================================

# Spinner frames for activity indicator
SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


class RichTUI:
    """Modern split-panel TUI using Rich library."""

    def __init__(
        self,
        repo_url: str,
        log_file: TextIO,
        verbose: bool = False,
    ):
        self.repo_url = repo_url
        self.repo_path: Optional[Path] = None  # Set after cloning
        self.log_file = log_file
        self.verbose = verbose

        # Log buffer (ring buffer for last N entries)
        self.log_entries: deque[Text] = deque(maxlen=100)

        # Statistics
        self.stats = {"events": 0, "messages": 0, "tools": 0, "subagents": 0}

        # State
        self._watching = False
        self._running = True
        self._completed = False
        self.docs_watcher_thread: Optional[Thread] = None

        # Spinner for activity indicator
        self._spinner_frame = 0
        self._last_activity = time.time()

        # Rich components
        self.console = Console()
        self.layout = self._create_layout()
        self.live: Optional[Live] = None

        # Track current step for context
        self.current_step = ""

        # Pipeline result for completion display
        self.pipeline_result: Optional[dict] = None

    def _create_layout(self) -> Layout:
        """Create the split-panel layout structure."""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3),
        )
        layout["body"].split_row(
            Layout(name="logs", ratio=2),
            Layout(name="docs", ratio=1),
        )
        return layout

    def start(self):
        """Start the TUI with Live context."""
        self.live = Live(
            self.layout,
            console=self.console,
            refresh_per_second=4,
            screen=True,
        )
        self.live.__enter__()
        self._update_display()

    def start_docs_watcher(self):
        """Start the docs directory watcher (call after repo_path is set)."""
        if self.repo_path and not self._watching:
            self._start_docs_watcher()

    def stop(self):
        """Stop the TUI."""
        self._running = False
        self._stop_docs_watcher()
        if self.live:
            self.live.__exit__(None, None, None)

    def log_message(
        self,
        category: str,
        message: str,
        style: str = "white",
        category_style: str = "bold white",
    ):
        """
        Add a styled log message to the log panel.

        Args:
            category: Category label (e.g., "CLONE", "INFO", "ERROR")
            message: The message text
            style: Style for the message text
            category_style: Style for the category label
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = Text()
        entry.append(f"[{timestamp}] ", style="dim")
        entry.append(f"{category:10s}", style=category_style)
        entry.append(message, style=style)
        self.log_entries.append(entry)
        self._last_activity = time.time()
        self._update_display()

    def handle_event(self, line: str) -> None:
        """
        Process an event (same interface as current TUI).

        Args:
            line: JSON string from OpenCode event stream
        """
        # Write to log file
        self.log_file.write(line)
        if not line.endswith("\n"):
            self.log_file.write("\n")
        self.log_file.flush()

        # Parse and add to log buffer
        entry = self._parse_event(line)
        if entry:
            self.log_entries.append(entry)
            self._last_activity = time.time()
            self._update_display()

    def _parse_event(self, line: str) -> Optional[Text]:
        """Parse event line and return styled Text."""
        try:
            data = json.loads(line)
            event = OpenCodeEvent(**data)
            self.stats["events"] += 1

            timestamp = datetime.now().strftime("%H:%M:%S")
            entry = Text()
            entry.append(f"[{timestamp}] ", style="dim")

            if event.type == "step_start":
                if event.part and event.part.snapshot:
                    self.current_step = event.part.snapshot
                    entry.append("STEP      ", style="bold magenta")
                    entry.append(event.part.snapshot or "", style="magenta")
                else:
                    return None

            elif event.type == "text":
                if not event.part or not event.part.text:
                    return None
                self.stats["messages"] += 1
                entry.append("MESSAGE   ", style="bold green")
                # Truncate long messages
                msg = (event.part.text or "").replace("\n", " ").strip()
                if len(msg) > 50:
                    msg = msg[:47] + "..."
                entry.append(msg, style="green")

            elif event.type == "tool_use":
                if not event.part or not event.part.tool:
                    return None

                tool = event.part.tool
                tool_state = event.part.state
                tool_input = tool_state.input if tool_state and tool_state.input else {}
                tool_status = tool_state.status if tool_state else "unknown"

                if tool == "task" or "agent" in tool.lower():
                    self.stats["subagents"] += 1
                    subtype = tool_input.get("subagent_type", tool)
                    desc = tool_input.get("description", "")

                    # Calculate duration if available
                    duration_str = ""
                    if tool_state and tool_state.time:
                        time_info = tool_state.time
                        if isinstance(time_info, dict) and "start" in time_info and "end" in time_info:
                            duration_ms = time_info["end"] - time_info["start"]
                            duration_sec = duration_ms / 1000
                            if duration_sec >= 60:
                                duration_str = f" ({duration_sec / 60:.1f}m)"
                            else:
                                duration_str = f" ({duration_sec:.1f}s)"

                    # Show completion status
                    if tool_status == "completed":
                        entry.append("AGENT OK  ", style="bold green")
                        if desc:
                            if len(desc) > 30:
                                desc = desc[:27] + "..."
                            entry.append(f"{subtype} ", style="green bold")
                            entry.append(f"- {desc}", style="green")
                        else:
                            entry.append(subtype, style="green")
                        if duration_str:
                            entry.append(duration_str, style="green dim")
                    elif tool_status == "error":
                        entry.append("AGENT ERR ", style="bold red")
                        if desc:
                            if len(desc) > 30:
                                desc = desc[:27] + "..."
                            entry.append(f"{subtype} ", style="red bold")
                            entry.append(f"- {desc}", style="red")
                        else:
                            entry.append(subtype, style="red")
                        if duration_str:
                            entry.append(duration_str, style="red dim")
                    else:
                        # Unknown status (shouldn't happen often)
                        entry.append("AGENT     ", style="bold yellow")
                        if desc:
                            if len(desc) > 30:
                                desc = desc[:27] + "..."
                            entry.append(f"{subtype} ", style="yellow bold")
                            entry.append(f"- {desc}", style="yellow")
                        else:
                            entry.append(subtype, style="yellow")
                else:
                    self.stats["tools"] += 1
                    entry.append("TOOL      ", style="bold blue")
                    # Build tool description
                    params = self._extract_tool_params(tool_input)
                    if params:
                        entry.append(f"{tool} ", style="blue bold")
                        entry.append(f"({params})", style="blue")
                    else:
                        entry.append(tool, style="blue")

            elif event.type == "step_finish":
                if event.part and event.part.reason:
                    entry.append("FINISH    ", style="bold magenta")
                    reason = event.part.reason
                    cost = event.part.cost
                    msg = f"Reason: {reason}"
                    if cost:
                        msg += f", Cost: ${cost:.4f}"
                    entry.append(msg, style="magenta dim")
                else:
                    return None

            elif event.type == "error":
                entry.append("ERROR     ", style="bold red")
                error_msg = "Unknown error"
                if event.error:
                    error_msg = str(event.error).replace("\n", " ")[:50]
                entry.append(error_msg, style="red")

            else:
                # Skip other event types unless verbose
                if self.verbose:
                    entry.append("OTHER     ", style="dim")
                    entry.append(event.type, style="dim")
                else:
                    return None

            return entry

        except json.JSONDecodeError:
            # Not JSON - log in verbose mode
            if self.verbose:
                stripped = line.strip()
                if stripped:
                    entry = Text()
                    entry.append(f"[{datetime.now().strftime('%H:%M:%S')}] ", style="dim")
                    entry.append("NON-JSON  ", style="yellow")
                    entry.append(stripped[:60], style="yellow dim")
                    return entry
            return None

        except ValidationError:
            # Could be a custom pipeline message (not OpenCodeEvent format)
            try:
                data = json.loads(line)
                if data.get("type") == "message" and data.get("content"):
                    entry = Text()
                    entry.append(f"[{datetime.now().strftime('%H:%M:%S')}] ", style="dim")
                    entry.append("WAIT      ", style="bold cyan")
                    content = data["content"]
                    if len(content) > 50:
                        content = content[:47] + "..."
                    entry.append(content, style="cyan")
                    return entry
            except:
                pass
            return None

        except Exception as e:
            if self.verbose:
                entry = Text()
                entry.append(f"[{datetime.now().strftime('%H:%M:%S')}] ", style="dim")
                entry.append("PARSE ERR ", style="red")
                entry.append(str(e)[:50], style="red dim")
                return entry
            return None

    def _extract_tool_params(self, tool_input: dict) -> str:
        """Extract relevant parameters from tool input for display."""
        params = []

        if "file_path" in tool_input:
            path = Path(tool_input["file_path"])
            params.append(f"file={path.name}")
        elif "path" in tool_input:
            path = Path(tool_input["path"])
            params.append(f"path={path.name}")

        if "pattern" in tool_input:
            pattern = tool_input["pattern"]
            if len(pattern) > 20:
                pattern = pattern[:17] + "..."
            params.append(f"pattern={pattern}")

        if "command" in tool_input:
            cmd = tool_input["command"]
            if len(cmd) > 25:
                cmd = cmd[:22] + "..."
            params.append(f"cmd={cmd}")

        return ", ".join(params)

    def _update_display(self):
        """Update the entire display layout."""
        if not self.live:
            return

        # Advance spinner
        self._spinner_frame = (self._spinner_frame + 1) % len(SPINNER_FRAMES)

        self.layout["header"].update(self._render_header())
        self.layout["logs"].update(self._render_logs())
        self.layout["docs"].update(self._render_docs_tree())
        self.layout["footer"].update(self._render_footer())

    def _render_header(self) -> Panel:
        """Render the top bar with repo info."""
        text = Text()
        text.append("Repository: ", style="bold")
        text.append(self.repo_url, style="bold cyan underline")

        return Panel(text, style="cyan", height=3)

    def _render_logs(self) -> Panel:
        """Render the scrolling logs panel."""
        # Get available height for logs
        try:
            visible_lines = self.console.height - 10  # Account for header/footer/borders
        except Exception:
            visible_lines = 20  # Default fallback

        if visible_lines < 5:
            visible_lines = 5

        # Build log display from buffer
        log_text = Text()
        entries = list(self.log_entries)[-visible_lines:]

        for i, entry in enumerate(entries):
            log_text.append_text(entry)
            if i < len(entries) - 1:
                log_text.append("\n")

        if not entries:
            log_text.append("Waiting for events...", style="dim italic")

        return Panel(log_text, title="[bold]Logs[/bold]", border_style="blue")

    def _render_docs_tree(self) -> Panel:
        """Render the docs tree panel."""
        if not self.repo_path:
            # Still cloning
            content = Text()
            content.append("Cloning repository...\n\n", style="dim italic")
            content.append("Documentation will appear\n", style="dim")
            content.append("here after exploration.", style="dim")
            return Panel(content, title="[bold]Documentation[/bold]", border_style="green")

        docs_dir = self.repo_path / "planning" / "docs"

        if not docs_dir.exists():
            # Show loading indicator
            content = Text()
            content.append("Waiting for documentation...\n\n", style="dim italic")
            content.append("Files will appear here as\n", style="dim")
            content.append("they are created.", style="dim")
            return Panel(content, title="[bold]Documentation[/bold]", border_style="green")

        # Build tree from directory
        tree = Tree("[bold]planning/docs/[/bold]", guide_style="dim")
        self._build_tree(tree, docs_dir)

        return Panel(tree, title="[bold]Documentation[/bold]", border_style="green")

    def _build_tree(self, tree: Tree, path: Path, depth: int = 0):
        """Recursively build tree from directory."""
        if depth > 3:
            return

        try:
            items = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            return

        for item in items:
            if item.name.startswith("."):
                continue

            if item.is_dir():
                branch = tree.add(f"[bold blue]{item.name}/[/bold blue]")
                self._build_tree(branch, item, depth + 1)
            else:
                # Color based on file type
                if item.suffix == ".md":
                    tree.add(f"[green]{item.name}[/green]")
                elif item.suffix in (".yaml", ".yml"):
                    tree.add(f"[yellow]{item.name}[/yellow]")
                else:
                    tree.add(f"[white]{item.name}[/white]")

    def _render_footer(self) -> Panel:
        """Render the statistics bar with activity indicator."""
        stats = Table.grid(padding=(0, 2))
        stats.add_column(justify="left")
        stats.add_column(justify="left")
        stats.add_column(justify="left")
        stats.add_column(justify="left")
        stats.add_column(justify="right", ratio=1)

        # Activity indicator
        if self._completed:
            activity = "[bold green]Complete[/bold green]"
        elif self._running:
            spinner = SPINNER_FRAMES[self._spinner_frame]
            elapsed = time.time() - self._last_activity
            if elapsed > 5:
                activity = f"[yellow]{spinner} Working (no activity for {int(elapsed)}s)[/yellow]"
            else:
                activity = f"[cyan]{spinner} Running[/cyan]"
        else:
            activity = "[dim]Stopped[/dim]"

        stats.add_row(
            f"[cyan]Events:[/cyan] {self.stats['events']}",
            f"[green]Messages:[/green] {self.stats['messages']}",
            f"[blue]Tools:[/blue] {self.stats['tools']}",
            f"[yellow]Agents Done:[/yellow] {self.stats['subagents']}",
            activity,
        )
        return Panel(stats, style="dim", height=3)

    def _start_docs_watcher(self):
        """Start background thread to monitor docs directory."""
        self._watching = True
        self.docs_watcher_thread = Thread(target=self._watch_docs, daemon=True)
        self.docs_watcher_thread.start()

    def _stop_docs_watcher(self):
        """Stop the background docs watcher thread."""
        self._watching = False
        if self.docs_watcher_thread:
            self.docs_watcher_thread.join(timeout=2)

    def _watch_docs(self):
        """Background thread that monitors docs directory for changes."""
        if not self.repo_path:
            return

        docs_dir = self.repo_path / "planning" / "docs"
        last_state: set = set()

        while self._watching:
            try:
                if docs_dir.exists():
                    # Get current file state
                    current_state = set()
                    for f in docs_dir.rglob("*"):
                        if f.is_file():
                            try:
                                current_state.add((str(f), f.stat().st_mtime))
                            except (OSError, FileNotFoundError):
                                pass

                    # If changed, trigger redraw
                    if current_state != last_state:
                        last_state = current_state
                        self._update_display()

                time.sleep(1)  # Check every second

            except Exception:
                pass  # Ignore errors in watcher thread

    def log_post_process(self, result: dict):
        """Log post-processing results to the TUI."""
        if not result:
            return

        # Log diagram rendering
        diagrams_found = result.get("diagrams_found", 0)
        diagrams_rendered = result.get("diagrams_rendered", 0)
        diagrams_failed = result.get("diagrams_failed", 0)

        if diagrams_found > 0:
            if diagrams_rendered == diagrams_found:
                self.log_message(
                    "DIAGRAMS",
                    f"Rendered {diagrams_rendered}/{diagrams_found} mermaid diagrams",
                    "green", "bold green"
                )
            elif diagrams_rendered > 0:
                self.log_message(
                    "DIAGRAMS",
                    f"Rendered {diagrams_rendered}/{diagrams_found} ({diagrams_failed} failed)",
                    "yellow", "bold yellow"
                )
            else:
                self.log_message(
                    "DIAGRAMS",
                    f"Failed to render {diagrams_found} diagrams (mmdc not installed?)",
                    "red", "bold red"
                )

        # Log markdown fixes
        markdown_fixes = result.get("markdown_issues_fixed", 0)
        if markdown_fixes > 0:
            self.log_message("MARKDOWN", f"Fixed {markdown_fixes} markdown issues", "cyan", "bold cyan")

        # Log link fixing
        links_fixed = result.get("github_links_fixed", 0)
        if links_fixed > 0:
            self.log_message("LINKS", f"Fixed {links_fixed} GitHub links", "cyan", "bold cyan")

        # Log validation errors (unrendered mermaid blocks)
        validation_errors = result.get("validation_errors", [])
        if validation_errors:
            self.log_message(
                "VALIDATE",
                f"{len(validation_errors)} unrendered mermaid blocks detected",
                "yellow", "bold yellow"
            )

        # Log HTML site
        html_dir = result.get("html_output_dir")
        if html_dir:
            from pathlib import Path
            if Path(html_dir).exists() and any(Path(html_dir).iterdir()):
                self.log_message("HTML", f"Site built successfully", "green", "bold green")
            else:
                self.log_message("HTML", "Site directory empty (mkdocs failed?)", "red", "bold red")
        else:
            self.log_message("HTML", "Site not built (mkdocs not installed?)", "yellow", "bold yellow")

        # Log errors
        errors = result.get("errors", [])
        for err in errors[:3]:  # Show first 3 errors
            self.log_message("ERROR", str(err)[:50], "red", "bold red")

    def show_completion(self, result: Optional[dict] = None):
        """Show completion summary after pipeline finishes."""
        self.pipeline_result = result
        self._completed = True
        self._running = False

        # Add completion message to log
        self.log_message("COMPLETE", "Documentation pipeline finished", "green", "bold green")


def prompt_for_url(console: Console) -> str:
    """Show a styled prompt for the GitHub URL."""
    console.print()
    console.print("[bold cyan]" + "=" * 60 + "[/bold cyan]")
    console.print("[bold cyan]  Repository Documentation System[/bold cyan]")
    console.print("[bold cyan]" + "=" * 60 + "[/bold cyan]")
    console.print()
    console.print("[dim]Enter a GitHub repository URL to document.[/dim]")
    console.print("[dim]Example: https://github.com/kubernetes/kubernetes[/dim]")
    console.print()

    url = console.input("[bold]GitHub URL:[/bold] ").strip()
    return url


def print_completion_summary(
    repo_path: Path,
    repo_url: str,
    log_file_path: Path,
    stats: dict,
    pipeline_result: Optional[dict] = None,
):
    """Print a final completion summary after the TUI exits."""
    console = Console()

    console.print()
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]")
    console.print("[bold green]Documentation Complete[/bold green]")
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]")
    console.print()

    # Output location (dist folder)
    dist_path = None
    if pipeline_result and "output_paths" in pipeline_result:
        dist_path = pipeline_result["output_paths"].get("dist")

    if dist_path:
        console.print("[bold]Output Location:[/bold]")
        console.print(f"  [bold green]{dist_path}[/bold green]")
        console.print(f"    markdown/  - Processed markdown documentation")
        console.print(f"    site/      - HTML website (serve with python -m http.server)")
        console.print()

    # Repository info
    console.print("[bold]Source Repository:[/bold]")
    console.print(f"  URL:   {repo_url}")
    console.print(f"  Clone: {repo_path}")
    console.print()

    # Statistics
    console.print("[bold]Statistics:[/bold]")
    console.print(f"  Events:    {stats.get('events', 0)}")
    console.print(f"  Messages:  {stats.get('messages', 0)}")
    console.print(f"  Tools:     {stats.get('tools', 0)}")
    console.print(f"  Subagents: {stats.get('subagents', 0)}")
    console.print()

    # Generated files
    main_index = repo_path / "planning" / "index.md"
    component_docs_path = repo_path / "planning" / "docs"
    planning_overview = repo_path / "planning" / "overview.md"
    build_site_dir = repo_path / "build" / "site"

    # Get HTML path from pipeline result if available
    html_output_dir = None
    if pipeline_result and "steps" in pipeline_result:
        post_process = pipeline_result["steps"].get("post_process", {})
        if post_process.get("html_output_dir"):
            html_output_dir = Path(post_process["html_output_dir"])

    if not html_output_dir:
        html_output_dir = build_site_dir

    console.print("[bold]Generated Documentation:[/bold]")
    console.print(
        f"  Main Index:     {main_index} {'[green]OK[/green]' if main_index.exists() else '[dim](not created)[/dim]'}"
    )
    console.print(
        f"  Overview:       {planning_overview} {'[green]OK[/green]' if planning_overview.exists() else '[dim](not created)[/dim]'}"
    )
    console.print(f"  Component Docs: {component_docs_path}/")
    console.print(
        f"  HTML Site:      {html_output_dir}/ {'[green]OK[/green]' if html_output_dir.exists() else '[dim](not built)[/dim]'}"
    )
    console.print(f"  Event Log:      {log_file_path}")
    console.print()

    # Show docs tree if exists
    if component_docs_path.exists():
        console.print("[bold]Component Documentation:[/bold]")
        console.print(f"[dim]Location: {component_docs_path}[/dim]")
        console.print()

        tree = Tree(f"[bold]{component_docs_path.name}/[/bold]")
        _build_completion_tree(tree, component_docs_path)
        console.print(tree)
        console.print()

    # HTML site info
    if html_output_dir and html_output_dir.exists():
        console.print("[bold green]HTML Site Built:[/bold green]")
        console.print(f"  Path: {html_output_dir}")
        console.print(f"  [dim]To view: cd {html_output_dir} && python3 -m http.server 8080[/dim]")
        console.print(f"  [dim]Then open: http://localhost:8080[/dim]")
        console.print()

    # Cleanup hint
    console.print(f"[dim]To remove clone: rm -rf {repo_path.parent}[/dim]")
    console.print()

    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]")
    console.print()


def _build_completion_tree(tree: Tree, path: Path, depth: int = 0):
    """Build tree for completion summary."""
    if depth > 2:
        return

    try:
        items = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except PermissionError:
        return

    for item in items:
        if item.name.startswith("."):
            continue

        if item.is_dir():
            branch = tree.add(f"[bold blue]{item.name}/[/bold blue]")
            _build_completion_tree(branch, item, depth + 1)
        else:
            tree.add(f"[green]{item.name}[/green]")
