# Microservices Lab → Kubernetes (Kubespray + GitLab CI)

Учебный проект: микросервисное приложение (auth, users, orders) на Flask + PostgreSQL + Redis, развёрнутое в Kubernetes-кластере, созданном через Terraform и Kubespray. CI/CD — GitLab CI, образы — в GitLab Container Registry.

## Архитектура

```
Terraform (Yandex Cloud)
   └── VM: 1 master + 2 worker
         └── Kubespray (Ansible)
               └── Kubernetes cluster
                     └── app-ns: auth, users, orders, gateway, frontend
                           ├── PostgreSQL (PVC)
                           ├── Redis (emptyDir)
                           └── Ingress (nginx)
```

- **Ingress** — `orderapp.local` → `frontend-gateway:80`
- **Registry** — GitLab Container Registry (`172.17.0.1:5050`)
- **Secrets** — Sealed Secrets (контроллер в `kube-system`)
- **Мониторинг** — план (kube-prometheus-stack + Loki)

## Стек

| Слой | Технологии |
|------|------------|
| IaC | Terraform (Yandex Cloud provider) |
| Кластер | Kubespray (Ansible), containerd |
| Приложение | Python 3.12, Flask, gunicorn |
| БД | PostgreSQL 15, Redis 7 |
| Gateway | nginx (reverse proxy + static) |
| CI/CD | GitLab CI, Docker-in-Docker |
| Registry | GitLab Container Registry (HTTPS, self-signed) |

## Структура репозитория

```
.
├── terraform/              # VM + inventory для Kubespray
│   ├── main.tf
│   ├── modules/vm_module/
│   └── cloud-init.yaml
├── kubespray/              # клон upstream, inventory вынесен
├── k8s/                    # манифесты
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── pvc.yaml
│   └── sealed-secrets.yaml
├── services/               # auth, users, orders (Flask)
├── gateway/                # nginx.conf + Dockerfile
├── frontend/               # статика (HTML/CSS/JS)
├── infrastructure/postgres/init.sql
├── tests/                  # pytest + requests
├── .gitlab-ci.yml
└── Makefile
```

## Быстрый старт (с нуля)

### 1. Инфраструктура (Terraform)

```bash
cd terraform
export TF_VAR_yc_token=$(yc iam create-token)
export TF_VAR_yc_cloud_id=$(yc config get cloud-id)
export TF_VAR_yc_folder_id=$(yc config get folder-id)
terraform init && terraform apply -auto-approve
```

Terraform создаёт VM и генерирует inventory для Kubespray.

### 2. Кластер (Kubespray)

```bash
cd kubespray
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
ansible-playbook -i ../inventory/mycluster/inventory.ini cluster.yml -b -v
```

### 3. Kubeconfig

```bash
MASTER_IP=$(cd terraform && terraform output -raw master_external_ip)
ssh hex@$MASTER_IP "sudo cat /etc/kubernetes/admin.conf" > ~/.kube/config-kubespray
sed -i "s/127.0.0.1/$MASTER_IP/g" ~/.kube/config-kubespray
export KUBECONFIG=~/.kube/config-kubespray
kubectl get nodes
```

### 4. Настройка containerd (доверие к Registry)

В `group_vars/all/containerd.yml` (рядом с inventory):

```yaml
containerd_registries_mirrors:
  - prefix: "172.17.0.1:5050"
    mirrors:
      - host: "https://172.17.0.1:5050"
        capabilities: ["pull", "resolve"]
        skip_verify: true
```

```bash
ansible-playbook -i ../inventory/mycluster/inventory.ini cluster.yml -b --tags container-engine
```

### 5. GitLab CI/CD Variables

В GitLab → **Settings → CI/CD → Variables**:

| Key | Type | Значение |
|-----|------|----------|
| `KUBECONFIG_CONTENT` | File | содержимое `~/.kube/config-kubespray` |
| `GITLAB_REGISTRY_TOKEN` | Masked | PAT с правами `read_registry` |

### 6. Деплой

```bash
git push origin master
```

CI:
1. **validate** — black, terraform fmt, yamllint
2. **build** — 4 образа → GitLab Registry (тег `$CI_COMMIT_SHORT_SHA`), только при изменениях в `services/`, `gateway/`, `frontend/`
3. **deploy** — **manual**: `kubectl apply` + `kubectl set image` + `rollout status`

Нажми **Run** на job `deploy-to-kubespray` в GitLab UI.

## Локальная разработка

```bash
make build           # docker build + minikube + kubectl apply
make test            # pytest (port-forward на :8080)
make format          # black + prettier + terraform fmt + yamllint
make update          # rebuild images + rollout restart
make rebuild         # clear + build (с нуля)
make clear           # удалить minikube, образы, venv
```

Тесты ходят на `http://localhost:8080` (через `kubectl port-forward`).

## Секреты

- `secret.yaml` — исходник (в `.gitignore`), **не коммитить**.
- `k8s/sealed-secrets.yaml` — зашифрованная версия, коммитится.
- Генерация: `kubeseal --cert pub-cert.pem --format yaml < secret.yaml > k8s/sealed-secrets.yaml`.

## Что сделано / что в планах

**Сделано:**
- Terraform: VM + inventory
- Kubespray: 1 master + 2 worker
- GitLab CI: validate → build → manual deploy
- GitLab Container Registry (HTTPS, self-signed)
- Sealed Secrets
- Ingress (nginx)
- Probes: startupProbe, readinessProbe (/ready), livenessProbe (/health)
- initContainer: wait-for-postgres/redis/auth

**В планах:**
- Мониторинг: kube-prometheus-stack + Loki
- HPA на orders-service
- NetworkPolicy (deny-by-default)
- ArgoCD (GitOps)
- 3 control-plane (HA)

## Известные ограничения

- **1 control-plane** — не HA. Для HA нужно 3 master (Kubespray).
- **Redis на emptyDir** — данные теряются при рестарте пода.
- **Self-signed сертификат** Registry — `skip_verify: true` в containerd.
- **`kubectl set image` для всех 4 сервисов** при manual deploy — образы собираются все, если изменилась любая из папок.

## Полезные команды

```bash
# статус кластера
kubectl get nodes -o wide
kubectl get pods -n app-ns

# логи
kubectl logs -n app-ns deploy/auth-service --tail=50
kubectl logs -n app-ns deploy/auth-service --previous --tail=50

# rollout
kubectl rollout restart -n app-ns deploy
kubectl rollout status -n app-ns deploy/auth-service --timeout=180s

# Registry
curl -k https://172.17.0.1:5050/v2/
```

## Лицензия

MIT
