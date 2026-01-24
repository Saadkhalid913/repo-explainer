Generate comprehensive reference tables for documentation

## Table Types

### 1. API Endpoint Table

| Endpoint | Method | Parameters | Returns | Description |
|----------|--------|-----------|---------|-------------|
| /api/v1/pods | GET | namespace, name | Pod | Get pod details |
| /api/v1/pods | POST | Pod spec | Pod | Create pod |

### 2. Configuration Options Table

| Option | Type | Default | Description | Example |
|--------|------|---------|-------------|---------|
| --port | int | 8080 | Server port | --port=9090 |
| --verbose | bool | false | Enable logging | --verbose=true |

### 3. Sub-Component Matrix

| Component | Purpose | Dependencies | Status |
|-----------|---------|--------------|--------|
| DeploymentController | Manages deployments | ReplicaSet | Active |
| StatefulSetController | Manages stateful apps | PVC | Active |

### 4. Dependencies Table

| Dependency | Version | Purpose | Required |
|------------|---------|---------|----------|
| etcd | 3.5+ | Data store | Yes |
| containerd | 1.6+ | Container runtime | Yes |

## Formatting Rules

- Use markdown tables (pipes and dashes)
- Include header row
- Align columns for readability
- Include units in headers (e.g., "Timeout (seconds)")
- Use code formatting for values (`true`, `8080`)

## When to Use

- **API Endpoint Table**: When documenting REST APIs, gRPC services, or any endpoint-based interface
- **Configuration Options Table**: When documenting CLI flags, config files, environment variables
- **Sub-Component Matrix**: When a component has multiple sub-parts (controllers, plugins, handlers)
- **Dependencies Table**: When documenting external dependencies, libraries, or system requirements
