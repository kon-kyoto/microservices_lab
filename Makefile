PY = python3
SOURCE = tests/auth_tests.py
VENV = test_venv

.PHONY: test_all clear

test_all:
	@if [ ! -d $(VENV) ]; then \
		$(PY) -m venv $(VENV); \
		./$(VENV)/bin/pip install --upgrade pip; \
		./$(VENV)/bin/pip install --no-cache-dir -r tests/requirements.txt; \
	fi
	@./$(VENV)/bin/python $(SOURCE)

clear:
	@rm -rf $(VENV)
