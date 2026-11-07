.PHONY: setup dev test migrate worker eval docker-up docker-down clean

PYTHON ?= ./backend/venv/bin/python
PIP ?= ./backend/venv/bin/pip
UVICORN ?= ./backend/venv/bin/uvicorn
CELERY ?= ./backend/venv/bin/celery
PYTEST ?= ./backend/venv/bin/pytest

setup:
	@echo "Setting up environment..."
	@mkdir -p storage evaluation/labeled_dataset
	@if [ ! -d "backend/venv" ]; then \
		python3 -m venv backend/venv; \
	fi
	$(PIP) install --upgrade pip
	$(PIP) install -r backend/requirements.txt
	@echo "Setup complete. Copy .env.example to .env and configure credentials."

dev:
	@echo "Starting FastAPI backend development server..."
	cd backend && PYTHONPATH=. $(UVICORN) app.main:app --reload --host 0.0.0.0 --port 8000

worker:
	@echo "Starting Celery worker..."
	cd backend && PYTHONPATH=. $(CELERY) -A app.core.celery_app.celery_app worker --loglevel=info -c 2

test:
	@echo "Running test suite with coverage..."
	cd backend && PYTHONPATH=. $(PYTEST) tests/ -v --cov=app --cov-report=term-missing --cov-report=html

migrate:
	@echo "Running database migrations..."
	cd backend && PYTHONPATH=. $(PYTHON) -m alembic upgrade head

eval:
	@echo "Running evaluation benchmark..."
	PYTHONPATH=backend $(PYTHON) evaluation/run_eval.py

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf backend/.pytest_cache backend/htmlcov backend/.coverage
