# FastAPI Architecture Analysis

## High-Level Overview

FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.9+ based on standard Python type hints. It is built on top of **Starlette** for the web parts and **Pydantic** for the data parts.

The core design philosophy revolves around:
1.  **Type Safety**: Leveraging Python's type hints for validation and serialization.
2.  **Performance**: Using `async` and `await` with an ASGI foundation (Starlette).
3.  **Developer Experience**: Automatic interactive documentation (Swagger UI, ReDoc) and editor support (autocompletion).

## Core Components

### 1. The Application (`FastAPI` class)
Located in `fastapi/applications.py`, the `FastAPI` class is the main entry point. It inherits directly from `starlette.applications.Starlette`. This inheritance means FastAPI *is* a Starlette application, just with extra features on top:
-   Automatic OpenAPI schema generation.
-   Enhanced routing (`APIRouter`) that supports dependency injection.
-   Integrated Pydantic model validation.

### 2. Routing (`APIRouter` & `APIRoute`)
The routing system (`fastapi/routing.py`) extends Starlette's routing. 
-   **APIRoute**: Customizes the standard route handling to include the "FastAPI lifecycle":
    -   Resolving dependencies.
    -   Validating request body and parameters against Pydantic models.
    -   Executing the endpoint.
    -   Validating and serializing the response.
-   **APIRouter**: A utility to group routes (paths) and middleware, which can be included in the main app or other routers.

### 3. Dependency Injection System
This is a distinguishing feature of FastAPI, located in `fastapi/dependencies/`.
-   **Dependant**: Represents a node in the dependency graph.
-   **Resolution**: The `solve_dependencies` function recursively resolves the dependency graph. It handles:
    -   Getting values from the request (headers, cookies, query params).
    -   Calling dependency functions (which can themselves have dependencies).
    -   Managing scopes and context managers (`yield` dependencies).
    -   Async and Sync compatibility.

### 4. Data Validation & Serialization
FastAPI uses **Pydantic** (v2) extensively.
-   **Input**: Request parameters (Query, Path, Body) are declared with type hints. FastAPI extracts these from the request and passes them to Pydantic for validation.
-   **Output**: The `response_model` argument allows the framework to filter and validate the data returned by the endpoint before sending it to the client.

### 5. OpenAPI Generation
The framework automatically inspects the registered routes, their parameters, and Pydantic models to generate an OpenAPI 3.1.0 schema.
-   **utils.py**: The `get_openapi` function iterates over all routes, converting Pydantic models to JSON Schemas and mapping parameters to OpenAPI definitions.
-   **Docs**: This schema is used to power the `/docs` (Swagger UI) and `/redoc` (ReDoc) endpoints.

## Architecture Pattern

FastAPI follows a **Layered Micro-framework** architecture:
1.  **Interface Layer**: ASGI (via Uvicorn/Starlette) handles the raw protocol.
2.  **Routing Layer**: Starlette matches URLs to handlers.
3.  **Validation Layer**: FastAPI/Pydantic intercepts the request to validate data *before* it reaches the handler.
4.  **Service/Controller Layer**: The user's path operation functions.
5.  **Serialization Layer**: The response is validated and serialized back to JSON.

The Dependency Injection system acts as a cross-cutting concern, allowing shared logic (auth, database connections) to be injected cleanly into any layer.
