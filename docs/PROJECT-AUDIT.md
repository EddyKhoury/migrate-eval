# migrate-eval — Project Audit

This document records the implementation history, technical decisions, tests, problems, fixes, and remaining work for the migrate-eval project.

It allows development to continue across separate ChatGPT conversations without losing context.

---

# Milestone 0 — Setup

## Goal

Create the repository, Python environment, Docker execution environment, local model environment, and HumanEval-X dataset required by migrate-eval.

## Exit Criterion

Milestone 0 is complete when:

- `make setup` runs successfully.
- Python project environment is configured.
- Go Docker image builds successfully.
- Ollama is installed and a local coder model responds.
- HumanEval-X Java and Go data are downloaded.
- Dataset count is confirmed as 164 problems.

---

## Step 0.1 — Repository Skeleton

### Status

Completed.

### Git

Repository initialized with:

    git init

Current branch:

    main

### Directories Created

    src/migrate_eval/models/
    scripts/
    tests/
    data/
    results/
    docs/

### Files Created

    README.md
    pyproject.toml
    Makefile
    Dockerfile.go
    .gitignore
    docs/PROJECT-AUDIT.md

### Design Decision

The project uses a Python `src/` layout.

Application code will live under:

    src/migrate_eval/

This keeps the main application separate from tests, scripts, datasets, results, and documentation.

### Note

Git does not track empty directories. Therefore folders such as `src/`, `tests/`, and `data/` may not appear in `git status` until files are added to them.

---

## Step 0.2 — Git Ignore Configuration

### Status

Completed.

### Purpose

The `.gitignore` prevents local environments, secrets, generated files, downloaded benchmark data, caches, and temporary files from accidentally entering Git history.

### Important Rules

Ignored:

    .venv/
    venv/
    .env
    .env.*
    __pycache__/
    .pytest_cache/
    .DS_Store
    data/humaneval_x/
    results/

Exception:

    !.env.example

### Security Decision

API keys must never be committed to Git.

Credentials will later be stored in a local `.env` file.

### Verification

`git status` successfully showed the expected project files as untracked.

---

## Current Milestone Status

Milestone 0: IN PROGRESS

### Completed

- Git repository initialized.
- Base directory structure created.
- Base files created.
- `.gitignore` configured.
- Git behavior verified.
- Project audit initialized.

### Remaining

- Configure `pyproject.toml`.
- Add Python package initialization.
- Create Python virtual environment.
- Install dependencies.
- Configure Makefile.
- Create and build Go Docker image.
- Install and configure Ollama.
- Pull local coder model.
- Download HumanEval-X Java and Go data.
- Confirm 164 benchmark problems.
- Make `make setup` work end-to-end.

## Next Action

Configure `pyproject.toml`.

---

## Step 0.4 — Python Environment

### Status

Completed.

### Python Version

The macOS system Python was:

    Python 3.9.6
    /usr/bin/python3

This was too old for the project requirement of Python 3.11+.

Homebrew Python 3.12 was available:

    Python 3.12.14
    /opt/homebrew/bin/python3.12

### Problem Encountered

Creating the virtual environment initially failed because the project path contained a colon:

    AI:LLM

Python refused to create the environment because `:` is a PATH separator.

### Fix

The project was moved to:

    /Users/Shared/Files From d.localized/AI-LLM/migrate-eval

The folder name was changed from:

    AI:LLM

to:

    AI-LLM

### Virtual Environment

Created with:

    python3.12 -m venv .venv

Activated with:

    source .venv/bin/activate

### Verification

Python:

    Python 3.12.14

Interpreter:

    /Users/Shared/Files From d.localized/AI-LLM/migrate-eval/.venv/bin/python

### Design Decision

The project will use Python 3.12 inside a local `.venv`.

The macOS system Python will not be modified.

## Next Action

Configure `pyproject.toml`.

---

## Step 0.6 — Project Dependencies

### Status

Completed.

### Installation

The project was installed in editable mode with development dependencies:

    python -m pip install -e ".[dev]"

### Why Editable Mode

Editable mode allows changes under:

    src/migrate_eval/

to be immediately available without reinstalling the package after every code change.

### Dependencies Installed

Runtime:

- openai
- httpx
- pandas
- matplotlib
- typer
- python-dotenv

Development:

- pytest

### Verification

Dependency import check passed:

    dependencies OK

Project package import check passed:

    migrate_eval import OK

### Design Decision

The project uses `pyproject.toml` as the central Python project configuration.

The package source lives under:

    src/migrate_eval/

The minimum supported Python version is:

    Python 3.11+

Current development environment:

    Python 3.12.14

## Next Action

Configure the Makefile.

---

## Step 0.8 — Makefile and Smoke Test

### Status

Completed.

### Makefile Targets Added

`setup`

- Creates `.venv`
- Upgrades pip
- Installs the project in editable mode
- Installs development dependencies

`test`

- Runs pytest using the project's virtual environment

`clean`

- Removes pytest cache
- Removes Python `__pycache__` directories

### Smoke Test

Created:

    tests/test_smoke.py

Purpose:

Verify that the installed Python package can be imported successfully.

Test:

    test_package_imports

### Verification

Command:

    make setup

Result:

Completed successfully.

Command:

    make test

Result:

    1 passed

### Problem Encountered

Before the Makefile targets were implemented, running:

    make setup
    make test

returned:

    No rule to make target `setup'
    No rule to make target `test'

### Cause

The Makefile existed but was empty.

### Fix

Implemented the `setup`, `test`, and `clean` targets.

### Important Note

The current `make setup` only configures the Python environment.

Before Milestone 0 is complete, it will be extended so that the full project setup also handles the remaining required environment preparation.

## Next Action

Configure the Go Docker execution environment.

---

## Step 0.11 — Go Docker Environment

### Status

Completed.

### Docker Environment

Docker was already installed and running.

Verified:

    Docker version 29.7.2

Docker server:

    Docker Desktop

Architecture:

    aarch64

This confirms the development machine is using Apple Silicon.

### Docker Image

Created:

    migrate-eval-go:latest

Dockerfile:

    Dockerfile.go

Base image:

    golang:1.25-bookworm

### Security Design

A non-root Linux user named:

    runner

was created inside the container.

Generated Go code will eventually execute under this non-root user rather than as root.

Working directory:

    /work

### Build Command

    docker build -t migrate-eval-go -f Dockerfile.go .

### Verification

Command:

    docker run --rm migrate-eval-go

Result:

    go version go1.25.14 linux/arm64

Image verification:

    docker image ls migrate-eval-go

Image successfully exists locally.

### Important Note

CPU, memory, network, and execution timeout restrictions are not implemented yet.

Those restrictions belong to Milestone 1 when the Go test runner is implemented.

## Next Action

Verify Ollama installation and configure the local coding model.

---

## Step 0.13–0.14 — Ollama and Local Coding Model

### Status

Completed.

### Ollama Installation

Ollama was not initially installed.

Installed using:

    brew install ollama

Installed version:

    Ollama 0.33.3

### Ollama Service

Started with:

    brew services start ollama

Verification:

    ollama --version

Result:

    ollama version is 0.33.3

### Hardware

Mac unified memory:

    51539607552 bytes

Equivalent to:

    48 GB

### Local Model Decision

Selected:

    qwen2.5-coder:14b

Reason:

The machine has enough memory to comfortably run the 14B model while keeping evaluation speed practical.

A 7B model would be lighter but weaker.

A 32B model could fit, but would make the later full benchmark significantly slower.

### Model Installation

Command:

    ollama pull qwen2.5-coder:14b

Downloaded model size:

    9.0 GB

### Verification

Command:

    ollama run qwen2.5-coder:14b "Return only the word READY"

Result:

    READY

Local model execution is working successfully.

## Next Action

Set up and verify the HumanEval-X dataset.

---

## Step 0.15–0.16 — HumanEval-X Dataset

### Status

Completed.

### Dataset Source

HumanEval-X benchmark data was configured for the two languages required by the core project:

- Java — source language
- Go — target language

### Download Script

Created:

    scripts/fetch_data.py

The script downloads:

    data/humaneval_x/humaneval_java.jsonl.gz
    data/humaneval_x/humaneval_go.jsonl.gz

### Idempotent Download Behavior

The script checks whether each dataset file already exists.

Existing files are not downloaded again.

### Validation

Each gzip JSONL file is opened and every line is parsed as JSON.

Expected benchmark size:

    164 problems per language

Verified:

    java: 164 problems
    go: 164 problems

Result:

    HumanEval-X verification successful.

### Dataset Structure

Java problem fields:

    task_id
    prompt
    canonical_solution
    test
    text
    declaration
    example_test

Go problem fields:

    task_id
    prompt
    import
    docstring
    declaration
    canonical_solution
    test
    test_setup
    example_test

### Pairing Observation

First task IDs:

    Java/0
    Go/0

The language prefixes differ, but the numeric benchmark index `/0` corresponds to the same benchmark problem.

Later, `dataset.py` will pair benchmark entries using this numeric task index.

### Intended Data Flow

For each benchmark problem:

Java provides:

    source implementation

Go provides:

    target declaration/signature
    canonical Go solution
    target Go tests

The canonical Go solution will first be used in Milestone 1 to validate the test oracle before any LLM-generated migration is trusted.

## Next Action

Make `make setup` perform the complete Milestone 0 environment setup and verification.

---

# Milestone 0 — Final Verification

## Status

COMPLETED.

## Environment

Python:

    Python 3.12.14

Virtual environment:

    .venv

Project installation:

    Editable installation via pyproject.toml

## Dataset

HumanEval-X languages configured:

- Java
- Go

Verified benchmark size:

    Java: 164 problems
    Go: 164 problems

Dataset verification result:

    HumanEval-X verification successful.

## Docker

Docker Desktop is installed and running.

Go sandbox image:

    migrate-eval-go:latest

Container Go version:

    go1.25.14 linux/arm64

Container uses a non-root `runner` user.

Full CPU, memory, network, and timeout sandbox restrictions will be implemented in Milestone 1.

## Ollama

Installed version:

    0.33.3

Service:

    Running

Local coding model:

    qwen2.5-coder:14b

Model size:

    9.0 GB

Model response test:

    READY

## Makefile

Implemented targets:

    make setup
    make test
    make clean

`make setup` currently performs:

1. Python virtual environment creation
2. Python dependency installation
3. HumanEval-X download/verification
4. Go Docker image build
5. Ollama/model verification

Final setup result:

    migrate-eval setup complete.

## Tests

Current harness tests:

    1 passed

Current test:

    tests/test_smoke.py

This is only a setup smoke test. The main harness test suite will be built during later milestones.

## Licence

MIT licence added.

## Milestone 0 Exit Criteria

- [x] Repository initialized
- [x] MIT licence added
- [x] `.gitignore` configured
- [x] Python 3.11+ configured
- [x] Virtual environment configured
- [x] Dependencies install correctly
- [x] `make setup` runs end-to-end
- [x] HumanEval-X Java dataset verified
- [x] HumanEval-X Go dataset verified
- [x] 164 problems confirmed for each language
- [x] Docker image builds
- [x] Go runs inside Docker
- [x] Ollama installed and running
- [x] Local coder model downloaded and verified
- [x] `make test` passes

## Problems Encountered During Milestone 0

### Python version

macOS system Python was 3.9.6.

Resolved by using Homebrew Python 3.12.14.

### Invalid project path

Original path contained:

    AI:LLM

The colon prevented Python from creating a virtual environment.

Resolved by moving the project to:

    AI-LLM/migrate-eval

### Empty Makefile

Initial `make setup` and `make test` attempts failed because no targets existed.

Resolved by implementing the required Makefile targets.

### Ollama server not running

The Ollama CLI was installed but initially could not connect to a running instance.

Resolved with:

    brew services start ollama

## Final Milestone Result

Milestone 0 setup is complete and reproducible.

## Next Milestone

Milestone 1 — Oracle Works

Main objective:

Build a trustworthy Docker-based Go test runner and prove that canonical HumanEval-X Go solutions pass before any LLM-generated code is evaluated.

