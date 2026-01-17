# Node.js Architecture Overview

Node.js is an open-source, cross-platform JavaScript runtime environment that executes JavaScript code outside of a web browser. It is designed to build scalable network applications using an event-driven, non-blocking I/O model.

## Core Layers

The architecture of Node.js consists of several distinct layers:

### 1. Node.js Standard Library (`lib/`)
This is the JavaScript layer exposed to the developer. It includes core modules like `fs`, `http`, `path`, `events`, and `stream`. These modules provide a high-level API for interacting with the underlying system resources.

### 2. Node.js Bindings (`src/`)
This layer is written in C++ and serves as the bridge between the JavaScript standard library and the core C++ dependencies. It uses the V8 API to create JavaScript objects and functions that wrap C++ functionality. Key components include:
- **Built-in Loaders:** Mechanisms to load native C++ modules.
- **Async Wraps:** Infrastructure for asynchronous resource tracking.
- **Inspector Agent:** Debugging and profiling integration.

### 3. V8 JavaScript Engine (`deps/v8/`)
Developed by Google for Chrome, V8 is the engine Node.js uses to parse and execute JavaScript code. It compiles JavaScript directly to native machine code. V8 provides the memory heap, call stack, and garbage collector.

### 4. libuv (`deps/uv/`)
libuv is a multi-platform support library with a focus on asynchronous I/O. It abstracts non-blocking I/O operations to a consistent interface across supported platforms (Windows, Linux, macOS, etc.). It provides:
- **The Event Loop:** The core mechanism that handles orchestrating callbacks.
- **Thread Pool:** Used for operations that cannot be done non-blocking at the kernel level (e.g., file system operations, DNS lookups).
- **Network I/O:** TCP, UDP, and named pipes.

### 5. Other Core Dependencies (`deps/`)
Node.js relies on several other libraries for specific functionality:
- **OpenSSL:** For TLS/SSL and crypto operations.
- **zlib:** For compression and decompression (gzip).
- **c-ares:** For asynchronous DNS requests.
- **llhttp:** For parsing HTTP messages.
- **nghttp2:** For HTTP/2 support.

## The Event Loop Model

Node.js operates on a single-threaded event loop model. While the JavaScript execution is single-threaded (handled by V8), I/O operations are offloaded to the system kernel or the libuv thread pool. When these operations complete, the kernel or thread pool signals libuv, which queues the associated callback to be executed by V8 on the main thread.
