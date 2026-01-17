# OpenCode Architecture Overview

## System Purpose

OpenCode is an open-source AI coding agent that provides intelligent development assistance through multiple interfaces. It operates as a provider-agnostic alternative to commercial AI coding tools, with a focus on terminal-based interactions and extensibility.

## Core Architecture

### Client/Server Model

OpenCode follows a client/server architecture where the main application runs as a local server (default port 4096) with multiple client types connecting to it:

- **TUI Client** - Terminal User Interface using OpenTUI/SolidJS
- **Web Client** - Browser-based interface using SolidJS
- **Desktop Client** - Native application using Tauri
- **External Clients** - Via JavaScript/TypeScript SDK

### Agent System Architecture

The system uses a multi-agent architecture with specialized agents:

- **Primary Agents**:
  - `build` - Full access agent for code generation and modification
  - `plan` - Read-only agent for analysis and planning
- **Sub-agents**:
  - `general` - Complex task execution
  - `explore` - Codebase exploration and analysis
- **Hidden Agents**: `compaction`, `title`, `summary` for internal operations

### Permission-Based Security

All operations are governed by a permission system that validates tool access based on agent capabilities and user configuration.

## Component Architecture

### Core Packages

#### `packages/opencode` - Main Application

- **Responsibility**: Primary CLI/TUI application and server
- **Key Features**: Agent system, session management, tool registry, HTTP server
- **Technology**: OpenTUI, SolidJS, Hono framework

#### `packages/app` - Web Interface

- **Responsibility**: Browser-based user interface
- **Key Features**: Alternative to TUI, real-time communication
- **Technology**: SolidJS, Tailwind CSS, SSE communication

#### `packages/desktop` - Desktop Application

- **Responsibility**: Native desktop application
- **Key Features**: Cross-platform support, native capabilities
- **Technology**: Tauri (Rust + Web frontend)

#### `packages/sdk/js` - Client SDK

- **Responsibility**: External integration library
- **Key Features**: Client/server libraries, OpenAPI-based
- **Technology**: Auto-generated from OpenAPI specs

### Infrastructure Components

#### `packages/console` - Management Console

- **Responsibility**: User management, billing, and premium services
- **Key Features**: Authentication, workspace management, Stripe integration
- **Technology**: SolidJS, PlanetScale database

#### `packages/function` - Cloud API

- **Responsibility**: Serverless API endpoints
- **Key Features**: GitHub integration, authentication services
- **Technology**: SST on Cloudflare Workers

#### `packages/web` - Documentation

- **Responsibility**: Documentation and help site
- **Technology**: Astro, Starlight framework

## Data Flow Architecture

### User Interaction Flow

1. User initiates session via preferred client interface
2. Client establishes HTTP connection with Server-Sent Events (SSE)
3. Server creates session with selected agent and model
4. User prompts processed through agent pipeline
5. Agent executes tools with permission validation
6. Results stream back to client via SSE events

### Agent Processing Pipeline

1. **Input Processing**: User prompt → Agent selection → Model provider
2. **LLM Execution**: Model response → Tool calls → Permission validation
3. **Tool Execution**: Tool operations → Result collection → Response formatting
4. **Output Streaming**: Formatted response → SSE events → Client display

### File System Integration

- Project workspace detection and initialization
- Real-time file watching with chokidar
- Git integration for version control awareness
- LSP server integration for code intelligence

### Cloud Services Integration

- Console app handles authentication and billing
- Zen gateway provides managed AI model access
- Stripe integration for subscription management
- Cloudflare Workers for serverless APIs

## Technology Stack

### Core Runtime

- **Bun** - JavaScript/TypeScript runtime and package manager
- **TypeScript** - Primary language with strict typing
- **Turbo** - Monorepo build system

### Frontend Technologies

- **OpenTUI/SolidJS** - Terminal interface framework
- **SolidJS** - Reactive web framework
- **Tailwind CSS** - Styling framework
- **Tauri** - Desktop application framework

### Backend Technologies

- **Hono** - Lightweight web framework
- **PlanetScale** - MySQL database for console
- **SST** - Serverless Stack for cloud deployment
- **Cloudflare Workers** - Serverless runtime

### AI/LLM Integration

- **Vercel AI SDK** - Multi-provider AI integration
- **Multiple Providers**: Anthropic, OpenAI, Google, Azure, Groq, etc.
- **Model Support**: Extensive model catalog including reasoning models

### Development Tools

- **Tree-sitter** - Code parsing and syntax analysis
- **bun-pty** - Terminal integration
- **Chokidar** - File system watching
- **LSP** - Language Server Protocol support

## Architecture Patterns

### Plugin Architecture

- **MCP Server Support** - Model Context Protocol for extensibility
- **Tool Registry** - Extensible tool system for custom operations
- **Provider System** - Pluggable AI model providers

### Session Management

- **Persistent Storage** - Session history and state management
- **Collaboration Features** - Session sharing and multi-user support
- **Fork/Revert** - Experimental workflow support

### Security Architecture

- **Permission System** - Role-based access control
- **Sandboxed Execution** - Isolated tool operations
- **Validation Layer** - Input sanitization and security checks

## Key Architectural Strengths

1. **Provider Agnostic** - Easy switching between AI providers and models
2. **Multi-Interface Support** - Consistent experience across TUI, web, and desktop
3. **Extensibility** - Plugin system for custom tools and agents
4. **Performance** - Bun runtime and optimized tool implementations
5. **Security** - Comprehensive permission system and sandboxed execution
6. **Collaboration** - Session sharing and remote access capabilities
7. **Developer Experience** - Integrated LSP, git awareness, and real-time updates

## Deployment Architecture

### Local Development

- Bun-based development server
- Hot reload with file watching
- Integrated testing and linting

### Production Deployment

- Serverless deployment on Cloudflare Workers
- Managed database with PlanetScale
- CDN distribution for web assets
- Container support for enterprise deployments

This architecture demonstrates a sophisticated approach to building an AI coding assistant that prioritizes flexibility, performance, security, and user experience across multiple interaction paradigms.
