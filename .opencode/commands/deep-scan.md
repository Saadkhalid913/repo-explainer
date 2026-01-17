# deep-scan

Perform a comprehensive deep analysis of the repository architecture, patterns, and implementation details.

## Instructions

You are an expert software architect performing an exhaustive analysis of this codebase. Generate detailed documentation covering all aspects of the system.

### 1. architecture.md

Create an extremely detailed architecture document:

#### Executive Summary
- What the system does
- Who it's for
- Key capabilities

#### System Architecture
- Architectural pattern (with justification)
- System boundaries
- External integrations
- Deployment model (if discernible)

#### Core Components (for each major component)
- Name and purpose
- Responsibilities (bulleted list)
- Public interfaces/APIs
- Internal structure
- Dependencies (internal and external)
- Configuration requirements
- Error handling approach

#### Data Architecture
- Data models and entities
- Data stores (databases, caches, etc.)
- Data flow and transformations
- Data validation points

#### API Design
- API style (REST, GraphQL, gRPC, etc.)
- Authentication/authorization patterns
- Request/response formats
- Error handling

#### Security Considerations
- Authentication mechanisms
- Authorization patterns
- Input validation
- Secrets management

### 2. components.mermaid

Detailed component diagram:

```mermaid
flowchart TB
    subgraph Frontend
        UI[User Interface]
        State[State Management]
    end
    
    subgraph Backend
        API[API Layer]
        Service[Service Layer]
        Data[Data Layer]
    end
    
    subgraph Infrastructure
        DB[(Database)]
        Cache[(Cache)]
    end
    
    UI --> State
    State --> API
    API --> Service
    Service --> Data
    Data --> DB
    Data --> Cache
```

### 3. dataflow.mermaid

Comprehensive data flow diagram showing all major flows:

```mermaid
flowchart TD
    subgraph User Flows
        Login[Login Flow]
        Action[User Action]
    end
    
    subgraph Processing
        Validate[Validation]
        Process[Business Logic]
        Store[Persistence]
    end
    
    Login --> Validate
    Action --> Validate
    Validate --> Process
    Process --> Store
```

### 4. sequence-auth.mermaid (if applicable)

Authentication/authorization sequence:

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant Auth
    participant Database
    
    User->>Frontend: Login request
    Frontend->>API: POST /auth/login
    API->>Auth: Validate credentials
    Auth->>Database: Query user
    Database-->>Auth: User data
    Auth-->>API: JWT token
    API-->>Frontend: Auth response
    Frontend-->>User: Logged in
```

### 5. er-diagram.mermaid (if applicable)

Entity relationship diagram for data models:

```mermaid
erDiagram
    USER ||--o{ ORDER : places
    ORDER ||--|{ ORDER_ITEM : contains
    PRODUCT ||--o{ ORDER_ITEM : "ordered in"
```

### 6. dependency-graph.mermaid

Module/package dependency graph:

```mermaid
flowchart BT
    subgraph Core
        Utils[Utilities]
        Config[Configuration]
    end
    
    subgraph Features
        Auth[Authentication]
        API[API Handlers]
    end
    
    Auth --> Utils
    Auth --> Config
    API --> Auth
    API --> Utils
```

### 7. tech-stack.txt

Exhaustive technology inventory:

```
# Programming Languages
- Python 3.11
- TypeScript 5.x

# Frameworks
- FastAPI 0.100+
- React 18

# Libraries
- Pydantic (validation)
- SQLAlchemy (ORM)
...

# Build Tools
- pip / poetry
- npm / pnpm

# Testing
- pytest
- Jest

# CI/CD
- GitHub Actions

# Infrastructure
- Docker
- PostgreSQL
```

### 8. patterns.md

Document all identified patterns:

```markdown
# Identified Patterns

## Architectural Patterns
- **Pattern Name**: Description and where it's used

## Design Patterns
- **Factory**: Used in X for creating Y instances
- **Strategy**: Used for Z behavior variations

## Code Patterns
- Error handling conventions
- Logging patterns
- Configuration management

## Anti-Patterns (if found)
- Description and location
- Potential improvements
```

## Analysis Strategy

1. **Manifest files**: package.json, pyproject.toml, requirements.txt, go.mod, Cargo.toml
2. **Configuration**: .env.example, config/, settings files
3. **Entry points**: main files, __main__.py, index files
4. **Core business logic**: services/, handlers/, controllers/
5. **Data layer**: models/, schemas/, migrations/
6. **API definitions**: routes/, endpoints/, resolvers/
7. **Tests**: Understand behavior from test cases
8. **Documentation**: Existing docs, README, comments

Take your time to be thorough and accurate. This analysis will be used for developer onboarding.
