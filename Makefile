PY = python3
SOURCE = tests/tests.py
VENV = test_venv

.PHONY: test clear build-kube

start: test format clear

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
	minikube start -p micro --cpus 2 --memory 3072
	docker build -f ./gateway/Dockerfile . -t ordernginx:1.0
	minikube image load ordernginx:1.0 -p micro
	kubectl create namespace app-ns
	kubectl create configmap nginx-gateway-config --from-file=./gateway/nginx.conf -n app-ns
	kubectl create configmap frontend-html --from-file=./frontend -n app-ns
	kubectl apply -f deployment.yaml
clear:
	rm -rf $(VENV)
	minikube delete -p micro
	docker image rm ordernginx:1.0

