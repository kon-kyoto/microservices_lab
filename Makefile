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
	minicube image load ordernginx:1.0 -p micro

clear:
	rm -rf $(VENV)
	minikube delete -p micro
	docker image rm ordernginx:1.0

