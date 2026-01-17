# Pattern Detection - Architectural & Design Patterns

## Objective
Identify and document architectural patterns and design patterns present in the codebase. Provide concrete evidence with file references and line numbers to support Stage 2 orchestrators.

## Context Requirements
This prompt assumes you have access to:
- `components.json` from architecture analysis
- Repository manifest files (package.json, pyproject.toml, etc.)
- Directory structure listing

## Required Outputs

### 1. Patterns Report (patterns/identified-patterns.md)
```markdown
# Identified Patterns

## Architectural Patterns

### <Pattern Name> (Confidence: X%)
**Evidence**:
- `<file-path>:<line-range>` - <description-of-evidence>
- `<file-path>:<line-range>` - <description-of-evidence>

**Description**: [How this pattern is implemented in the codebase]

**Components Involved**:
- `<component-id>` - <role-in-pattern>
- `<component-id>` - <role-in-pattern>

## Design Patterns

### <Pattern Name>
**Instances**:
1. **Location**: `<file-path>:<line-range>`
   - **Implementation**: [Description]
   - **Purpose**: [Why this pattern is used here]
   - **Participants**:
     - `<class/function>` - <role>

2. **Location**: `<file-path>:<line-range>`
   - ...

### <Another Pattern>
...
```

### 2. Patterns Metadata (patterns/patterns.json)
```json
{
  "architectural_patterns": [
    {
      "name": "MVC",
      "confidence": 0.95,
      "evidence": [
        {
          "file_path": "src/models/user.py",
          "line_range": {"start": 1, "end": 50},
          "description": "Model layer handling data persistence"
        },
        {
          "file_path": "src/views/user_view.py",
          "line_range": {"start": 1, "end": 80},
          "description": "View layer rendering templates"
        },
        {
          "file_path": "src/controllers/user_controller.py",
          "line_range": {"start": 1, "end": 120},
          "description": "Controller coordinating model and view"
        }
      ],
      "components_involved": ["user-model", "user-view", "user-controller"]
    }
  ],
  "design_patterns": [
    {
      "name": "Singleton",
      "instances": [
        {
          "file_path": "src/database/connection.py",
          "line_range": {"start": 15, "end": 35},
          "class_name": "DatabaseConnection",
          "description": "Ensures single database connection instance",
          "implementation_details": "Uses __new__ method to control instantiation"
        }
      ]
    },
    {
      "name": "Factory",
      "instances": [
        {
          "file_path": "src/services/notification_factory.py",
          "line_range": {"start": 20, "end": 45},
          "class_name": "NotificationFactory",
          "description": "Creates different notification types based on input",
          "products": ["EmailNotification", "SMSNotification", "PushNotification"]
        }
      ]
    }
  ],
  "api_patterns": [
    {
      "type": "REST",
      "confidence": 1.0,
      "evidence_files": ["src/routes/*.py", "src/api/handlers.js"],
      "characteristics": ["HTTP methods", "Resource-based URLs", "Status codes"]
    }
  ]
}
```

## Analysis Instructions

### Architectural Pattern Detection

#### 1. MVC (Model-View-Controller)
**Look for**:
- Separate directories: `models/`, `views/`, `controllers/`
- Files with naming: `*_model.py`, `*_view.tsx`, `*_controller.py`
- Clear separation of data, presentation, and logic

**Evidence to collect**:
- Model files handling database/data structures
- View files rendering UI
- Controller files coordinating between model and view

#### 2. Microservices
**Look for**:
- Multiple services in separate directories: `services/*`
- Independent deployment configurations (Dockerfiles per service)
- Service-to-service communication (HTTP, gRPC, message queues)
- Separate package files per service

**Evidence to collect**:
- Service entry points
- Inter-service API calls
- Service boundaries and responsibilities

#### 3. Layered Architecture
**Look for**:
- Directories like `presentation/`, `business/`, `data/`, `infrastructure/`
- Or `api/`, `services/`, `repositories/`, `models/`
- Unidirectional dependencies (upper layers depend on lower layers)

**Evidence to collect**:
- Layer boundary files
- Dependency flow between layers

#### 4. Event-Driven
**Look for**:
- Event emitters/listeners
- Message queues (Kafka, RabbitMQ, Redis Pub/Sub)
- Event handler registration
- Files named `*_event.py`, `*_listener.js`

**Evidence to collect**:
- Event definition files
- Event handler implementations
- Message queue configurations

#### 5. CQRS (Command Query Responsibility Segregation)
**Look for**:
- Separate command and query handlers
- Different models for read and write operations
- Directories like `commands/`, `queries/`

**Evidence to collect**:
- Command handler implementations
- Query handler implementations
- Separate read/write models

### Design Pattern Detection

#### Common Patterns to Detect

1. **Singleton**
   - Look for: `__new__` override, class-level instance variables, `getInstance()` methods
   - File pattern: `*singleton*`, `*connection*`, `*config*`

2. **Factory**
   - Look for: Methods returning different subclass instances
   - Keywords: `create*`, `make*`, `build*`, `*Factory`

3. **Observer**
   - Look for: Event listeners, callbacks, subscriber lists
   - Keywords: `subscribe`, `addListener`, `notify`, `*Observer`

4. **Strategy**
   - Look for: Polymorphic behavior, algorithm selection
   - Keywords: `*Strategy`, algorithm swapping

5. **Decorator**
   - Look for: Python `@decorator` or wrapper classes
   - Keywords: `@*`, `*Decorator`, wrapping behavior

6. **Adapter**
   - Look for: Interface translation, wrapper classes
   - Keywords: `*Adapter`, `*Wrapper`

7. **Repository**
   - Look for: Data access abstraction
   - Keywords: `*Repository`, `*DAO`, data access objects

## Detection Workflow

```
1. Load components.json to understand system structure
2. For each architectural pattern:
   a. Search for characteristic directory structures
   b. Read relevant files to confirm pattern
   c. Record evidence with file paths and line ranges
   d. Calculate confidence score (0.0-1.0)
3. For each design pattern:
   a. Search for pattern-specific keywords/structures
   b. Read implementation details
   c. Verify it's actually the pattern (not just naming)
   d. Document all instances with file references
4. Generate patterns.md and patterns.json
5. Validate all file paths and line ranges exist
```

## Confidence Scoring

### Architectural Patterns
- **1.0 (Certain)**: All characteristic elements present and clearly implemented
- **0.8-0.9 (High)**: Most elements present, pattern clearly recognizable
- **0.6-0.7 (Medium)**: Some elements present, pattern partially implemented
- **0.4-0.5 (Low)**: Few elements, might be coincidental structure
- **< 0.4**: Don't report

### Design Patterns
- Only report instances where the pattern is clearly and intentionally implemented
- Avoid false positives from coincidental naming or structure

## Evidence Quality Requirements

For each pattern instance:
- **MUST** provide exact file path
- **MUST** provide line range (start and end)
- **SHOULD** include code snippet (2-5 lines) showing key characteristic
- **MUST** explain WHY this is evidence of the pattern

## Example Evidence

**Good Evidence**:
```
file_path: "src/database/connection.py"
line_range: {start: 15, end: 35}
description: "Singleton pattern using __new__ to ensure single instance. Line 18 checks if instance exists, line 20 creates new instance only if None."
```

**Bad Evidence**:
```
file_path: "src/utils.py"
description: "This file has some singleton-like code"
```

## Output Validation

Before finalizing, verify:
- [ ] All file paths are relative to repository root
- [ ] All line ranges are accurate
- [ ] Confidence scores justified by evidence
- [ ] No false positives (naming doesn't mean pattern is used)
- [ ] At least 1 piece of evidence per reported pattern
- [ ] JSON is valid and matches schema

## Token Efficiency

- Use glob/grep to find pattern-indicative files first
- Read only relevant sections using line ranges
- Don't analyze every file, focus on likely pattern locations
- Reuse component information from components.json

## Success Criteria
- Architectural patterns identified with >= 0.6 confidence
- Design pattern instances have concrete code evidence
- All evidence includes file paths and line ranges
- No false positives from superficial analysis
