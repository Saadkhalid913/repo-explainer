# Technology Stack

# Project: Kubernetes
# Last Updated: 2026-01-17

== Languages ==
- Go 1.25.0 - Primary language for all core components

== Core Frameworks & Libraries ==
- k8s.io/apiserver - Framework for building Kubernetes-style API servers
- k8s.io/client-go - Go clients for talking to Kubernetes API
- k8s.io/apimachinery - Shared logic for API serialization, schema, and more
- cobra - CLI framework for kubectl and other components
- gRPC - Used for internal communication (CRI, CSI, KMS)

== Build System ==
- Make - Entry point for build commands
- Docker/Buildkit - Used for containerized builds
- Go modules - Dependency management

== Testing ==
- Go testing package - Unit and integration tests
- Ginkgo/Gomega - BDD framework for End-to-End (e2e) tests

== Infrastructure & Deployment ==
- etcd - Distributed key-value store for cluster state
- Container Runtime (Docker, containerd, CRI-O) - Executes containers
- Cloud Providers (AWS, GCP, Azure, etc.) - Infrastructure backends

== Documentation ==
- Markdown - Primary documentation format
- Hugo - Used for the public website (kubernetes.io)
- OpenAPI/Swagger - API documentation

== External Dependencies (Runtime) ==
- etcd - State storage
- CoreDNS - Cluster DNS
- CNI Plugins - Networking
- CSI Drivers - Storage

== Development Tools ==
- kind (Kubernetes in Docker) - Local cluster development
- minikube - Local cluster development
- hack/ scripts - Various development utilities (linting, code generation, etc.)
