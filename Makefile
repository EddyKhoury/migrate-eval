PYTHON ?= python3.12
VENV := .venv
VENV_PYTHON := $(VENV)/bin/python
OLLAMA_MODEL := qwen2.5-coder:14b
DOCKER_IMAGE := migrate-eval-go

MODEL ?= ollama:qwen2.5-coder:14b
N ?= 10
ITERS ?= 3
WORKERS ?= 1

.PHONY: setup python-setup data docker-build ollama-check run test clean

setup: python-setup data docker-build ollama-check
	@echo ""
	@echo "migrate-eval setup complete."

python-setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PYTHON) -m pip install -e ".[dev]"

data:
	$(VENV_PYTHON) scripts/fetch_data.py

docker-build:
	docker build -t $(DOCKER_IMAGE) -f Dockerfile.go .

ollama-check:
	@command -v ollama >/dev/null || (echo "Ollama is not installed."; exit 1)
	@ollama list | grep -q "$(OLLAMA_MODEL)" || (echo "Missing Ollama model: $(OLLAMA_MODEL)"; exit 1)
	@echo "Ollama ready: $(OLLAMA_MODEL)"

run:
	$(VENV)/bin/migrate-eval run \
		--model "$(MODEL)" \
		--n "$(N)" \
		--iters "$(ITERS)" \
		--workers "$(WORKERS)"

test:
	$(VENV_PYTHON) -m pytest

clean:
	rm -rf .pytest_cache
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +