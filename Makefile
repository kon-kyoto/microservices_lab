PY = python3
SOURCE = tests/tests.py
VENV = test_venv

.PHONY: test clear build-kube build-docker build-minikube update-kube build update rebuild

build: build-docker build-minikube build-kube
update: build-docker build-minikube update-kube
rebuild: clear build

format:
	@if [ ! -d $(VENV) ]; then \
		$(PY) -m venv $(VENV); \
		./$(VENV)/bin/pip install --upgrade pip; \
		./$(VENV)/bin/pip install --no-cache-dir -r tests/requirements.txt; \
	fi
	@./$(VENV)/bin/black infrastructure/ services/ tests/ --line-length 88
		
test:
	@if [ ! -d $(VENV) ]; then \
		$(PY) -m venv $(VENV); \
		./$(VENV)/bin/pip install --upgrade pip; \
		./$(VENV)/bin/pip install --no-cache-dir -r tests/requirements.txt; \
	fi
	kubectl port-forward -n app-ns svc/frontend-gateway 8080:80 || true
	@./$(VENV)/bin/pytest $(SOURCE) -v --tb=short --disable-warnings

build-docker:
	docker build -f ./gateway/Dockerfile . -t ordernginx:1.0
	docker build -f ./services/auth/Dockerfile ./services/auth/ -t orderauth:1.0
	docker build -f ./services/users/Dockerfile ./services/users/ -t orderusers:1.0
	docker build -f ./services/orders/Dockerfile ./services/orders/ -t orderorders:1.0
build-minikube:
	minikube start -p orderapp --cpus 2 --memory 3072
	minikube image load ordernginx:1.0 -p orderapp
	minikube image load orderauth:1.0 -p orderapp
	minikube image load orderusers:1.0 -p orderapp
	minikube image load orderorders:1.0 -p orderapp
build-kube:
	kubectl create namespace app-ns || true
	kubectl create configmap init-db --from-file=./infrastructure/postgres/init.sql -n app-ns || true
	kubectl apply -f sealed-secrets.yaml
	kubectl apply -f pvc.yaml
	kubectl apply -f deployment.yaml
	kubectl apply -f service.yaml
update-kube:
	kubectl rollout restart -n app-ns deploy
	kubectl rollout status -n app-ns deploy --timeout=180s
clear:
	rm -rf $(VENV)
	minikube delete -p orderapp	
	docker image rm ordernginx:1.0
	docker image rm orderauth:1.0
	docker image rm orderusers:1.0
	docker image rm orderorders:1.0
