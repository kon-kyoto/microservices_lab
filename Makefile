PY = python3
SOURCE = tests/tests.py
VENV = test_venv

.PHONY: test clear

start: test clear

test:
	@if [ ! -d $(VENV) ]; then \
		$(PY) -m venv $(VENV); \
		./$(VENV)/bin/pip install --upgrade pip; \
		./$(VENV)/bin/pip install --no-cache-dir -r tests/requirements.txt; \
	fi
	@./$(VENV)/bin/python $(SOURCE)

clear:
	@rm -rf $(VENV)
