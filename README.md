# 🐳 Microservices Lab → Kubernetes Cluster

[![Kubernetes](https://img.shields.io/badge/Kubernetes-1.28+-326CE5?logo=kubernetes&logoColor=white)](https://kubernetes.io/)
[![k3s](https://img.shields.io/badge/k3s-1.28+-FFC61A?logo=rancher&logoColor=black)](https://k3s.io/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

> **Эволюция проекта:** от `docker-compose` к production-готовому кластеру на **k3s** с 2 master и 2 worker нодами.  
> Основной фокус: безопасность, отказоустойчивость, оптимизация ресурсов и наблюдаемость.

---

## 📋 Содержание

1. [Архитектура кластера](#-архитектура-кластера)
2. [Технологический стек](#-технологический-стек)
3. [Структура проекта](#-структура-проекта)
4. [Безопасность](#-безопасность)
5. [Оптимизации](#-оптимизации)
6. [Запуск в кластере](#-запуск-в-кластере)
7. [Статусы ответов API](#-статусы-ответов-api)
8. [Планы развития](#-планы-развития)

---

## 🏗 Архитектура кластера

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

- **2 Master ноды:** обеспечение высокой доступности control plane (k3s с embedded etcd).
- **2 Worker ноды:** запуск микросервисов, PostgreSQL, Redis с репликацией.
- **Балансировка нагрузки:** через Ingress Controller + MetalLB (для on-prem).
- **Сетевая политика:** ограничение трафика между сервисами (Calico / Cilium).

---

## 🧩 Технологический стек

| Компонент          | Технологии                                                                 |
|--------------------|----------------------------------------------------------------------------|
| **Container**      | Docker, k3s (containerd)                                                  |
| **Orchestration**  | Kubernetes 1.28+, Helm, Kustomize                                         |
| **Service Mesh**   | (план) Istio / Linkerd для mTLS и observability                           |
| **API Gateway**    | OpenResty (Nginx + Lua) → маршрутизация, rate limiting, JWT               |
| **Microservices**  | Python 3.11 + Flask, JWT, psycopg2-binary                                 |
| **Databases**      | PostgreSQL 15 (StatefulSet + replicas), Redis 7 (sentinel)                |
| **Storage**        | Longhorn (распределенные блоки), S3-совместимое (minIO для логов)         |
| **Observability**  | Prometheus + Grafana + Loki (сбор логов), Tempo (traces)                  |
| **Security**       | k3s Hardening, OPA/Gatekeeper, Falco, Trivy (scan образов), Sealed Secrets|
| **Backup**         | Velero + restic (в S3)                                                    |
| **CI/CD**          | GitHub Actions + ArgoCD (GitOps)                                          |

---

## 📁 Структура проекта

```
microservices_lab/
├── kubernetes/                     # Манифесты для k8s
│   ├── base/                       # Базовые конфигурации
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── ingress.yaml
│   │   └── kustomization.yaml
│   ├── overlays/                   # Окружения
│   │   ├── dev/
│   │   ├── staging/
│   │   └── production/             # HA, реплики, ресурсы
│   ├── helm/                       # Helm charts
│   │   ├── auth-service/
│   │   ├── users-service/
│   │   └── orders-service/
│   ├── pv/                         # PersistentVolume + PVC
│   │   ├── postgres-pv.yaml
│   │   └── redis-pv.yaml
│   └── network-policies/           # Сетевая сегментация
├── services/                       # Микросервисы (Python)
├── gateway/                        # API Gateway (OpenResty)
├── infrastructure/                 # PostgreSQL, Redis (StatefulSets)
├── monitoring/                     # Prometheus, Grafana, Loki
├── security/                       # OPA policies, Falco rules
├── scripts/                        # Утилиты для деплоя и бэкапов
├── Makefile                        # Команды для cluster management
└── README.md
```

---

## 🔒 Безопасность

| Мера | Реализация |
|------|-------------|
| **mTLS** | Istio / Linkerd (шифрование сервис→сервис) |
| **JWT validation** | На уровне API Gateway (проверка перед маршрутизацией) |
| **Secrets** | Sealed Secrets + внешний провайдер (Bitwarden / Vault) |
| **Network Policies** | deny-by-default, только явные разрешения (e.g., gateway → auth) |
| **Pod Security** | `restricted` стандарт, запрет root, readOnlyRootFilesystem |
| **Image Scanning** | Trivy в CI, запрет уязвимых образов через OPA |
| **Runtime Security** | Falco (отслеживание аномалий в подах) |
| **Backup Encryption** | Velero + restic с шифрованием (AES-256) |

---

## ⚡ Оптимизации

- **Resource Limits & Requests** – точные значения CPU/RAM для каждого микросервиса.
- **HPA (Horizontal Pod Autoscaler)** – на основе CPU и пользовательских метрик (RPS).
- **Cluster Autoscaler** – авто-добавление worker нод при необходимости.
- **Cache** – Redis как L2 cache для профилей пользователей.
- **Readiness & Liveness Probes** – быстрый restart зависших подов.
- **Бинарные образы:** `python:3.11-slim-bookworm` + multi-stage сборка.
- **Anti-affinity** – распределение подов одного сервиса по разным нодам.
- **Spot instances** (для worker нод) – экономия 60-70%.

---

## 🚀 Запуск в кластере

### 1. Подготовка Ubuntu нод (22.04 / 24.04)

```bash
# На всех нодах (master/worker)
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="server" sh -s - \
  --cluster-init \
  --disable=traefik \
  --flannel-backend=none \
  --write-kubeconfig-mode=644
```

> Для второго мастера используйте `--server https://<master1>:6443 --token <token>`

### 2. Установка CNI (Calico или Cilium)

```bash
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.27/manifests/calico.yaml
```

### 3. Установка Ingress + MetalLB

```bash
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.13.12/config/manifests/metallb-native.yaml
# Настроить IP-пул для LoadBalancer
```

### 4. Деплой проекта

```bash
# Клонирование репозитория
git clone https://github.com/kon-kyoto/microservices_lab.git
cd microservices_lab

# Установка Helm-чартов
make deploy-all

# Или через Kustomize
make deploy-kustomize
```

### Makefile цели

```makefile
deploy-all:     # Установка всех сервисов + мониторинг
deploy-security # OPA, Falco, Sealed Secrets
deploy-backup   # Velero + restic
hpa-scale       # Активация горизонтального масштабирования
test-ha         # Симуляция отказа мастер-ноды
```

---

## 📊 Статусы ответов API

| Code | Name | When to use |
|------|------|--------------|
| 200 | OK | GET, PUT, DELETE успешно |
| 201 | Created | POST (ресурс создан) |
| 204 | No Content | DELETE успешен |
| 400 | Bad Request | Ошибка валидации |
| 401 | Unauthorized | Нет токена / неверный токен |
| 403 | Forbidden | Недостаточно прав |
| 404 | Not Found | Ресурс не найден |
| 409 | Conflict | Пользователь/email уже есть |
| 429 | Too Many Requests | Лимит попыток логина |
| 500 | Internal Server Error | Ошибка сервера |
| 503 | Service Unavailable | Зависимый сервис недоступен |

---

## 🗺 Планы развития

- [ ] **Istio service mesh** – mTLS, circuit breaking, canary deployments.
- [ ] **GitOps** – ArgoCD для синхронизации кластера с репозиторием.
- [ ] **Multi-cluster** – резервный кластер в облаке (k3s на AWS/GCP).
- [ ] **Chaos Mesh** – тестирование устойчивости к сбоям.
- [ ] **eBPF-мониторинг** – Cilium Hubble для сетевой наблюдаемости.
- [ ] **Full audit logging** – все API-вызовы + аудит администраторов.
- [ ] **Поддержка GPU** (для ML-сервисов) – если появятся в кластере.

---

## 👤 Контрибьютор

**[kon-kyoto](https://github.com/kon-kyoto)** – архитектура, разработка, DevOps.

---

## 📄 Лицензия

MIT © 2026

---

*Последнее обновление: 08.06.2026 — переход на k3s HA-кластер, фаза hardening.*
