PY = python3
SOURCE = tests/tests.py
VENV = test_venv

.PHONY: test clear

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

clear:
	@rm -rf $(VENV)
