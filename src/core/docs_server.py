"""HTTP server for serving generated documentation.

Provides:
1. Static file serving for the HTML documentation site
2. Zip download endpoint for raw markdown + HTML docs
"""

import http.server
import io
import os
import signal
import socketserver
import threading
import zipfile
from pathlib import Path
from typing import Optional, Callable
from urllib.parse import urlparse, parse_qs
import logging

logger = logging.getLogger(__name__)


class DocsRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom request handler for documentation server."""

    # Class-level attributes set by DocsServer
    docs_dir: Path = Path(".")
    raw_docs_dir: Optional[Path] = None
    html_site_dir: Optional[Path] = None
    repo_name: str = "docs"

    def __init__(self, *args, **kwargs):
        # Set directory to serve from
        super().__init__(*args, directory=str(self.html_site_dir or self.docs_dir), **kwargs)

    def do_GET(self):
        """Handle GET requests."""
        parsed = urlparse(self.path)

        # Handle zip download endpoint
        if parsed.path == "/download.zip":
            self._serve_zip_download()
            return

        # Handle root redirect to index.html if it exists
        if parsed.path == "/" or parsed.path == "":
            index_path = Path(self.directory) / "index.html"
            if index_path.exists():
                self.path = "/index.html"

        # Default static file serving
        super().do_GET()

    def _serve_zip_download(self):
        """Generate and serve a zip file of the documentation."""
        try:
            zip_buffer = io.BytesIO()

            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Add raw markdown docs
                if self.raw_docs_dir and self.raw_docs_dir.exists():
                    self._add_directory_to_zip(zf, self.raw_docs_dir, "markdown")

                # Add HTML site
                if self.html_site_dir and self.html_site_dir.exists():
                    self._add_directory_to_zip(zf, self.html_site_dir, "html")

            zip_buffer.seek(0)
            zip_data = zip_buffer.getvalue()

            # Send response
            self.send_response(200)
            self.send_header("Content-Type", "application/zip")
            self.send_header("Content-Disposition", f"attachment; filename={self.repo_name}-docs.zip")
            self.send_header("Content-Length", str(len(zip_data)))
            self.end_headers()
            self.wfile.write(zip_data)

        except Exception as e:
            logger.error(f"Error generating zip: {e}")
            self.send_error(500, f"Error generating zip file: {e}")

    def _add_directory_to_zip(self, zf: zipfile.ZipFile, directory: Path, prefix: str):
        """Add all files from a directory to the zip file."""
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                # Create relative path within zip
                rel_path = file_path.relative_to(directory)
                arcname = f"{prefix}/{rel_path}"
                zf.write(file_path, arcname)

    def log_message(self, format, *args):
        """Suppress default logging to avoid cluttering output."""
        pass


class DocsServer:
    """HTTP server for documentation with graceful shutdown."""

    def __init__(
        self,
        docs_dir: Path,
        raw_docs_dir: Optional[Path] = None,
        html_site_dir: Optional[Path] = None,
        repo_name: str = "docs",
        port: int = 8080,
        log_callback: Optional[Callable[[str], None]] = None
    ):
        """
        Initialize the documentation server.

        Args:
            docs_dir: Base documentation directory
            raw_docs_dir: Directory containing raw markdown files
            html_site_dir: Directory containing generated HTML site
            repo_name: Repository name (used for zip filename)
            port: Port to serve on (will try next available if busy)
            log_callback: Optional callback for logging
        """
        self.docs_dir = Path(docs_dir)
        self.raw_docs_dir = Path(raw_docs_dir) if raw_docs_dir else None
        self.html_site_dir = Path(html_site_dir) if html_site_dir else None
        self.repo_name = repo_name
        self.requested_port = port
        self.actual_port: Optional[int] = None
        self.log_callback = log_callback

        self._server: Optional[socketserver.TCPServer] = None
        self._server_thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()

    def _log(self, message: str):
        """Log a message."""
        logger.info(message)
        if self.log_callback:
            self.log_callback(message)

    def _find_available_port(self, start_port: int, max_attempts: int = 10) -> int:
        """Find an available port starting from start_port."""
        import socket

        for offset in range(max_attempts):
            port = start_port + offset
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("", port))
                    return port
            except OSError:
                continue

        raise RuntimeError(f"Could not find available port in range {start_port}-{start_port + max_attempts}")

    def start(self) -> int:
        """
        Start the server in a background thread.

        Returns:
            The actual port the server is running on.
        """
        if self._server is not None:
            raise RuntimeError("Server already running")

        # Find available port
        self.actual_port = self._find_available_port(self.requested_port)

        # Configure the request handler class
        DocsRequestHandler.docs_dir = self.docs_dir
        DocsRequestHandler.raw_docs_dir = self.raw_docs_dir
        DocsRequestHandler.html_site_dir = self.html_site_dir
        DocsRequestHandler.repo_name = self.repo_name

        # Create server with address reuse
        socketserver.TCPServer.allow_reuse_address = True
        self._server = socketserver.TCPServer(("", self.actual_port), DocsRequestHandler)

        # Start server thread
        self._server_thread = threading.Thread(target=self._serve_forever, daemon=True)
        self._server_thread.start()

        self._log(f"Documentation server started on port {self.actual_port}")
        return self.actual_port

    def _serve_forever(self):
        """Serve requests until shutdown is requested."""
        try:
            self._server.serve_forever()
        except Exception as e:
            if not self._shutdown_event.is_set():
                logger.error(f"Server error: {e}")

    def stop(self):
        """Stop the server gracefully."""
        if self._server is None:
            return

        self._shutdown_event.set()

        # Shutdown the server (this will stop serve_forever)
        try:
            self._server.shutdown()
        except Exception:
            pass

        # Wait for thread to finish
        if self._server_thread and self._server_thread.is_alive():
            self._server_thread.join(timeout=2.0)

        # Close the server socket
        try:
            self._server.server_close()
        except Exception:
            pass

        self._server = None
        self._shutdown_event.clear()

    def get_docs_url(self) -> str:
        """Get the URL to view documentation."""
        if self.actual_port is None:
            raise RuntimeError("Server not started")
        return f"http://localhost:{self.actual_port}/"

    def get_download_url(self) -> str:
        """Get the URL to download the documentation zip."""
        if self.actual_port is None:
            raise RuntimeError("Server not started")
        return f"http://localhost:{self.actual_port}/download.zip"

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False


def create_docs_server(
    build_dir: Path,
    repo_name: str = "docs",
    port: int = 8080,
    log_callback: Optional[Callable[[str], None]] = None
) -> DocsServer:
    """
    Create a documentation server from a build directory.

    Args:
        build_dir: The build directory containing docs/ and site/
        repo_name: Repository name for the zip filename
        port: Preferred port (will find next available if busy)
        log_callback: Optional logging callback

    Returns:
        Configured DocsServer instance (not yet started)
    """
    build_dir = Path(build_dir)

    # Determine directory paths
    raw_docs_dir = build_dir / "docs"
    html_site_dir = build_dir / "site"

    # Fall back to docs if site doesn't exist
    if not html_site_dir.exists():
        html_site_dir = raw_docs_dir

    return DocsServer(
        docs_dir=build_dir,
        raw_docs_dir=raw_docs_dir if raw_docs_dir.exists() else None,
        html_site_dir=html_site_dir if html_site_dir.exists() else None,
        repo_name=repo_name,
        port=port,
        log_callback=log_callback
    )
