PYTHON ?= python3

.PHONY: install test lint content check
install:
	$(PYTHON) -m pip install -r requirements-dev.txt

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check .

content:
	$(PYTHON) scripts/merge_lessons.py
	$(PYTHON) scripts/validate_content.py

check: lint test content

.PHONY: run smoke preflight
run:
	$(PYTHON) -m streamlit run app.py

smoke:
	$(PYTHON) scripts/smoke_test.py

preflight:
	$(PYTHON) scripts/check_deploy.py
