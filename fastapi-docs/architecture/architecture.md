# FastAPI Architecture Overview

FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.8+ based on standard Python type hints. It acts as a glue layer between **Starlette** (for web routing and ASGI support) and **Pydantic** (for data validation and serialization), adding a powerful dependency injection system and automatic OpenAPI documentation generation.

## Architectural Layers

### 1. The Core: Starlette
FastAPI inherits directly from `Starlette`. Every FastAPI application is a Starlette application.
- **Responsibility:** Handling ASGI requests, Routing, Middleware, WebSockets, Background Tasks, and Lifecycle events.
- **Key Class:** `FastAPI` (subclass of `starlette.applications.Starlette`).

### 2. Data & Validation: Pydantic
FastAPI uses Pydantic to define the shape of data.
- **Responsibility:** Data validation, Data parsing (conversion from string/JSON to Python types), and Schema definition (JSON Schema).
- **Integration:** Request bodies, query parameters, path parameters, and headers are validated against Pydantic models.

### 3. Dependency Injection System
FastAPI introduces a hierarchical dependency injection system.
- **Responsibility:** Managing shared logic (database connections, authentication, security) and injecting them into path operations.
- **Mechanism:** Dependencies are defined as standard Python functions or classes. The `solve_dependencies` engine resolves the graph of dependencies (including sub-dependencies) before calling the endpoint.

### 4. OpenAPI & Documentation
FastAPI automatically generates an OpenAPI schema based on the routing and Pydantic models.
- **Responsibility:** Producing `openapi.json` and serving interactive documentation UIs (Swagger UI, ReDoc).
- **Mechanism:** Inspection of function signatures and type hints.

## Key Concepts

- **Path Operation:** A specific endpoint (e.g., `GET /users/{id}`) defined by a decorated function.
- **APIRouter:** A mechanism to structure the application into multiple modules/files, similar to Flask Blueprints.
- **Dependant:** An internal representation of the dependency graph for a specific path operation.
- **Middleware:** Components that process requests before they reach the application and responses before they leave.

## Request Lifecycle
1.  **ASGI Interface:** The server (e.g., Uvicorn) receives a raw network request and passes it to FastAPI via the ASGI interface.
2.  **Middleware:** The request passes through the middleware stack (e.g., CORS, GZip).
3.  **Routing:** The `APIRouter` matches the path to a specific `APIRoute`.
4.  **Dependency Resolution:** The system executes the dependency graph defined for that route.
5.  **Validation:** Input data (Query, Path, Body) is validated against Pydantic models.
6.  **Execution:** The user-defined path operation function is executed with the injected dependencies and validated data.
7.  **Serialization:** The return value is validated and serialized (JSON encoding) based on the `response_model`.
8.  **Response:** A standard ASGI response is sent back.
