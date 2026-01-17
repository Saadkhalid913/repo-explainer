# Kubernetes Architecture

## Executive Summary
Kubernetes is a production-grade container orchestration system designed to automate the deployment, scaling, and management of containerized applications. It provides a platform-agnostic way to manage clusters of hosts (nodes) and the workloads running on them.

The system follows a **decoupled, asynchronous, and declarative** design. Users describe the "desired state" of the system through the API, and various independent controllers work continuously to transition the "actual state" toward that desired state. This reconciliation loop is the fundamental pattern of Kubernetes.

## System Purpose & Design Philosophy
- **Problem Solved:** Managing microservices at scale, handling failures automatically, and optimizing resource utilization across a cluster of machines.
- **Design Goals:** 
    - **Scalability:** Capable of managing thousands of nodes and tens of thousands of pods.
    - **High Availability:** No single point of failure in the control plane.
    - **Extensibility:** Almost every component can be replaced or extended (CRDs, Admission Webhooks, CNI, CSI).
    - **Portability:** Runs on public clouds, private clouds, and bare metal.

## Architecture at a Glance

### Architectural Style
Kubernetes uses a **Modular Monorepo** structure. It is composed of a central **Control Plane** that manages the cluster and a set of **Nodes** that run the actual workloads. Communication is centralized through the API Server; no other control plane component talks directly to etcd or to each other.

### Core Subsystems
- **API Server** (`cmd/kube-apiserver`) - The central gateway for all cluster operations.
- **etcd** (External) - Distributed storage for cluster state.
- **Scheduler** (`cmd/kube-scheduler`) - Decides where to place workloads.
- **Controller Manager** (`cmd/kube-controller-manager`) - Handles routine cluster tasks (node management, replication).
- **Kubelet** (`cmd/kubelet`) - The primary agent running on each node.
- **Kube Proxy** (`cmd/kube-proxy`) - Manages network rules on nodes.

## Detailed Component Analysis

### Component: API Server
**Purpose:** Serves the Kubernetes API and acts as the "brain" of the cluster.
**Location:** `cmd/kube-apiserver`
**Key Responsibilities:**
- Validates and configures data for API objects.
- Provides RESTful entry points for clients and other components.
- Manages authentication, authorization, and admission control.
- Directly interacts with etcd for persistence.
**Core Abstractions:**
- `GenericAPIServer` - The base server logic.
- `Registry` - Logic for storing and retrieving objects from etcd.
**Entry Points:**
- `cmd/kube-apiserver/main.go` -> `app.NewAPIServerCommand()`

### Component: Scheduler
**Purpose:** Assigns unscheduled Pods to Nodes.
**Location:** `cmd/kube-scheduler`
**Key Responsibilities:**
- Filters nodes (Predicates) based on resource requirements, constraints, and affinity.
- Ranks remaining nodes (Priorities) to find the best fit.
- Updates the Pod object with the selected Node name (Binding).
**Extension Points:**
- **Scheduling Framework** - Allows adding custom plugins for sorting, filtering, and scoring nodes.

### Component: Kubelet
**Purpose:** Ensures that containers are running in a Pod on a specific node.
**Location:** `cmd/kubelet`
**Key Responsibilities:**
- Watches the API Server for Pods assigned to its node.
- Interacts with the Container Runtime (via CRI) to start/stop containers.
- Reports node and pod status back to the API Server.
- Performs health checks (Liveness/Readiness probes).
**Interactions:**
- Consumes: Pod definitions from API Server.
- Provides: Container management on the host.

### Component: Controller Manager
**Purpose:** Runs controller processes that regulate the state of the cluster.
**Location:** `cmd/kube-controller-manager`
**Key Responsibilities:**
- **Node Controller:** Notices when nodes go down.
- **Job Controller:** Watches for Job objects and creates Pods to run them.
- **EndpointSlice Controller:** Populates EndpointSlices for services.

## Data Flow & Communication

### Primary Data Flows
1. **Desired State Update:** User -> kubectl -> API Server -> etcd.
2. **Scheduling Loop:** API Server (Watch) -> Scheduler -> API Server (Binding) -> etcd.
3. **Execution Loop:** API Server (Watch) -> Kubelet -> Container Runtime (CRI).

### Communication Patterns
- **Synchronous:** REST over HTTP/gRPC for API calls.
- **Asynchronous:** The **Watch** mechanism allows components to be notified of changes in real-time without polling.
- **Persistence:** All cluster state is stored in **etcd**.

## Directory Structure Guide

```
kubernetes/
├── cmd/                    # Entry points for all binaries
│   ├── kube-apiserver/     # Control plane API server
│   ├── kubelet/            # Node agent
│   └── kubectl/            # CLI tool
├── pkg/                    # Core library code (private to this repo)
│   ├── apis/               # Internal API types and conversions
│   ├── controller/         # Logic for various controllers
│   └── kubelet/            # Detailed implementation of the kubelet
├── api/                    # OpenAPI and Swagger definitions
├── staging/                # Published libraries (k8s.io/*)
│   ├── src/k8s.io/api/     # Versioned API types
│   ├── src/k8s.io/client-go/# Go client library
│   └── src/k8s.io/apiserver/# API server framework
├── test/                   # Integration and E2E tests
└── hack/                   # Scripts for building, linting, and codegen
```

## Key Interfaces & Abstractions

### Interface: CRI (Container Runtime Interface)
**Location:** `staging/src/k8s.io/cri-api/pkg/apis/services.go` (approx)
**Purpose:** Standard interface between the Kubelet and the container runtime.
**Implementations:** containerd, CRI-O, Docker (via shim).

### Interface: Informer
**Location:** `staging/src/k8s.io/client-go/informers/`
**Purpose:** Provides a local cache and event notifications for API objects to minimize API server load.

## Development Guide

### Building
Use the provided Makefile:
```bash
make
```
To build a specific component:
```bash
make WHAT=cmd/kube-apiserver
```

### Testing
- **Unit Tests:** `go test ./pkg/scheduler/...`
- **Integration Tests:** `make test-integration`
- **E2E Tests:** Use `hack/ginkgo-e2e.sh` or `kind`.

## Glossary
- **Pod:** The smallest deployable unit in Kubernetes, containing one or more containers.
- **Node:** A worker machine (VM or physical) in the cluster.
- **CRD (Custom Resource Definition):** A way to extend the Kubernetes API with your own objects.
- **Admission Controller:** A piece of code that intercepts requests to the API server prior to persistence.
