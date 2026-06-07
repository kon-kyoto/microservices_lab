PY = python3
SOURCE = tests/tests.py
VENV = test_venv

.PHONY: test clear build-kube

start: test format clear
rebuild: clear build-kube

format:
	@if [ ! -d $(VENV) ]; then \
		$(PY) -m venv $(VENV); \
		./$(VENV)/bin/pip install --upgrade pip; \
		./$(VENV)/bin/pip install --no-cache-dir -r tests/requirements.txt; \
	fi
	@./$(VENV)/bin/black infrastructure/ services/ tests/ --line-length 88; \

test:
	@if [ ! -d $(VENV) ]; then \
		$(PY) -m venv $(VENV); \
		./$(VENV)/bin/pip install --upgrade pip; \
		./$(VENV)/bin/pip install --no-cache-dir -r tests/requirements.txt; \
	fi
	@./$(VENV)/bin/pytest $(SOURCE) -v --tb=short --disable-warnings

build-kube:
	minikube start -p orderapp --cpus 2 --memory 3072
	docker build -f ./gateway/Dockerfile . -t ordernginx:1.0
	docker build -f ./services/auth/Dockerfile ./services/auth/ -t orderauth:1.0
	docker build -f ./services/users/Dockerfile ./services/users/ -t orderusers:1.0
	docker build -f ./services/orders/Dockerfile ./services/orders/ -t orderorders:1.0
	minikube image load postgresql:15-alpine -p orderapp
	minikube image load redis:7-alpine -p orderapp
	minikube image load ordernginx:1.0 -p orderapp
	minikube image load orderauth:1.0 -p orderapp
	minikube image load orderusers:1.0 -p orderapp
	minikube image load orderorders:1.0 -p orderapp
	kubectl create namespace app-ns
	kubectl create configmap init-db --from-file=./infrastructure/postgres/init.sql -n app-ns
	kubectl apply -f deployment.yaml
	kubectl apply -f service.yaml
	kubectl apply -f pvc.yaml
clear:
	rm -rf $(VENV)
	minikube delete -p orderapp
	docker image rm ordernginx:1.0
	docker image rm orderauth:1.0
	docker image rm orderusers:1.0
	docker image rm orderorders:1.0

