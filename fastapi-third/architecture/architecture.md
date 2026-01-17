# FastAPI Architecture Analysis

## High-Level Overview

FastAPI is a modern, high-performance web framework for building APIs with Python. It is built on top of **Starlette** for the web parts and **Pydantic** for the data parts.

The architecture follows a layered approach:
1.  **ASGI Interface**: The foundation, typically served by Uvicorn.
2.  **Starlette Core**: Handles low-level routing, Request/Response objects, and Middleware.
3.  **FastAPI Layer**: Adds Dependency Injection, Data Validation (Pydantic), and OpenAPI generation.

## Key Components

### 1. Application (`FastAPI`)
The main entry point. It inherits from Starlette's `App` and adds specific FastAPI functionality. It manages the central router, exception handlers, and the middleware stack.

### 2. Routing System (`APIRouter`, `APIRoute`)
*   **APIRouter**: Allows structuring the application into multiple modules. It aggregates routes and sub-routers.
*   **APIRoute**: Represents a single path operation. It wraps the user's endpoint function. Crucially, it generates a custom request handler (`get_request_handler`) that orchestrates the execution flow for that specific endpoint.

### 3. Dependency Injection System
A unique and powerful feature of FastAPI.
*   **Dependant**: A model representing the dependency graph for a specific endpoint.
*   **Resolution**: Dependencies are resolved recursively. The system handles caching (scoped to the request), async/sync compatibility, and clean-up (via `yield` and `AsyncExitStack`).

### 4. Data Validation & Serialization
FastAPI deeply integrates with Pydantic.
*   **Input**: Request parameters (Query, Path, Header, Cookie) and Body are extracted and validated against Pydantic models or type hints.
*   **Output**: Return values are validated and serialized using the `response_model` schema.

## Execution Model

When a request arrives:
1.  **Middleware**: Passes through global middleware (e.g., CORS, GZip).
2.  **Routing**: The URL is matched against registered routes.
3.  **Dependency Resolution**: The DI system executes the dependency graph, creating necessary objects (database sessions, users, etc.).
4.  **Validation**: Incoming data is parsed and validated. Errors raise `RequestValidationError`.
5.  **Endpoint**: The user's function is executed with the resolved dependencies and validated data.
6.  **Serialization**: The result is validated against the response schema and serialized to JSON.
