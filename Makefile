.PHONY: install index dashboard api test lint
install:
	pip install -e .
index:
	python scripts/build_index.py
dashboard:
	streamlit run dashboard.py
api:
	uvicorn app.api.main:app --reload --port 8000
test:
	pytest -q
lint:
	ruff check app tests
