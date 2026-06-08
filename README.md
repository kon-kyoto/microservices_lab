# 🐳 Microservices Lab → Kubernetes Cluster

[![Kubernetes](https://img.shields.io/badge/Kubernetes-1.28+-326CE5?logo=kubernetes&logoColor=white)](https://kubernetes.io/)
[![k3s](https://img.shields.io/badge/k3s-1.28+-FFC61A?logo=rancher&logoColor=black)](https://k3s.io/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://python.org/)
[![Docker](https://img.shields.io/badge/Docker-24.0+-2496ED?logo=docker&logoColor=white)](https://docker.com/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

> **Project Evolution:** from `docker-compose` to a production-ready cluster on **k3s** with 2 master and 2 worker nodes.  
> Main focus: security, high availability, resource optimization, and observability.

---

## 📋 Table of Contents

1. [Cluster Architecture](#-cluster-architecture)
2. [Technology Stack](#-technology-stack)
3. [Project Structure](#-project-structure)
4. [Security](#-security)
5. [Optimizations](#-optimizations)
6. [Deploy to Cluster](#-deploy-to-cluster)
7. [API Response Statuses](#-api-response-statuses)
8. [Roadmap](#-roadmap)

---

## 🏗 Cluster Architecture

```
┌─────────────────────────────────────────────┐
│           Ingress (Traefik / Nginx)          │
├─────────────────────────────────────────────┤
│            API Gateway (OpenResty)           │
├──────────────┬──────────────┬────────────────┤
│   Master-1   │   Master-2    │  k3s control  │
│  (control)   │   (control)   │    plane       │
├──────────────┼──────────────┼────────────────┤
│  Worker-1    │  Worker-2     │                │
│  (app, db)   │  (app, db)    │  (HA, etcd)    │
└──────────────┴──────────────┴────────────────┘
        ▲               ▲
        └───────┬───────┘
                │
         Persistent Volumes
         (Longhorn / Local)
```

- **2 Master nodes:** high availability for control plane (k3s with embedded etcd).
- **2 Worker nodes:** running microservices, PostgreSQL, Redis with replication.
- **Load balancing:** via Ingress Controller + MetalLB (for on-prem).
- **Network policies:** traffic restriction between services (Calico / Cilium).

---

## 🧩 Technology Stack

| Component          | Technologies                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| **Container**      | Docker, k3s (containerd)                                                   |
| **Orchestration**  | Kubernetes 1.28+, Helm, Kustomize                                          |
| **Service Mesh**   | (planned) Istio / Linkerd for mTLS and observability                       |
| **API Gateway**    | OpenResty (Nginx + Lua) → routing, rate limiting, JWT                      |
| **Microservices**  | Python 3.11 + Flask, JWT, psycopg2-binary                                  |
| **Databases**      | PostgreSQL 15 (StatefulSet + replicas), Redis 7 (sentinel)                 |
| **Storage**        | Longhorn (distributed block), S3-compatible (minIO for logs)               |
| **Observability**  | Prometheus + Grafana + Loki (log aggregation), Tempo (traces)              |
| **Security**       | k3s Hardening, OPA/Gatekeeper, Falco, Trivy (image scanning), Sealed Secrets|
| **Backup**         | Velero + restic (to S3)                                                    |
| **CI/CD**          | GitHub Actions + ArgoCD (GitOps)                                           |

---

## 📁 Project Structure

```
microservices_lab/
├── kubernetes/                     # k8s manifests
│   ├── base/                       # Base configurations
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── ingress.yaml
│   │   └── kustomization.yaml
│   ├── overlays/                   # Environments
│   │   ├── dev/
│   │   ├── staging/
│   │   └── production/             # HA, replicas, resources
│   ├── helm/                       # Helm charts
│   │   ├── auth-service/
│   │   ├── users-service/
│   │   └── orders-service/
│   ├── pv/                         # PersistentVolume + PVC
│   │   ├── postgres-pv.yaml
│   │   └── redis-pv.yaml
│   └── network-policies/           # Network segmentation
├── services/                       # Microservices (Python)
├── gateway/                        # API Gateway (OpenResty)
├── infrastructure/                 # PostgreSQL, Redis (StatefulSets)
├── monitoring/                     # Prometheus, Grafana, Loki
├── security/                       # OPA policies, Falco rules
├── scripts/                        # Deployment and backup utilities
├── Makefile                        # Cluster management commands
└── README.md
```

---

## 🔒 Security

| Measure | Implementation |
|---------|----------------|
| **mTLS** | Istio / Linkerd (service→service encryption) |
| **JWT validation** | At API Gateway level (validation before routing) |
| **Secrets** | Sealed Secrets + external provider (Bitwarden / Vault) |
| **Network Policies** | deny-by-default, explicit allows only (e.g., gateway → auth) |
| **Pod Security** | `restricted` standard, root prohibited, readOnlyRootFilesystem |
| **Image Scanning** | Trivy in CI, vulnerable images blocked via OPA |
| **Runtime Security** | Falco (anomaly detection in pods) |
| **Backup Encryption** | Velero + restic with AES-256 encryption |

---

## ⚡ Optimizations

- **Resource Limits & Requests** – precise CPU/RAM values for each microservice.
- **HPA (Horizontal Pod Autoscaler)** – based on CPU and custom metrics (RPS).
- **Cluster Autoscaler** – automatic worker node addition when needed.
- **Cache** – Redis as L2 cache for user profiles.
- **Readiness & Liveness Probes** – fast restart of hung pods.
- **Binary images:** `python:3.11-slim-bookworm` + multi-stage build.
- **Anti-affinity** – distributing pods of the same service across different nodes.
- **Spot instances** (for worker nodes) – 60-70% cost savings.

---

## 🚀 Deploy to Cluster

### 1. Prepare Ubuntu nodes (22.04 / 24.04)

```bash
# On all nodes (master/worker)
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="server" sh -s - \
  --cluster-init \
  --disable=traefik \
  --flannel-backend=none \
  --write-kubeconfig-mode=644
```

> For the second master, use `--server https://<master1>:6443 --token <token>`

### 2. Install CNI (Calico or Cilium)

```bash
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.27/manifests/calico.yaml
```

### 3. Install Ingress + MetalLB

```bash
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.13.12/config/manifests/metallb-native.yaml
# Configure IP pool for LoadBalancer
```

### 4. Deploy the project

```bash
# Clone the repository
git clone https://github.com/kon-kyoto/microservices_lab.git
cd microservices_lab

# Install Helm charts
make deploy-all

# Or via Kustomize
make deploy-kustomize
```

### Makefile targets

```makefile
deploy-all:     # Install all services + monitoring
deploy-security # OPA, Falco, Sealed Secrets
deploy-backup   # Velero + restic
hpa-scale       # Enable horizontal autoscaling
test-ha         # Simulate master node failure
```

---

## 📊 API Response Statuses

| Code | Name | When to use |
|------|------|--------------|
| 200 | OK | GET, PUT, DELETE successful |
| 201 | Created | POST (resource created) |
| 204 | No Content | DELETE successful |
| 400 | Bad Request | Validation error |
| 401 | Unauthorized | Missing / invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | User/email already exists |
| 429 | Too Many Requests | Login attempt limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Dependent service is down |

---

## 🗺 Roadmap

- [ ] **Istio service mesh** – mTLS, circuit breaking, canary deployments.
- [ ] **GitOps** – ArgoCD for cluster sync with repository.
- [ ] **Multi-cluster** – backup cluster in the cloud (k3s on AWS/GCP).
- [ ] **Chaos Mesh** – fault tolerance testing.
- [ ] **eBPF monitoring** – Cilium Hubble for network observability.
- [ ] **Full audit logging** – all API calls + admin audit.
- [ ] **GPU support** (for ML services) – if available in the cluster.

---

## 👤 Contributor

**[kon-kyoto](https://github.com/kon-kyoto)** – architecture, development, DevOps.

---

## 📄 License

MIT © 2026

---

*Last updated: 2026-06-08 — migration to k3s HA cluster, hardening phase.*
