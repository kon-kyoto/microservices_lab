PY = python3
SOURCE = tests/tests.py
VENV = test_venv
NS = app-ns

# ANSI цвета (bash/zsh)
GREEN  = \033[0;32m
YELLOW = \033[0;33m
RED    = \033[0;31m
CYAN   = \033[0;36m
NC     = \033[0m
SEP    = ==========================================

.PHONY: all build update rebuild test format port-forward \
        build-docker build-minikube build-kube update-kube clear

all: build

# ---------------------------------------------------------------
# Агрегаторы
# ---------------------------------------------------------------

build: build-docker build-minikube build-kube
	@printf "$(GREEN)$(SEP)$(NC)\n"
	@printf "$(GREEN)DONE: BUILD (all images loaded, k8s applied)$(NC)\n"
	@printf "$(GREEN)$(SEP)$(NC)\n"

update: build-docker build-minikube update-kube
	@printf "$(GREEN)$(SEP)$(NC)\n"
	@printf "$(GREEN)DONE: UPDATE (images rebuilt, deployment restarted)$(NC)\n"
	@printf "$(GREEN)$(SEP)$(NC)\n"

rebuild: clear build
	@printf "$(GREEN)$(SEP)$(NC)\n"
	@printf "$(GREEN)DONE: REBUILD (everything from scratch)$(NC)\n"
	@printf "$(GREEN)$(SEP)$(NC)\n"

# ---------------------------------------------------------------
# Docker
# ---------------------------------------------------------------

build-docker:
	@printf "$(CYAN)$(SEP)$(NC)\n"
	@printf "$(CYAN)START BUILD-DOCKER$(NC)\n"
	@printf "$(CYAN)$(SEP)$(NC)\n"
	docker build -f ./gateway/Dockerfile . -t ordernginx:1.0
	docker build -f ./services/auth/Dockerfile ./services/auth/ -t orderauth:1.0
	docker build -f ./services/users/Dockerfile ./services/users/ -t orderusers:1.0
	docker build -f ./services/orders/Dockerfile ./services/orders/ -t orderorders:1.0
	@printf "$(GREEN)$(SEP)$(NC)\n"
	@printf "$(GREEN)END BUILD-DOCKER$(NC)\n"
	@printf "$(GREEN)$(SEP)$(NC)\n"

# ---------------------------------------------------------------
# Minikube
# ---------------------------------------------------------------

build-minikube:
	@printf "$(CYAN)$(SEP)$(NC)\n"
	@printf "$(CYAN)START BUILD-MINIKUBE$(NC)\n"
	@printf "$(CYAN)$(SEP)$(NC)\n"
	minikube start -p orderapp --cpus 2 --memory 3072
	kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.36.1/controller.yaml
	kubectl wait --for=condition=Available deployment/sealed-secrets-controller -n kube-system --timeout=120s
	minikube image load ordernginx:1.0 -p orderapp
	minikube image load orderauth:1.0 -p orderapp
	minikube image load orderusers:1.0 -p orderapp
	minikube image load orderorders:1.0 -p orderapp
	minikube addons enable ingress -p orderapp
	@printf "$(GREEN)$(SEP)$(NC)\n"
	@printf "$(GREEN)END BUILD-MINIKUBE$(NC)\n"
	@printf "$(GREEN)$(SEP)$(NC)\n"

# ---------------------------------------------------------------
# Kubernetes
# ---------------------------------------------------------------

build-kube:
	@printf "$(CYAN)$(SEP)$(NC)\n"
	@printf "$(CYAN)START BUILD-KUBE$(NC)\n"
	@printf "$(CYAN)$(SEP)$(NC)\n"
	kubectl create namespace $(NS) --dry-run=client -o yaml | kubectl apply -f -
	kubectl create configmap init-db --from-file=./infrastructure/postgres/init.sql -n $(NS) \
	  --dry-run=client -o yaml | kubectl apply -f -
	kubeseal --format yaml < secret.yaml > sealed-secrets.yaml
	kubectl apply -f k8s/sealed-secrets.yaml
	kubectl apply -f k8s/pvc.yaml
	kubectl apply -f k8s/deployment.yaml
	kubectl apply -f k8s/service.yaml
	kubectl apply -f k8s/ingress.yaml
	@printf "$(RED)Add this line to /etc/hosts:$(NC)\n"
	@printf "$(RED)  $$(minikube ip -p orderapp) orderapp.local$(NC)\n"
	@printf "$(GREEN)$(SEP)$(NC)\n"
	@printf "$(GREEN)END BUILD-KUBE$(NC)\n"
	@printf "$(GREEN)$(SEP)$(NC)\n"

update-kube:
	@printf "$(CYAN)$(SEP)$(NC)\n"
	@printf "$(CYAN)START UPDATE-KUBE$(NC)\n"
	@printf "$(CYAN)$(SEP)$(NC)\n"
	kubectl rollout restart -n $(NS) deploy
	kubectl rollout status -n $(NS) deploy --timeout=180s
	@printf "$(GREEN)$(SEP)$(NC)\n"
	@printf "$(GREEN)END UPDATE-KUBE$(NC)\n"
	@printf "$(GREEN)$(SEP)$(NC)\n"

# ---------------------------------------------------------------
# Tests & format
# ---------------------------------------------------------------

format:
	@printf "$(CYAN)$(SEP)$(NC)\n"
	@printf "$(CYAN)START FORMAT$(NC)\n"
	@printf "$(CYAN)$(SEP)$(NC)\n"
	@printf "$(YELLOW)[1/4] Python (black)$(NC)\n"
	@if [ ! -d $(VENV) ]; then \
		$(PY) -m venv $(VENV); \
		./$(VENV)/bin/pip install --upgrade pip; \
		./$(VENV)/bin/pip install --no-cache-dir -r tests/requirements.txt; \
	fi
	@./$(VENV)/bin/black infrastructure/ services/ tests/
	@printf "$(YELLOW)[2/4] JS/HTML/YAML (prettier)$(NC)\n"
	@if ! command -v npx >/dev/null 2>&1; then \
		printf "$(RED)npx not found. Install Node.js first.$(NC)\n"; \
		exit 1; \
	fi
	@cd frontend && npx --yes prettier@3.3.3 --write "js/**/*.js" "*.html" "css/**/*.css"
	@npx --yes prettier@3.3.3 --write "k8s/**/*.yaml" ".gitlab-ci.yml"
	@printf "$(YELLOW)[3/4] Terraform (fmt)$(NC)\n"
	@if command -v terraform >/dev/null 2>&1; then \
		cd terraform && terraform fmt -recursive; \
	else \
		printf "$(RED)terraform not found. Skipping.$(NC)\n"; \
	fi
	@printf "$(YELLOW)[4/4] YAML (yamllint check)$(NC)\n"
	@if command -v yamllint >/dev/null 2>&1; then \
		yamllint -d relaxed k8s/ .gitlab-ci.yml || \
		printf "$(RED)yamllint found issues (not auto-fixable). Fix manually.$(NC)\n"; \
	else \
		printf "$(RED)yamllint not found. Install via 'pip install yamllint'.$(NC)\n"; \
	fi
	@printf "$(GREEN)$(SEP)$(NC)\n"
	@printf "$(GREEN)END FORMAT$(NC)\n"
	@printf "$(GREEN)$(SEP)$(NC)\n"

test:
	@printf "$(CYAN)$(SEP)$(NC)\n"
	@printf "$(CYAN)START TEST$(NC)\n"
	@printf "$(CYAN)$(SEP)$(NC)\n"
	@if [ ! -d $(VENV) ]; then \
		$(PY) -m venv $(VENV); \
		./$(VENV)/bin/pip install --upgrade pip; \
		./$(VENV)/bin/pip install --no-cache-dir -r tests/requirements.txt; \
	fi
	@printf "$(YELLOW)Starting port-forward on :8080 ...$(NC)\n"
	@kubectl port-forward -n $(NS) svc/frontend-gateway 8080:80 &>/dev/null & \
		PF_PID=$$!; \
		sleep 2; \
		./$(VENV)/bin/pytest $(SOURCE) -v --tb=short --disable-warnings; \
		RC=$$?; \
		kill $$PF_PID 2>/dev/null || true; \
		if [ $$RC -eq 0 ]; then \
			printf "$(GREEN)$(SEP)$(NC)\n"; \
			printf "$(GREEN)END TEST (PASSED)$(NC)\n"; \
			printf "$(GREEN)$(SEP)$(NC)\n"; \
		else \
			printf "$(RED)$(SEP)$(NC)\n"; \
			printf "$(RED)END TEST (FAILED, exit $$RC)$(NC)\n"; \
			printf "$(RED)$(SEP)$(NC)\n"; \
		fi; \
		exit $$RC

port-forward:
	@printf "$(CYAN)$(SEP)$(NC)\n"
	@printf "$(CYAN)START PORT-FORWARD (Ctrl+C to stop)$(NC)\n"
	@printf "$(CYAN)$(SEP)$(NC)\n"
	kubectl port-forward -n $(NS) svc/frontend-gateway 8080:80

# ---------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------

clear:
	@printf "$(YELLOW)$(SEP)$(NC)\n"
	@printf "$(YELLOW)START CLEAR$(NC)\n"
	@printf "$(YELLOW)$(SEP)$(NC)\n"
	rm -rf $(VENV)
	minikube delete -p orderapp || true
	docker image rm ordernginx:1.0 orderauth:1.0 orderusers:1.0 orderorders:1.0 || true
	@printf "$(GREEN)$(SEP)$(NC)\n"
	@printf "$(GREEN)END CLEAR$(NC)\n"
	@printf "$(GREEN)$(SEP)$(NC)\n"
