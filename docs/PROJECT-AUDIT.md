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


---

# Milestone 1 — Oracle Works

## Goal

Build and validate a trustworthy Docker-based Go test oracle before evaluating any LLM-generated migrations.

The oracle must execute target-language Go code safely, distinguish important failure types, enforce resource limits, and correctly pass canonical HumanEval-X Go solutions.

## Step 1.1 — Runner Result Contract

### Status

Completed.

### Files Modified

    src/migrate_eval/runner.py
    tests/test_runner.py

### Implemented

Created the shared execution status taxonomy:

    PASS
    COMPILE_ERROR
    TEST_FAIL
    TIMEOUT
    EXTRACT_ERROR
    MODEL_ERROR

Created:

    RunResult

with fields:

    status
    stdout
    stderr
    duration

### Design Decision

The complete failure taxonomy is defined early so later components such as the Docker runner, repair loop, result logger, and evaluation plots all use the same result representation.

The Milestone 1 Go runner will directly produce:

    PASS
    COMPILE_ERROR
    TEST_FAIL
    TIMEOUT

The remaining statuses are reserved for later pipeline stages:

    EXTRACT_ERROR
    MODEL_ERROR

### Verification

Runner-specific tests passed.

Full harness test suite:

    3 passed

This confirms the new result contract did not break the Milestone 0 smoke test.

## Current Milestone Status

Milestone 1: IN PROGRESS

### Completed

- Runner status taxonomy defined.
- RunResult execution contract defined.
- Initial runner unit tests added.

### Next Action

Implement sandboxed Go execution inside Docker.

---

## Step 1.2 — Sandboxed Go PASS Execution

### Status

Completed.

### Files Modified

    src/migrate_eval/runner.py
    tests/test_runner.py

### Implemented

Created:

    run_go_tests(go_code, go_test)

The runner:

1. Creates an isolated temporary directory.
2. Writes:

       solution.go
       solution_test.go
       go.mod

3. Mounts the project into the Go Docker container.
4. Executes:

       go test ./... -count=1

5. Captures:

       stdout
       stderr
       duration
       exit code

6. Returns a RunResult.

### Sandbox Restrictions

Each generated program currently runs with:

    --cpus=1
    --memory=512m
    --network=none
    --read-only

The source workspace is mounted read-only:

    /work:ro

A temporary writable and executable filesystem is provided at:

    /tmp

This is needed because Go compiles and executes temporary test binaries during `go test`.

### Successful Verification

A simple Go function:

    Add(2, 3)

was tested inside Docker.

Expected result:

    5

Runner result:

    PASS

The integration test:

    test_run_go_tests_passes_valid_go_code

passed successfully.

### Problems Encountered

#### Missing GOTMPDIR

Initially the runner set:

    GOTMPDIR=/tmp/go-tmp

but that directory did not exist inside the temporary filesystem.

Error:

    go: creating work dir: stat /tmp/go-tmp: no such file or directory

Fix:

Removed the custom GOTMPDIR setting and allowed Go to use its normal temporary directory under `/tmp`.

#### Temporary Filesystem Not Executable

After the first fix, Go compiled the test binary successfully but could not execute it.

Error:

    fork/exec /tmp/go-build.../migrateeval.test: permission denied

Cause:

The `/tmp` tmpfs mount was not executable.

Fix:

Changed:

    /tmp:rw,nosuid,size=256m

to:

    /tmp:rw,exec,nosuid,size=256m

This allows Go-generated test binaries to execute while the remainder of the container filesystem stays read-only.

### Design Decision

Generated Go code is never executed directly on the host machine.

All target-language code runs inside the Docker sandbox.

## Current Milestone Status

Milestone 1: IN PROGRESS

### Completed

- Runner result contract.
- Docker-based Go execution.
- CPU limit.
- Memory limit.
- Network isolation.
- Read-only source mount.
- Read-only container filesystem.
- Successful PASS execution verified.

### Next Action

Verify that incorrect but compilable Go code is classified as TEST_FAIL.

---

## Step 1.3 — TEST_FAIL Classification

### Status

Completed.

### Files Modified

    tests/test_runner.py

### Verification Scenario

A valid Go implementation was provided that compiled successfully but returned the wrong result.

Implementation:

    func Add(a int, b int) int {
        return a - b
    }

Expected behavior:

    Add(2, 3) == 5

Actual behavior:

    Add(2, 3) == -1

### Expected Runner Status

    TEST_FAIL

### Result

The integration test:

    test_run_go_tests_classifies_failed_assertion_as_test_fail

passed successfully.

This confirms the runner can distinguish a behavioral test failure from a successful execution.

## Current Milestone Status

Milestone 1: IN PROGRESS

### Completed

- Runner result contract.
- Sandboxed Docker execution.
- PASS path verified.
- TEST_FAIL path verified.

### Next Action

Verify that invalid Go source is classified as COMPILE_ERROR.

---

## Step 1.4 — COMPILE_ERROR Classification

### Status

Completed.

### Files Modified

    tests/test_runner.py

### Verification Scenario

An intentionally invalid Go implementation was provided.

The function was missing its closing brace:

    func Add(a int, b int) int {
        return a + b

This causes Go parsing/compilation to fail before any test can execute.

### Expected Runner Status

    COMPILE_ERROR

### Result

The integration test:

    test_run_go_tests_classifies_invalid_go_as_compile_error

passed successfully.

This confirms that compiler failures are distinguished from behavioral test failures.

## Current Milestone Status

Milestone 1: IN PROGRESS

### Completed

- Runner result contract.
- Sandboxed Docker execution.
- PASS path verified.
- TEST_FAIL path verified.
- COMPILE_ERROR path verified.

### Next Action

Verify that non-terminating Go code is stopped and classified as TIMEOUT.

---

## Step 1.5 — TIMEOUT Classification

### Status

Completed.

### Files Modified

    tests/test_runner.py

### Verification Scenario

Valid Go code containing a non-terminating loop was executed:

    func Hang() {
        for {
        }
    }

The test calls Hang(), causing the generated program to run indefinitely.

### Timeout Configuration

For this integration test:

    timeout=15.0

The shorter test-specific timeout was chosen because normal fresh-container Go compilation currently takes several seconds.

The production runner default remains:

    30 seconds

### Expected Runner Status

    TIMEOUT

### Result

The integration test:

    test_run_go_tests_classifies_infinite_loop_as_timeout

passed successfully.

Observed runtime:

    15.06 seconds

This confirms that:

- the Python timeout is enforced;
- the runaway Docker container is forcefully removed;
- a non-terminating generated solution is classified as TIMEOUT.

## Oracle Status Paths Verified

    PASS          verified
    TEST_FAIL     verified
    COMPILE_ERROR verified
    TIMEOUT       verified

## Current Milestone Status

Milestone 1: IN PROGRESS

### Next Action

Verify temporary execution directories are cleaned up after a run.

---

## Step 1.6 — Temporary Directory Cleanup

### Status

Completed.

### Files Modified

    tests/test_runner.py

### Verification

The runner's temporary execution directory was observed during a real Docker execution.

After:

    run_go_tests(...)

returned, the temporary directory no longer existed.

Integration test:

    test_run_go_tests_cleans_up_temporary_directory

Result:

    PASSED

Observed runtime:

    7.65 seconds

### Why This Matters

Each benchmark execution creates temporary files:

    solution.go
    solution_test.go
    go.mod

The cleanup test confirms repeated evaluation runs will not leave these generated projects on the host filesystem.

## Current Milestone Status

Milestone 1: IN PROGRESS

### Completed Oracle Behaviors

    PASS          verified
    TEST_FAIL     verified
    COMPILE_ERROR verified
    TIMEOUT       verified
    temp cleanup  verified

### Next Action

Add direct unit tests for Go failure-output classification before running the HumanEval-X canonical solutions.

---

## Step 1.7 — Direct Failure Classification Tests

### Status

Completed.

### Files Added

    tests/fixtures/runner/syntax_error.txt
    tests/fixtures/runner/undefined_error.txt
    tests/fixtures/runner/test_failure.txt

### Files Modified

    tests/test_runner.py

### Purpose

Added fast unit tests for the Go failure-output classifier without launching Docker.

This complements the slower end-to-end Docker integration tests.

### Cases Verified

Syntax error:

    COMPILE_ERROR

Undefined identifier:

    COMPILE_ERROR

Failed Go test assertion:

    TEST_FAIL

### Verification

Command executed three direct classification tests.

Result:

    3 passed in 0.01s

### Runner Test Count

Milestone 1 now contains:

    10 runner tests

This matches the project plan target of approximately 10 tests for the runner.

## Current Milestone Status

Milestone 1: IN PROGRESS

### Runner Validation Completed

- PASS integration path
- TEST_FAIL integration path
- COMPILE_ERROR integration path
- TIMEOUT integration path
- Timeout container termination
- Temporary-directory cleanup
- Syntax-error classification
- Undefined-identifier classification
- Test-failure classification
- Shared RunResult/status contract

### Next Action

Run the complete harness test suite before validating canonical HumanEval-X Go solutions.

---

## Step 1.8 — Full Harness Regression Check

### Status

Completed.

### Verification

Command:

    make test

Result:

    11 passed

The complete test suite now includes:

- Milestone 0 package smoke test
- Runner result-contract tests
- PASS integration test
- TEST_FAIL integration test
- COMPILE_ERROR integration test
- TIMEOUT integration test
- Temporary-directory cleanup test
- Direct failure-classification tests

### Result

The runner-validation phase is complete.

No previously implemented functionality was broken.

## Current Milestone Status

Milestone 1: IN PROGRESS

### Next Action

Inspect a real HumanEval-X Go benchmark entry and determine the exact source/test assembly required by the oracle validator.

---

## Step 1.9 — HumanEval-X Go Record Inspection

### Status

Completed.

### Problem Inspected

    Go/0

### HumanEval-X Go Fields Observed

    task_id
    import
    declaration
    canonical_solution
    test_setup
    test

### Source Assembly

Canonical Go source should be constructed as:

    package main
    + import
    + declaration
    + canonical_solution

For Go/0:

- `import` contains the required `math` package.
- `declaration` contains the function signature and opening brace.
- `canonical_solution` contains the function body and closing brace.

### Test Assembly

The Go test file should be constructed as:

    test_setup
    + test

The `test_setup` field already contains:

    package main

and its required test imports.

### Important Dependency Observation

HumanEval-X Go/0 uses:

    github.com/stretchr/testify/assert

The runner currently executes with:

    --network=none

Therefore external Go test dependencies may need to be prepared inside the Docker image rather than downloaded during benchmark execution.

No runner changes were made yet.

### Next Action

Execute the canonical Go/0 solution through the current runner and inspect the real result before changing dependency handling.

---

## Step 1.10 — First Canonical HumanEval-X Oracle Execution

### Status

Completed.

### Problem Validated

    Go/0

Function:

    HasCloseElements

### Canonical Source Assembly

The HumanEval-X Go source was assembled as:

    package main
    + import
    + declaration
    + canonical_solution

The test file was assembled as:

    test_setup
    + test

### Initial Result

The first canonical execution failed before the benchmark test could run.

Error:

    no required module provides package github.com/stretchr/testify/assert

### Cause

HumanEval-X Go tests depend on:

    github.com/stretchr/testify/assert

The runtime Docker sandbox intentionally uses:

    --network=none

Therefore benchmark dependencies cannot be downloaded during test execution.

### Docker Dependency Design

The Docker image was updated so HumanEval-X test dependencies are resolved during image build time, when network access is available.

A small dummy Go module imports:

    github.com/stretchr/testify/assert

During image creation the following are executed:

    go mod tidy
    go test ./...

This causes testify and its transitive dependency graph to be cached in the Docker image.

Runtime benchmark execution remains network isolated.

### Runtime Module Configuration

The temporary benchmark go.mod now explicitly requires:

    github.com/stretchr/testify v1.9.0

Runtime Go execution uses:

    go test -mod=mod ./... -count=1

This allows Go to create the temporary go.sum using dependencies already cached inside the image.

Runtime networking remains disabled using:

    --network=none
    GOPROXY=off
    GOSUMDB=off

### Sandbox Workspace Design

Host-created benchmark files are mounted read-only at:

    /src

They are copied inside the container to:

    /tmp/work

The Go compiler and test binary operate only inside this temporary writable filesystem.

The container root filesystem remains read-only.

### Problems Encountered and Fixed

#### Duplicate Docker Image Argument

An intermediate runner command accidentally supplied the Docker image twice.

Result:

    executable file not found in $PATH

Fixed by ensuring the image appears exactly once in the docker command.

#### /work Permission Failure

A separate tmpfs mounted at /work was not writable by the non-root runner user.

Error:

    Permission denied

Fixed by using:

    /tmp/work

inside the already-writable temporary filesystem instead.

#### Go Missing from PATH

The runner initially invoked:

    sh -lc

The login shell reset PATH and caused:

    sh: 1: go: not found

Fixed by using:

    sh -c

which preserves the Docker image PATH.

#### Missing go.sum Dependency Graph

The first dependency-prepared image still lacked parts of the testify transitive module graph.

Error included:

    gopkg.in/check.v1
    module lookup disabled by GOPROXY=off

Fixed by running a real dummy testify test during Docker image creation rather than only downloading the top-level module.

### Canonical Oracle Result

Final execution:

    Go/0

Result:

    PASS

Observed test output:

    ok migrateeval 0.001s

The full container invocation took approximately:

    15.98 seconds

### Regression Verification

After all runner and Docker changes:

    make test

Result:

    11 passed in 45.38s

### Conclusion

The oracle has now successfully executed a real canonical HumanEval-X Go solution while maintaining:

- CPU restriction
- memory restriction
- no runtime network access
- non-root execution
- read-only container filesystem
- read-only host source mount
- timeout enforcement
- temporary workspace cleanup

## Current Milestone Status

Milestone 1: IN PROGRESS

### Completed

- Runner result contract
- PASS classification
- TEST_FAIL classification
- COMPILE_ERROR classification
- TIMEOUT classification
- Temporary directory cleanup
- Direct classifier tests
- 10 runner tests
- Full harness regression: 11 passing tests
- HumanEval-X Go structure inspected
- Canonical HumanEval-X Go/0 successfully validated

### Next Action

Run a small sample of canonical HumanEval-X Go problems to confirm the source/test assembly generalizes beyond Go/0.

---

## Step 1.11 — Small Canonical HumanEval-X Sample

### Status

Completed.

### Goal

Validate the oracle against several canonical HumanEval-X Go solutions before scaling to the full 164-problem benchmark.

### Sample

Problems tested:

    Go/0
    Go/1
    Go/2
    Go/3
    Go/4

### Initial Result

The first five-problem run produced:

    Go/0 PASS
    Go/1 PASS
    Go/2 COMPILE_ERROR
    Go/3 PASS
    Go/4 COMPILE_ERROR

Result:

    3/5 PASS

### Cause of Go/2 and Go/4 Failures

The HumanEval-X tests for these problems directly call:

    math.Abs(...)

The problem-level `import` field contains:

    "math"

but Go imports are file-scoped.

Because the solution and tests are written to separate files:

    solution.go
    solution_test.go

the `math` import in solution.go is not visible to solution_test.go.

### Second Assembly Attempt

The problem imports were copied into every test file.

This fixed Go/2 and Go/4, but caused Go/0 to fail because its test did not use math.

Error:

    "math" imported and not used

Result:

    4/5 PASS

### Final Sample Assembly Rule

For the sample, a problem-level import is added to the test file only when:

- the test actually references that package;
- the package exists in the problem import field;
- the package is not already imported by test_setup.

For the observed sample this meant adding:

    import "math"

only when the test contained:

    math.

### Final Result

    Go/0 PASS
    Go/1 PASS
    Go/2 PASS
    Go/3 PASS
    Go/4 PASS

Result:

    5/5 PASS

### Observed Execution Time

Each fresh Docker execution currently takes approximately:

    16 seconds

The actual Go tests themselves execute in milliseconds; most of the elapsed time is Docker/Go compilation setup.

### Design Conclusion

HumanEval-X Go source and test assembly requires file-aware import handling.

A reusable and general implementation will be created in the next step rather than keeping this temporary sample-specific logic.

## Current Milestone Status

Milestone 1: IN PROGRESS

### Canonical Validation Progress

    Go/0-Go/4: 5/5 PASS

### Next Action

Create a reusable canonical HumanEval-X validator and generalize test-import assembly before running the full benchmark.

---

## Step 1.12 — Reusable Canonical HumanEval-X Validator

### Status

Completed.

### Files Added

    src/migrate_eval/dataset.py
    scripts/validate_oracle.py
    tests/test_dataset.py

### Purpose

Replace the temporary manual HumanEval-X assembly commands with reusable project code before running the complete benchmark.

### Dataset Loader

Implemented:

    load_go_problems(path)

The loader reads:

    data/humaneval_x/humaneval_go.jsonl.gz

and returns the HumanEval-X Go problem records.

### Canonical Go Assembly

Implemented:

    build_canonical_go_files(problem)

This constructs:

    solution.go
    solution_test.go

from the HumanEval-X fields:

    import
    declaration
    canonical_solution
    test_setup
    test

### Go Import Handling

HumanEval-X exposed an important Go-specific issue:

Go imports are file-scoped.

Some benchmark tests directly reference packages from the problem-level import field, even though those packages are not included in test_setup.

The assembler therefore:

1. Parses problem imports.
2. Parses imports already present in test_setup.
3. Detects whether the test references a problem import using:

       package.Symbol

4. Adds only required missing imports to solution_test.go.
5. Avoids adding unused imports.
6. Avoids duplicating imports already present in test_setup.

### Unit Tests Added

Added four dataset/assembly tests covering:

- canonical solution receives problem imports;
- tests receive a problem import when actually used;
- unused problem imports are not copied into tests;
- imports already present in test_setup are not duplicated.

Verification:

    python -m pytest tests/test_dataset.py -v

Result:

    4 passed

### Canonical Validator

Created:

    scripts/validate_oracle.py

Supported arguments:

    --dataset
    --n
    --timeout

The script:

1. Loads HumanEval-X Go problems.
2. Builds canonical source/test files.
3. Executes each through the Docker oracle.
4. Prints task status and duration.
5. Prints failures with stdout/stderr.
6. Produces a final PASS summary.
7. Returns a non-zero exit code if any selected problem fails.

### Five-Problem Validation

Command:

    python scripts/validate_oracle.py --n 5

Result:

    Go/0 PASS
    Go/1 PASS
    Go/2 PASS
    Go/3 PASS
    Go/4 PASS

Final result:

    5/5 PASS

### Full Harness Regression

Command:

    make test

Result:

    15 passed in 47.12s

Current harness tests:

    4 dataset tests
    10 runner tests
    1 smoke test

### Conclusion

Canonical HumanEval-X assembly is now implemented as reusable project code rather than manual shell experiments.

The oracle is ready to be scaled to the complete HumanEval-X Go benchmark.

## Current Milestone Status

Milestone 1: IN PROGRESS

### Canonical Validation Progress

    Sample: 5/5 PASS
    Full benchmark: not yet run

### Next Action

Run the canonical validator across all 164 HumanEval-X Go problems and collect the complete oracle validity result.

---

## Step 1.13 — Full Canonical HumanEval-X Oracle Run

### Status

Completed.

### Goal

Run every canonical HumanEval-X Go solution through the Docker oracle and measure oracle validity before applying any exclusions.

### Command

    python -u scripts/validate_oracle.py --n 164

The complete console output was also captured under:

    results/oracle/canonical_164.txt

### Result

Total benchmark problems:

    164

Canonical solutions passing:

    152

Canonical solutions failing:

    12

Pass rate:

    152 / 164
    92.68%

### Failed Tasks

    Go/10
    Go/17
    Go/20
    Go/27
    Go/32
    Go/38
    Go/50
    Go/59
    Go/75
    Go/90
    Go/108
    Go/162

### Failure Type

All 12 failures were classified as:

    COMPILE_ERROR

No canonical problem produced:

    TEST_FAIL
    TIMEOUT

### Observed Failure Patterns

Missing helper functions:

    Go/10  IsPalindrome
    Go/32  Poly
    Go/38  EncodeCyclic
    Go/50  EncodeShift

Missing solution imports included:

    strings
    math
    sort

Unused imports were also observed in some generated source/test files.

### Interpretation

The result is below the Milestone 1 target of:

    >= 160 / 164 PASS

However, the failures are strongly suggestive of HumanEval-X source assembly issues rather than incorrect canonical implementations.

No benchmark exclusions will be made yet.

The failed records must first be inspected to determine whether required helper functions and imports are present in other HumanEval-X fields such as `prompt`.

### Next Action

Inspect all 12 failing HumanEval-X records and determine a general source/test assembly rule before rerunning the benchmark.

---

## Step 1.14A — Canonical Assembly Fixes for Full Benchmark

### Status

Completed.

### Background

The first full canonical HumanEval-X run produced:

    152 / 164 PASS

with 12 canonical Go problems failing at compile time.

Failed tasks:

    Go/10
    Go/17
    Go/20
    Go/27
    Go/32
    Go/38
    Go/50
    Go/59
    Go/75
    Go/90
    Go/108
    Go/162

### Failure Diagnosis

Inspection of the failing HumanEval-X records identified three main assembly issues.

#### Helper functions stored in prompt

Some canonical implementations depend on helper functions defined in the HumanEval-X prompt rather than in declaration or canonical_solution.

Examples:

    Go/10  IsPalindrome
    Go/32  Poly
    Go/38  EncodeCyclic
    Go/50  EncodeShift

The previous source assembly:

    package main
    + import
    + declaration
    + canonical_solution

discarded those helper functions.

### Canonical Source Assembly Change

Canonical source assembly now preserves:

    prompt
    + canonical_solution

The prompt is stripped of package/import declarations and retained as the source scaffold.

This preserves helper functions required by the target function.

### Missing Standard-Library Imports

Some HumanEval-X records use standard-library packages in canonical_solution despite the dataset import field being empty or incomplete.

Examples included:

    strings
    math
    sort

The canonical assembler now detects selector usage such as:

    strings.Split
    math.Pow
    sort.Float64s

and infers the corresponding standard-library import when missing.

This logic is used only for canonical benchmark assembly.

It is not used to repair model-generated code.

### Unused Imports

Some dataset records contain imports that are not actually used in the assembled source or test file.

Go treats unused imports as compile errors.

Examples included:

    strings
    math
    crypto/md5

The assembler now normalizes imports independently for each file and keeps only imports actually referenced by that file.

### File-Scoped Import Handling

solution.go and solution_test.go now receive independent normalized import sets.

This preserves Go's file-scoped import semantics while avoiding:

- missing imports;
- duplicate imports;
- unused imports.

### Additional Dataset Tests

The dataset test suite now covers:

- used source imports;
- test imports required by test code;
- unused test imports;
- duplicate test imports;
- helper functions preserved from prompt;
- missing standard-library import inference;
- unused source import removal;
- unused test import removal.

### Targeted Canonical Revalidation

Only the 12 previously failing problems were rerun after the assembly changes.

Result:

    Go/10   PASS
    Go/17   PASS
    Go/20   PASS
    Go/27   PASS
    Go/32   PASS
    Go/38   PASS
    Go/50   PASS
    Go/59   PASS
    Go/75   PASS
    Go/90   PASS
    Go/108  PASS
    Go/162  PASS

Final result:

    12 / 12 PASS

### Conclusion

All failures from the original 152/164 canonical run are now explained by source/test assembly issues and have been corrected.

No benchmark exclusions are currently required.

### Next Action

Run the complete 164-problem canonical HumanEval-X validation again using the corrected assembler.

---

## Step 1.14B — Final Canonical Validation and Benchmark Exclusion

### Status

Completed.

### Final Full Validation

After correcting HumanEval-X canonical source/test assembly, all 164 Go problems were rerun through the Docker oracle.

The final validation used four concurrent workers for the evaluation run only.

The project runner itself was not modified for parallel execution.

### Raw Result

Canonical problems:

    164

PASS:

    163

TEST_FAIL:

    1

COMPILE_ERROR:

    0

TIMEOUT:

    0

Raw canonical pass rate:

    163 / 164
    99.39%

This exceeds the Milestone 1 requirement of:

    >= 160 / 164 PASS

### Remaining Failure

Task:

    Go/95

Function:

    CheckDictCase

Status:

    TEST_FAIL

The failing benchmark assertion expected false for a dictionary containing mixed-case keys, while the canonical implementation returned true.

### Go/95 Root Cause

The canonical HumanEval-X implementation is dependent on Go map iteration order.

Its loop contains logic equivalent to:

    if first key determines case:
        state = upper or lower
    else if next key has conflicting case:
        state = mixed
        break
    else:
        break

The final unconditional break means that when the second visited key has the same case as the first, the function exits without examining the remaining dictionary keys.

Because Go map iteration order is unspecified, the mixed dictionary:

    {"p", "A", "B"}

may be inspected in an order such as:

    "A"
    "B"

The implementation then returns true before inspecting:

    "p"

In a different iteration order it may correctly detect mixed case and return false.

Therefore Go/95 is a flaky canonical benchmark item rather than an oracle failure.

### Benchmark Exclusion

Excluded:

    Go/95

Reason:

    canonical HumanEval-X implementation is nondeterministic due to dependence on Go map iteration order.

No other benchmark problems are excluded.

### Validated Evaluation Set

Usable benchmark problems:

    163

Canonical oracle result after exclusion:

    163 / 163 PASS

Oracle validity:

    100%

### Milestone 1 Final Result

The Docker-based Go oracle has been validated successfully.

Verified behaviors:

    PASS
    TEST_FAIL
    COMPILE_ERROR
    TIMEOUT

Verified safety properties:

- generated Go code never executes directly on the host;
- non-root Docker execution;
- CPU limited to 1 core;
- memory limited to 512 MB;
- runtime network disabled;
- container root filesystem read-only;
- host source mount read-only;
- temporary execution workspace;
- timeout enforcement;
- runaway container termination;
- temporary host directory cleanup.

Canonical HumanEval-X validation:

    163 / 164 raw PASS
    Go/95 excluded as a flaky canonical benchmark item
    163 / 163 validated benchmark PASS

## Milestone 1 — Oracle Works

### Status

COMPLETED.

### Exit Criteria

- [x] Docker Go runner implemented
- [x] CPU restriction implemented
- [x] Memory restriction implemented
- [x] Runtime network disabled
- [x] Timeout enforcement implemented
- [x] PASS verified
- [x] TEST_FAIL verified
- [x] COMPILE_ERROR verified
- [x] TIMEOUT verified
- [x] Temporary directory cleanup verified
- [x] Runner status parsing tested
- [x] HumanEval-X canonical Go solutions evaluated
- [x] >=160/164 canonical solutions PASS
- [x] Benchmark failure inspected and documented
- [x] Benchmark exclusion list established

### Final Exclusion List

    Go/95

### Next Milestone

Milestone 2 — Single-Shot Migration

The next milestone introduces model adapters, migration prompts, Go-code extraction, and the first Java-to-Go LLM migrations.

Milestone 2 must begin in a new chat.


## Step 2.1 — Model Adapter Contract

### Status

Completed.

### Files Added

```
src/migrate_eval/models/base.py
tests/test_model_base.py
```

### Implemented

Created the shared model interface:

```
ModelAdapter
```

The protocol defines:

```
name: str
complete(prompt: str) -> str
```

All model backends used by migrate-eval will implement this same interface.

This allows later pipeline components to call OpenAI, Ollama, or future model providers without depending on provider-specific APIs.

### Design Decision

`ModelAdapter` is implemented as a runtime-checkable Python `Protocol`.

This provides structural typing: a model class does not need to inherit from a specific base class as long as it exposes the required attributes and methods.

This keeps model adapters lightweight and interchangeable.

### Tests Added

Verified that:

* a structurally compatible model satisfies `ModelAdapter`;
* a model missing the `complete()` method does not satisfy the protocol;
* the adapter contract can execute a mocked completion without any network access.

### Step-Specific Verification

Command:

```
python -m pytest tests/test_model_base.py -v
```

Result:

```
2 passed
```

### Next Action

Implement the first real model backend:

```
OpenAI adapter
```

The adapter will use the shared ModelAdapter contract introduced in this step.


## Step 2.2 — OpenAI Model Adapter

### Status

Completed.

### Files Added

```
src/migrate_eval/models/openai_adapter.py
tests/test_openai_adapter.py
```

### Implemented

Created:

```
OpenAIAdapter
```

The adapter implements the shared ModelAdapter contract introduced in Step 2.1.

The adapter exposes:

```
name
complete(prompt: str) -> str
```

and uses the OpenAI Responses API internally.

### Adapter Behavior

The adapter:

* accepts the model name as configuration;
* uses temperature 0.0 by default for deterministic evaluation;
* supports dependency injection of the OpenAI client;
* configures timeout and SDK retry behavior;
* records completion latency;
* reads input and output token usage when available;
* returns the raw generated text through `response.output_text`.

### Naming Convention

Model names are exposed to the evaluation pipeline as:

```
openai:<model>
```

This will later allow result files and evaluation summaries to distinguish providers and models consistently.

### Testing Strategy

The OpenAI API is never called from pytest.

A fake OpenAI client was injected into the adapter so tests remain:

* deterministic;
* fast;
* offline;
* free of API cost.

### Tests Added

Verified that:

* OpenAIAdapter satisfies the ModelAdapter protocol;
* the adapter returns the generated response text;
* the expected model, prompt, and temperature are sent to the client.

### Step-Specific Verification

Command:

```
python -m pytest tests/test_openai_adapter.py -v
```

Result:

```
3 passed
```

### Next Action

Implement the local Ollama model adapter using the same ModelAdapter interface.


## Step 2.3 — Ollama Model Adapter

### Status

Completed.

### Files Added

```
src/migrate_eval/models/ollama_adapter.py
tests/test_ollama_adapter.py
```

### Implemented

Created:

```
OllamaAdapter
```

The adapter implements the shared ModelAdapter contract introduced in Step 2.1.

The adapter exposes:

```
name
complete(prompt: str) -> str
```

and communicates with the local Ollama HTTP API.

### Adapter Behavior

The adapter:

* accepts the Ollama model name as configuration;
* uses the local Ollama API endpoint;
* disables streaming so each completion returns one complete response;
* uses temperature 0.0 by default;
* uses a fixed seed for improved reproducibility;
* supports dependency injection of the HTTP client;
* records completion latency;
* reads Ollama input/output token counts when available;
* retries temporary failures with exponential backoff;
* retries HTTP 429 and server-side 5xx responses;
* retries timeout and network errors;
* returns the raw generated response text.

### Naming Convention

Models are exposed to the evaluation pipeline as:

```
ollama:<model>
```

For the local benchmark model this will later be:

```
ollama:qwen2.5-coder:14b
```

### Testing Strategy

Pytest does not call the real Ollama service.

A fake HTTP client is injected into the adapter so tests remain:

* deterministic;
* fast;
* offline;
* independent of whether Ollama is currently running.

### Tests Added

Verified that:

* OllamaAdapter satisfies the ModelAdapter protocol;
* the adapter returns generated response text;
* the expected request payload is sent;
* deterministic generation settings are included;
* temporary server failures are retried correctly.

### Step-Specific Verification

Command:

```
python -m pytest tests/test_ollama_adapter.py -v
```

Result:

```
4 passed
```

### Next Action

Implement the initial Java-to-Go migration prompt.

## Step 2.4 — Initial Java-to-Go Migration Prompt

### Status

Completed.

### Files Added

```
src/migrate_eval/prompts.py
tests/test_prompts.py
```

### Implemented

Created:

```
initial(java_code, go_signature)
```

The function builds the initial Java-to-Go migration prompt used for single-shot model evaluation.

### Prompt Inputs

The prompt contains:

* the Java implementation;
* the exact Go function signature that must be implemented.

### Prompt Requirements

The model is instructed to:

* preserve the behavior of the Java implementation;
* implement exactly the supplied Go signature;
* return only one Go code block;
* not include tests;
* not include a main function;
* not include explanations;
* use package main.

### Evaluation Integrity

The prompt does not expose:

* the canonical Go solution;
* the HumanEval-X Go tests.

This prevents benchmark answer leakage and ensures the model must perform the migration from the Java implementation.

### Design Decision

The prompt template is stored as a plain Python string constant:

```
INITIAL_PROMPT_TEMPLATE
```

This keeps the benchmark prompt visible, inspectable, and easy to document later in the README.

### Tests Added

Verified that the generated prompt contains:

* the Java implementation;
* the required Go signature;
* the code-only output instruction;
* the no-tests instruction;
* the no-main instruction;
* the package main requirement.

### Problem Encountered

The first version of prompts.py was accidentally pasted incompletely.

Python reported:

```
SyntaxError: unterminated triple-quoted string literal
```

The prompt template was replaced with the complete version and the tests then passed successfully.

### Step-Specific Verification

Command:

```
python -m pytest tests/test_prompts.py -v
```

Result:

```
4 passed
```

### Next Action

Implement Go code extraction from raw model responses.


## Step 2.5 — Go Code Extraction

### Status

Completed.

### Files Added

    src/migrate_eval/extract.py
    tests/test_extract.py

### Implemented

Created:

    go_block(response, package_name="main")

and:

    ExtractionError

The extractor converts raw model responses into Go source code that can later be passed to the Docker oracle.

### Extraction Rules

If one or more Go fenced blocks are present:

    ```go
    ...
    ```

the extractor uses the final Go block.

This handles model responses where an initial answer is followed by a corrected implementation.

If no Go fenced block exists, the complete model response is treated as Go source.

### Package Normalization

Any package declaration returned by the model is removed.

The extractor then adds the package required by the evaluation harness:

    package main

This prevents model-generated package names from causing package mismatches with HumanEval-X target tests.

The function also supports an alternate package name through:

    package_name

for future reuse.

### Extraction Failure

If the response is empty, or contains only a package declaration, the extractor raises:

    ExtractionError

The migration pipeline will later convert this failure into the shared status:

    EXTRACT_ERROR

That integration is intentionally deferred until the single-shot migration loop is implemented.

### Tests Added

Verified:

- extraction from a single Go fenced block;
- selection of the final block when multiple Go blocks exist;
- extraction from an unfenced response;
- replacement of an incorrect package declaration;
- prevention of duplicate package main declarations;
- custom package-name support;
- empty-response failure;
- package-only-response failure.

### Step-Specific Verification

Command:

    python -m pytest tests/test_extract.py -v

Result:

    8 passed

### Next Action

Implement the single-shot migration pipeline with:

    iters=0

The pipeline will connect:

    dataset
    -> prompt
    -> model adapter
    -> extractor
    -> Docker oracle

## Step 2.6 — Single-Shot Migration Pipeline

### Status

Completed.

### Files Added

    src/migrate_eval/loop.py
    tests/test_loop.py

### Files Modified

    src/migrate_eval/dataset.py
    tests/test_dataset.py

### Goal

Connect the components built earlier in Milestone 2 into the first complete Java-to-Go migration path.

This step implements single-shot migration only:

    iters = 0

No repair attempts are performed yet.

### Migration Dataset Representation

Created:

    MigrationProblem

with fields:

    task_id
    java_code
    go_signature
    go_test

The Java and Go HumanEval-X datasets are paired using their shared numeric task index.

Examples:

    Java/0 -> Go/0
    Java/1 -> Go/1

### Java Dataset Loading

Added:

    load_java_problems(...)

The Java HumanEval-X gzip JSONL file is loaded using the same approach already used by the Go dataset loader.

### Migration Problem Assembly

Added:

    build_migration_problems(...)

The function:

1. pairs Java and Go records by numeric task index;
2. combines the Java prompt and canonical solution into the source implementation;
3. uses the Go declaration as the required target signature;
4. assembles the Go test file;
5. supports benchmark exclusions.

The known flaky benchmark problem:

    Go/95

can therefore remain excluded from migration evaluation.

### Dataset Validation

Added tests covering:

- Java/Go pairing by task index;
- preservation of Java source;
- preservation of Go signature and tests;
- exclusion of requested benchmark tasks;
- rejection of mismatched Java and Go task sets.

Dataset-specific verification:

    12 passed

### Single-Shot Migration Orchestration

Created:

    migrate_once(...)

The migration path is:

    MigrationProblem
        ->
    initial migration prompt
        ->
    ModelAdapter.complete(...)
        ->
    Go extraction
        ->
    Docker Go oracle
        ->
    MigrationAttempt

### MigrationAttempt

Created:

    MigrationAttempt

It records:

    task_id
    model_name
    prompt
    raw_response
    go_code
    run_result

This provides the information that later result logging will persist to JSONL.

### Failure Handling

Model exceptions are converted into:

    MODEL_ERROR

Extraction failures are converted into:

    EXTRACT_ERROR

In both cases, the Docker runner is not executed.

Failures returned by the Go oracle are preserved unchanged, including:

    COMPILE_ERROR
    TEST_FAIL
    TIMEOUT

### Mocked Pipeline Tests

Verified:

- successful single-shot migration;
- prompt reaches the model exactly once;
- extracted Go reaches the runner;
- model failure becomes MODEL_ERROR;
- extraction failure becomes EXTRACT_ERROR;
- runner failure status is preserved.

### Real Docker Integration Test

A fake model returned a valid Go implementation while the real Docker oracle was used.

Full path exercised:

    FakeModel
        ->
    prompt
        ->
    extraction
        ->
    run_go_tests
        ->
    Docker
        ->
    go test
        ->
    PASS

Command:

    python -m pytest tests/test_loop.py -v

Result:

    5 passed

Observed integration runtime:

    8.89 seconds

### Design Decision

The model and runner are injectable.

This allows unit tests to stay fast and offline while still permitting dedicated integration tests against the real Docker oracle.

No real OpenAI or Ollama request is required for pytest.

### Milestone 2 Progress

Completed:

- Step 2.1 — ModelAdapter contract
- Step 2.2 — OpenAI adapter
- Step 2.3 — Ollama adapter
- Step 2.4 — Initial migration prompt
- Step 2.5 — Go code extractor
- Step 2.6 — Single-shot migration pipeline

### Next Action

Implement JSONL result logging and the command-line interface for running single-shot migration experiments.

## Step 2.7 — JSONL Results and Command-Line Interface

### Status

Completed.

### Files Added

    src/migrate_eval/results.py
    src/migrate_eval/cli.py
    tests/test_results.py
    tests/test_cli.py

### Files Modified

    src/migrate_eval/models/openai_adapter.py
    pyproject.toml

### Goal

Add persistent result logging and a user-facing command-line interface for running single-shot migration evaluations.

---

### JSONL Result Logging

Created:

    attempt_to_record(...)
    append_attempt(...)

A MigrationAttempt can now be converted into a JSON-serializable record containing:

    task_id
    model
    iteration
    prompt
    raw_response
    go_code
    status
    stdout
    stderr
    duration

Each migration attempt is written as one JSON object per line.

Example structure:

    results/
        <model>/
            <run_id>.jsonl

### Append-Only Design

Result files are opened in append mode.

This ensures later benchmark problems are added without overwriting earlier attempts.

This design also supports the repair loop planned for Milestone 3, where multiple iterations of the same benchmark problem will be recorded.

### Results Tests

Verified:

- MigrationAttempt converts to JSON-serializable data.
- RunStatus is stored using its string value.
- failure statuses are preserved.
- missing parent directories are created automatically.
- one attempt produces one JSONL line.
- multiple attempts append rather than overwrite.

Step-specific result:

    5 passed

---

### CLI

Created:

    migrate-eval

with the command:

    migrate-eval run

The Milestone 2 CLI supports:

    --model
    --n
    --iters
    --java-dataset
    --go-dataset
    --results-dir

Example intended usage:

    migrate-eval run \
        --model ollama:qwen2.5-coder:14b \
        --n 20 \
        --iters 0

### Model Specifications

Supported forms:

    ollama:<model>
    openai:<model>

Examples:

    ollama:qwen2.5-coder:14b
    openai:<model-name>

The CLI creates the corresponding ModelAdapter automatically.

### Milestone 2 Iteration Restriction

Milestone 2 supports only:

    --iters 0

Requests for repair iterations are rejected.

Repair iterations belong to Milestone 3.

### Benchmark Handling

The CLI:

1. loads HumanEval-X Java records;
2. loads HumanEval-X Go records;
3. pairs Java and Go tasks;
4. excludes the known flaky canonical benchmark:

       Go/95

5. selects the requested number of tasks;
6. performs one migration attempt per task;
7. writes each result immediately to JSONL;
8. prints each task status;
9. calculates and prints pass@1.

### Run Identification

Each execution receives a unique run identifier consisting of:

    UTC timestamp
    +
    short UUID suffix

Results are written beneath a filesystem-safe model directory.

### CLI Tests

All CLI behavior is tested without:

- real OpenAI requests;
- real Ollama requests;
- Docker execution.

The tests verify:

- Ollama adapter selection;
- OpenAI adapter selection;
- invalid provider rejection;
- rejection of repair iterations in Milestone 2;
- selected-problem execution;
- JSONL output;
- PASS and TEST_FAIL output;
- pass@1 calculation.

Step-specific result:

    5 passed

### OpenAI Adapter Improvement

During CLI testing, constructing an OpenAIAdapter immediately attempted to create an authenticated OpenAI client.

This caused tests to require:

    OPENAI_API_KEY

even though no API request was being performed.

The adapter was changed to initialize the OpenAI client lazily.

The client is now created only when:

    complete(...)

is actually called.

This keeps adapter construction:

- offline;
- testable;
- independent of credentials.

### Typer Command Structure Fix

Typer initially interpreted the application as a single-command CLI.

This caused:

    migrate-eval run ...

to treat `run` as an unexpected argument.

A root callback was added so the CLI operates as a command group:

    migrate-eval
        └── run

### Package Entry Point

Added to pyproject.toml:

    [project.scripts]
    migrate-eval = "migrate_eval.cli:app"

The editable package was reinstalled.

Verification:

    migrate-eval --help

successfully displayed the `run` command.

---

### Milestone 2 Progress

Completed:

- Step 2.1 — ModelAdapter contract
- Step 2.2 — OpenAI adapter
- Step 2.3 — Ollama adapter
- Step 2.4 — Initial migration prompt
- Step 2.5 — Go code extractor
- Step 2.6 — Single-shot migration pipeline
- Step 2.7 — JSONL results and CLI

### Next Action

Run the first real single-shot evaluation:

    20 HumanEval-X problems
    ×
    Ollama model
    ×
    OpenAI model

Then calculate and compare pass@1.

This is Step 2.8 and the final step of Milestone 2.

## Step 2.8 — Real Single-Shot Model Evaluation

### Status

Completed.

### Goal

Run the first real Java-to-Go single-shot benchmark using both configured model backends.

Each model received exactly one migration attempt per problem:

    iteration = 0

No repair feedback or additional attempts were allowed.

The same first 20 usable HumanEval-X Java-to-Go problems were evaluated for both models.

The known flaky benchmark item:

    Go/95

remains excluded from the validated benchmark set.

---

### Ollama Smoke Test

Model:

    ollama:qwen2.5-coder:14b

One real migration was executed end-to-end.

Task:

    Go/0

Result:

    PASS

The complete production path was exercised:

    HumanEval-X Java source
        ->
    initial migration prompt
        ->
    qwen2.5-coder:14b
        ->
    raw model response
        ->
    Go extraction
        ->
    Docker oracle
        ->
    HumanEval-X Go tests
        ->
    PASS

The JSONL record successfully preserved:

    task_id
    model
    iteration
    prompt
    raw_response
    extracted Go code
    status
    stdout
    stderr
    duration

Smoke-test result file:

    results/ollama__qwen2.5-coder__14b/
    20260913T141031Z-f8f95734.jsonl

---

### Ollama 20-Problem Evaluation

Model:

    ollama:qwen2.5-coder:14b

Problems:

    20

Results:

    PASS           14
    COMPILE_ERROR   4
    TEST_FAIL       2

pass@1:

    14 / 20
    70.0%

Result file:

    results/ollama__qwen2.5-coder__14b/
    20260913T141209Z-4d3bc62f.jsonl

The local model therefore successfully migrated 70% of the first 20 benchmark problems in a single attempt.

---

### OpenAI Integration Issues and Fixes

The OpenAI smoke test exposed two configuration/compatibility issues before a successful model call was achieved.

#### API Key Validation

An initial API request returned:

    MODEL_ERROR
    HTTP 401 invalid_api_key

The environment configuration was inspected without exposing the secret key.

A direct authenticated request to the OpenAI API returned:

    Status: 200
    API key is valid.

This confirmed that the final local API credential configuration was correct.

The `.env` file remains ignored by Git.

#### Unsupported Temperature Parameter

After authentication was fixed, GPT-5.6 Terra returned:

    Unsupported parameter:
    'temperature' is not supported with this model.

The OpenAI adapter previously sent:

    temperature = 0.0

for every model.

The adapter was changed so temperature is now optional:

    temperature: float | None = None

The request includes the temperature parameter only when it is explicitly configured.

This allows models such as GPT-5.6 Terra to operate without receiving unsupported sampling parameters while retaining temperature support for compatible models.

The OpenAI adapter test suite was updated accordingly.

Verification:

    4 passed

---

### OpenAI Smoke Test

Model:

    openai:gpt-5.6-terra

Task:

    Go/0

Result:

    PASS

This confirmed the complete OpenAI production path:

    HumanEval-X Java
        ->
    prompt
        ->
    OpenAI Responses API
        ->
    GPT-5.6 Terra
        ->
    extraction
        ->
    Docker oracle
        ->
    Go tests
        ->
    PASS

Smoke-test result file:

    results/openai__gpt-5.6-terra/
    20260913T144140Z-5e0c0716.jsonl

---

### OpenAI 20-Problem Evaluation

Model:

    openai:gpt-5.6-terra

Problems:

    20

Results:

    PASS           18
    COMPILE_ERROR   2
    TEST_FAIL       0

pass@1:

    18 / 20
    90.0%

Result file:

    results/openai__gpt-5.6-terra/
    20260913T144228Z-be0fdf52.jsonl

---

### Single-Shot Model Comparison

Results on the same 20 benchmark problems:

| Model | PASS | COMPILE_ERROR | TEST_FAIL | pass@1 |
|---|---:|---:|---:|---:|
| qwen2.5-coder:14b | 14 | 4 | 2 | 70.0% |
| gpt-5.6-terra | 18 | 2 | 0 | 90.0% |

GPT-5.6 Terra achieved:

    +4 passing problems

and:

    +20 percentage points pass@1

relative to qwen2.5-coder:14b on this 20-problem single-shot sample.

Residual failures:

    qwen2.5-coder:14b
        4 compile errors
        2 test failures

    gpt-5.6-terra
        2 compile errors
        0 test failures

These measurements establish the iteration-0 baseline that the repair loop in Milestone 3 will attempt to improve.

---

# Milestone 2 — Single-Shot Migration

## Status

COMPLETED.

### Completed

- ModelAdapter protocol
- OpenAI model adapter
- Ollama model adapter
- initial Java-to-Go prompt
- Go response extraction
- EXTRACT_ERROR handling
- MODEL_ERROR handling
- paired Java/Go benchmark representation
- single-shot migration orchestration
- real Docker integration
- JSONL attempt logging
- append-only result persistence
- CLI
- model selection through CLI
- pass@1 reporting
- 20-problem Ollama evaluation
- 20-problem OpenAI evaluation
- comparison of two real models

### Milestone 2 Exit Results

    qwen2.5-coder:14b
    pass@1 = 70.0%

    gpt-5.6-terra
    pass@1 = 90.0%

### Next Milestone

Milestone 3 — Repair Loop

Main objective:

Feed compiler/test failures back to the model and measure whether up to three repair iterations improve the single-shot baseline.

Milestone 3 must begin in a new chat.


## Step 3.1 — Repair Prompt

### Status

Completed.

### Files Modified

    src/migrate_eval/prompts.py
    tests/test_prompts.py

### Goal

Create the repair prompt used by Milestone 3 when a generated Go migration fails compilation or target-language tests.

The repair loop itself is not implemented yet.

### Implemented

Created:

    repair(go_code, run_result)

The function constructs a repair prompt containing:

- the current generated Go implementation;
- the RunResult failure status;
- captured stdout;
- captured stderr;
- instructions to return the complete corrected Go implementation.

### Repair Prompt Requirements

The model is instructed to:

- fix the existing Go implementation;
- preserve the intended behavior;
- preserve required function signatures;
- return the complete corrected Go source;
- return exactly one Go code block;
- use package main;
- not include tests;
- not include a main function;
- not include explanations outside the code block.

### Failure Feedback

Created internal feedback formatting for:

    stdout
    stderr

The repair prompt therefore exposes the compiler or test feedback produced by the Docker oracle.

If neither stdout nor stderr is available, the prompt includes:

    (no compiler or test output was captured)

### Output Truncation

Repair feedback is limited to:

    60 actual compiler/test output lines

The STDOUT and STDERR labels do not consume the 60-line budget.

If more output exists, the feedback ends with:

    ...[output truncated]...

This prevents unusually large compiler or test output from unnecessarily increasing repair-prompt size.

### Design Decision — Original Java Not Included

The Step 3.1 repair prompt does not include the original Java source.

The repair model receives only:

    current Go code
    +
    failure status
    +
    compiler/test output

This establishes the repair-without-source condition.

The project plan later calls for an ablation comparing repair prompts with and without the original Java implementation.

### Tests Added

Repair prompt tests verify that:

- current Go code appears in the prompt;
- RunResult status appears in the prompt;
- failure output appears in the prompt;
- stdout and stderr are both preserved;
- failure output is truncated correctly;
- the prompt requests full corrected source;
- the prompt requires exactly one Go code block;
- package main is required;
- tests and main functions are forbidden;
- explanations outside the code block are forbidden.

Existing Milestone 2 initial-prompt tests remain unchanged.

### Step-Specific Verification

Command:

    python -m pytest tests/test_prompts.py -v

Result:

    9 passed

Prompt tests currently consist of:

    4 initial migration prompt tests
    5 repair prompt tests

### Problem Encountered

The first truncation implementation counted the:

    STDOUT:

label as one of the 60 allowed feedback lines.

As a result, only 59 actual output lines were preserved.

The implementation was corrected so the 60-line limit now applies only to actual compiler/test output.

### Milestone 3 Progress

Completed:

- Step 3.1 — Repair prompt

Not yet implemented:

- repair-loop orchestration;
- iterative migration attempts;
- stopping on PASS;
- maximum repair iteration enforcement;
- run metadata;
- real repair evaluation.

### Next Action

Run the complete harness regression suite.

If all tests pass, commit Step 3.1 before beginning Step 3.2 — Repair Loop.


## Step 3.2 — Repair Loop Orchestration

### Status

Completed.

### Files Modified

    src/migrate_eval/loop.py
    tests/test_loop.py

### Goal

Extend the Milestone 2 single-shot migration pipeline into an iterative repair loop.

The repair loop allows failed Go migrations to be sent back to the model with compiler/test feedback for up to a configured number of repair rounds.

### MigrationAttempt Iteration Tracking

MigrationAttempt now records:

    iteration

Iteration numbering is:

    0 = initial migration
    1 = first repair
    2 = second repair
    3 = third repair

The default iteration for migrate_once() remains:

    0

This preserves compatibility with the Milestone 2 single-shot path.

### Shared Attempt Execution

Created internal helper:

    _execute_prompt(...)

This centralizes the common attempt pipeline:

    prompt
        ->
    model.complete(...)
        ->
    Go extraction
        ->
    Docker oracle
        ->
    MigrationAttempt

The helper is reused by both:

    migrate_once(...)
    migrate(...)

This avoids duplicating model, extraction, runner, MODEL_ERROR, and EXTRACT_ERROR handling.

### Repair Loop

Created:

    migrate(problem, model, iters, runner=...)

Behavior:

1. Run the initial migration as iteration 0.
2. If iteration 0 passes, stop immediately.
3. If it fails and repair iterations remain:
   - build a repair prompt from the latest failed Go code;
   - include the latest RunResult feedback;
   - execute the repaired implementation;
   - record the new iteration.
4. Stop immediately when any iteration returns PASS.
5. Otherwise continue until the configured repair limit is reached.

### Iteration Semantics

The iters argument represents the number of repair rounds.

Therefore:

    iters=0

means:

    iteration 0 only

and:

    iters=3

allows at most:

    iteration 0
    iteration 1
    iteration 2
    iteration 3

for a maximum of four total model attempts.

### Failure Handling

If an attempt results in:

    MODEL_ERROR
    EXTRACT_ERROR

and no valid Go code is available, the repair loop stops.

This prevents attempting to construct a repair prompt when there is no extracted implementation to repair.

Compiler failures and test failures remain repairable because the failed Go code is available.

### Backward Compatibility

The existing:

    migrate_once(...)

function remains available.

Its behavior is unchanged from Milestone 2 except that the returned MigrationAttempt explicitly records:

    iteration = 0

This preserves the existing single-shot migration path while adding repair-loop support separately.

### Validation Rules

The repair loop verifies that:

- initial PASS stops immediately;
- failed code is sent to a repair prompt;
- repair feedback includes the previous failure;
- PASS during repair stops further iterations;
- maximum repair count is respected;
- iters=0 preserves single-shot behavior;
- iteration numbers are recorded correctly;
- EXTRACT_ERROR stops when no Go code is available;
- negative repair counts are rejected.

### Tests

The loop test suite now contains:

    11 tests

including the original Milestone 2 single-shot tests and new repair-loop tests.

### Step-Specific Verification

Command:

    python -m pytest tests/test_loop.py -v

Result:

    11 passed

### Milestone 3 Progress

Completed:

- Step 3.1 — Repair prompt
- Step 3.2 — Repair loop orchestration

Not yet implemented:

- CLI support for repair iterations;
- per-run reproducibility metadata;
- real 20-problem repair evaluation.

### Next Action

Run the complete harness regression suite.

If all tests pass, commit Step 3.2 before beginning the next Milestone 3 step.


## Step 3.3 — Run Metadata and Reproducibility

### Status

Completed.

### Files Modified

    src/migrate_eval/results.py
    src/migrate_eval/cli.py
    tests/test_results.py
    tests/test_cli.py

### Goal

Add reproducibility metadata for evaluation runs before enabling repair iterations through the command-line interface.

Each evaluation run now records both:

    <run_id>.jsonl
    <run_id>.meta.json

The JSONL file contains individual migration attempts.

The metadata file contains run-level configuration.

### MigrationAttempt Iteration Logging

Result persistence now reads the iteration directly from:

    MigrationAttempt.iteration

The previous separate:

    iteration=...

argument was removed from:

    attempt_to_record(...)
    append_attempt(...)

This prevents repair attempts from accidentally being persisted with an incorrect iteration number.

### Prompt Configuration Hash

Created:

    prompt_config_hash(...)

The function computes a stable SHA-256 hash over the configured prompt texts.

The hash changes if the initial or repair prompt configuration changes.

This provides a compact way to identify which prompt version was used for an evaluation run.

### Run Metadata

Created:

    write_run_metadata(...)

Each metadata file records:

    run_id
    created_at_utc
    model
    iters
    requested_n
    selected_n
    task_ids
    excluded_task_ids
    temperature
    prompt_hash

### Benchmark Exclusion Metadata

The known flaky benchmark item remains excluded:

    Go/95

The exclusion is now explicitly recorded in each metadata file.

### Model Configuration

The CLI records the model adapter's temperature setting when available.

For adapters where no explicit temperature is configured, the metadata value may be:

    null

This accurately reflects the effective adapter configuration rather than inventing a value.

### CLI Output

Each run now produces:

    results/<model>/<run_id>.jsonl
    results/<model>/<run_id>.meta.json

The CLI prints the locations of both files when the run finishes.

### Repair Iterations

Repair iterations are intentionally not enabled through the CLI in this step.

The CLI still executes:

    migrate_once(...)

and currently accepts only:

    --iters 0

This isolates metadata/reproducibility changes from repair-loop CLI integration.

Repair execution through the CLI will be connected in the next step.

### Tests

Results tests now verify:

- MigrationAttempt iteration is persisted automatically;
- JSONL remains append-only;
- failure statuses remain preserved;
- prompt hashes are stable;
- prompt hashes change when prompt configuration changes;
- metadata files contain the expected reproducibility configuration.

CLI tests now verify:

- model adapter selection;
- unsupported providers are rejected;
- repair iterations remain disabled during this step;
- JSONL output is produced;
- metadata output is produced;
- selected benchmark task IDs are recorded;
- benchmark exclusions are recorded;
- temperature is recorded;
- prompt hash is recorded.

### Step-Specific Verification

Command:

    python -m pytest \
      tests/test_results.py \
      tests/test_cli.py \
      -v

Result:

    14 passed

### Milestone 3 Progress

Completed:

- Step 3.1 — Repair prompt
- Step 3.2 — Repair loop orchestration
- Step 3.3 — Run metadata and reproducibility

Not yet implemented:

- CLI execution of repair iterations;
- real 20-problem repair evaluation;
- saved FAIL -> repair -> PASS demonstration trace.

### Next Action

Run the complete harness regression suite.

If all tests pass, commit Step 3.3 before enabling repair iterations through the CLI.

## Step 3.4 — CLI Repair-Loop Integration

### Status

Completed.

### Files Modified

    src/migrate_eval/cli.py
    tests/test_cli.py

### Goal

Connect the repair-loop orchestration implemented in Step 3.2 to the command-line interface.

The CLI can now execute:

    iteration 0
    repair iteration 1
    repair iteration 2
    repair iteration 3

depending on the value supplied through:

    --iters

### CLI Execution Change

The CLI previously executed:

    migrate_once(...)

for every benchmark problem.

It now executes:

    migrate(
        problem,
        adapter,
        iters=iters,
    )

This allows the command-line evaluation path to use the repair loop.

### Iteration Semantics

The CLI follows the repair-loop convention:

    --iters 0

means:

    initial migration only

while:

    --iters 3

allows:

    iteration 0
    iteration 1
    iteration 2
    iteration 3

for a maximum of four attempts per problem.

The repair loop stops early when a problem passes.

### Attempt Persistence

Every generated attempt is appended to the run JSONL file.

For example, a problem that fails initially and succeeds on the first repair produces two records:

    iteration 0 — TEST_FAIL
    iteration 1 — PASS

A problem that passes immediately produces only:

    iteration 0 — PASS

### Cumulative Pass Reporting

The CLI now reports cumulative pass rate for each allowed iteration.

A problem counts as passing at iteration N if it passed during any attempt from:

    iteration 0 through iteration N

For example:

    iteration 0: 1/2 PASS
    iteration 1: 2/2 PASS
    iteration 2: 2/2 PASS
    iteration 3: 2/2 PASS

This matches the benchmark metric used for measuring improvement from repair rounds.

### Per-Problem Output

The CLI reports each problem's final status and the iteration at which execution stopped.

Example:

    Go/0 PASS (iteration 0)
    Go/1 PASS (iteration 1)

### Metadata

The metadata implementation from Step 3.3 remains active.

The selected:

    --iters

value is stored in:

    <run_id>.meta.json

alongside model, prompt hash, task IDs, exclusions, and model configuration.

### Backward Compatibility

Single-shot evaluation remains supported:

    --iters 0

This preserves the Milestone 2 evaluation behavior while using the same general migration-loop interface.

### Tests

CLI tests verify:

- adapter selection still works;
- unknown model providers are rejected;
- single-shot runs still work with --iters 0;
- repair runs accept --iters 3;
- every attempt is written to JSONL;
- iteration numbers are preserved;
- repair success is reflected in final task output;
- cumulative pass rate is reported correctly;
- metadata records the configured repair count.

### Step-Specific Verification

Command:

    python -m pytest tests/test_cli.py -v

Result:

    5 passed

### Milestone 3 Progress

Completed:

- Step 3.1 — Repair prompt
- Step 3.2 — Repair loop orchestration
- Step 3.3 — Run metadata and reproducibility
- Step 3.4 — CLI repair-loop integration

Remaining:

- Step 3.5 — Real repair-loop evaluation on the same 20 benchmark problems used in Milestone 2
- Save at least one real FAIL -> repair -> PASS trace

### Next Action

Run the complete harness regression suite.

If all tests pass, commit Step 3.4 before starting the real repair evaluation.

## Step 3.5 — Real Repair-Loop Evaluation

### Status

Completed.

### Goal

Evaluate the Milestone 3 repair loop on the same first 20 usable HumanEval-X Java-to-Go problems used for the Milestone 2 single-shot evaluation.

Both configured models were evaluated with:

    --n 20
    --iters 3

Iteration 0 is the initial migration.

Iterations 1–3 are repair rounds.

The loop stops immediately when a problem passes.

---

### Qwen Repair Evaluation

Model:

    ollama:qwen2.5-coder:14b

Command:

    migrate-eval run \
      --model ollama:qwen2.5-coder:14b \
      --n 20 \
      --iters 3

Results:

    iteration 0: 15/20 PASS — 75.0%
    iteration 1: 16/20 PASS — 80.0%
    iteration 2: 16/20 PASS — 80.0%
    iteration 3: 16/20 PASS — 80.0%

Repair improvement within this run:

    75.0% -> 80.0%

Absolute improvement:

    +5 percentage points

Additional problems repaired:

    1

Successful repair:

    Go/4
    PASS at iteration 1

Residual failures after iteration 3:

    Go/7   TEST_FAIL
    Go/10  COMPILE_ERROR
    Go/12  COMPILE_ERROR
    Go/16  TEST_FAIL

The previous Milestone 2 single-shot Qwen run produced:

    14/20
    70.0%

The iteration-0 result in the repair evaluation was instead:

    15/20
    75.0%

Because local model execution may vary between runs, repair improvement is measured primarily within the same repair run:

    75.0% -> 80.0%

Result file:

    results/ollama__qwen2.5-coder__14b/
    20260913T154621Z-47577885.jsonl

Metadata file:

    results/ollama__qwen2.5-coder__14b/
    20260913T154621Z-47577885.meta.json

---

### GPT-5.6 Terra Repair Evaluation

Model:

    openai:gpt-5.6-terra

Command:

    migrate-eval run \
      --model openai:gpt-5.6-terra \
      --n 20 \
      --iters 3

Results:

    iteration 0: 18/20 PASS — 90.0%
    iteration 1: 19/20 PASS — 95.0%
    iteration 2: 20/20 PASS — 100.0%
    iteration 3: 20/20 PASS — 100.0%

Repair improvement within this run:

    90.0% -> 100.0%

Absolute improvement:

    +10 percentage points

Both initial failures were repaired.

Successful repairs:

    Go/16
    PASS at iteration 1

    Go/2
    PASS at iteration 2

No residual failures remained after iteration 2.

The iteration-0 result exactly reproduced the previous Milestone 2 GPT-5.6 Terra baseline:

    18/20
    90.0%

Result file:

    results/openai__gpt-5.6-terra/
    20260913T160413Z-40bbd5c5.jsonl

Metadata file:

    results/openai__gpt-5.6-terra/
    20260913T160413Z-40bbd5c5.meta.json

---

### Model Comparison

Repair-run cumulative pass rates:

| Model | Iteration 0 | Iteration 1 | Iteration 2 | Iteration 3 |
|---|---:|---:|---:|---:|
| qwen2.5-coder:14b | 75.0% | 80.0% | 80.0% | 80.0% |
| gpt-5.6-terra | 90.0% | 95.0% | 100.0% | 100.0% |

Within-run improvement:

    qwen2.5-coder:14b
    +5 percentage points

    gpt-5.6-terra
    +10 percentage points

### Repair Effectiveness

Qwen initial failures:

    5

Qwen failures repaired:

    1 / 5
    20%

GPT-5.6 Terra initial failures:

    2

GPT-5.6 Terra failures repaired:

    2 / 2
    100%

These values describe only this 20-problem sample and are not yet the final full-benchmark results.

---

### Saved Repair Trace

A complete real repair trace was preserved for:

    Go/2
    openai:gpt-5.6-terra

Trace:

    iteration 0 — COMPILE_ERROR
    iteration 1 — TEST_FAIL
    iteration 2 — PASS

Iteration 0 generated:

    number % 1.0

Go rejected the floating-point remainder operator.

Iteration 1 repaired compilation using:

    math.Trunc(number)

The code compiled, but the tests showed a semantic error:

    expected 0.5
    actual 3

Iteration 2 repaired the behavior using:

    math.Modf(number)

The target-language test suite then passed.

Permanent trace documentation:

    docs/repair-traces/gpt-5.6-terra-go2.md

This trace is a strong demonstration of the repair-loop design because it shows:

    compiler feedback
        ->
    compilation repair
        ->
    behavioral test feedback
        ->
    semantic repair
        ->
    PASS

---

# Milestone 3 — Repair Loop

## Status

COMPLETED.

### Completed

- repair prompt;
- compiler/test feedback injection;
- 60-line feedback truncation;
- iterative repair orchestration;
- early stopping on PASS;
- configurable repair limit;
- iteration tracking;
- MODEL_ERROR / EXTRACT_ERROR handling;
- JSONL logging of every attempt;
- per-run metadata;
- prompt configuration hashing;
- CLI support for --iters;
- cumulative pass reporting by iteration;
- real 20-problem Qwen evaluation;
- real 20-problem GPT-5.6 Terra evaluation;
- real FAIL -> repair -> PASS trace preserved.

### Milestone 3 Exit Results

Qwen:

    iteration 0: 75.0%
    iteration 3: 80.0%

GPT-5.6 Terra:

    iteration 0: 90.0%
    iteration 3: 100.0%

The repair loop improved pass rate for both evaluated models on the 20-problem sample.

### Next Milestone

Milestone 4 — Full Evaluation

Main objectives:

- run the validated benchmark set across both models;
- aggregate JSONL results;
- report pass rate by iteration and model;
- analyze failure taxonomy;
- generate evaluation plots;
- prepare results for the README.

Milestone 4 must begin in a new chat.


# Milestone 4 — Full Evaluation

## Goal

Run the validated HumanEval-X Java-to-Go benchmark across the configured models, aggregate the results, analyze repair effectiveness and failure taxonomy, and generate the final evaluation tables and plots required for the README.

Validated benchmark set:

    163 problems

Excluded benchmark item:

    Go/95

Reason:

    canonical HumanEval-X Go implementation is nondeterministic because it depends on unspecified Go map iteration order.

---

## Step 4.1 — Model Telemetry Persistence

### Status

Completed.

### Goal

Ensure the full Milestone 4 evaluation persists model-call latency and token usage before running the complete 163-problem benchmark.

The Milestone 4 analysis requires:

- mean model latency;
- mean input tokens;
- mean output tokens.

The model adapters already observed these values during execution, but prior JSONL result records did not preserve them.

Running the full evaluation before fixing this would have lost telemetry required for later aggregation.

### Files Modified

    src/migrate_eval/models/openai_adapter.py
    src/migrate_eval/models/ollama_adapter.py
    src/migrate_eval/loop.py
    src/migrate_eval/results.py
    tests/test_openai_adapter.py
    tests/test_ollama_adapter.py
    tests/test_loop.py
    tests/test_results.py

### OpenAI Token Telemetry

OpenAIAdapter now exposes the token usage from its most recent successful completion through:

    last_input_tokens
    last_output_tokens

These values are populated from the OpenAI Responses API usage fields:

    input_tokens
    output_tokens

They are reset before every new completion so stale telemetry cannot be reused accidentally.

### Ollama Token Telemetry

OllamaAdapter now exposes the same normalized attributes:

    last_input_tokens
    last_output_tokens

The values are populated from Ollama response fields:

    prompt_eval_count
    eval_count

Using the same attribute names across adapters allows the migration loop to persist token telemetry without provider-specific logic.

### Model Latency

Model-call duration is measured centrally in:

    loop.py

using:

    time.perf_counter()

The timer wraps:

    model.complete(prompt)

This means model latency is captured consistently for:

- OpenAI;
- Ollama;
- future ModelAdapter implementations;
- MODEL_ERROR attempts.

### MigrationAttempt Telemetry

MigrationAttempt now records:

    model_duration
    input_tokens
    output_tokens

Default values preserve compatibility with existing mocked adapters and older test construction:

    model_duration = 0.0
    input_tokens = None
    output_tokens = None

### Duration Semantics

The existing JSONL field:

    duration

continues to represent:

    Go Docker oracle/test execution duration

The new field:

    model_duration

represents:

    LLM completion latency

These values are intentionally kept separate so later evaluation can distinguish model generation time from target-language test execution time.

### JSONL Persistence

Every new migration-attempt record now contains:

    model_duration
    input_tokens
    output_tokens

alongside the existing fields:

    task_id
    model
    iteration
    prompt
    raw_response
    go_code
    status
    stdout
    stderr
    duration

### Failure Behavior

If the model call itself raises an exception:

    MODEL_ERROR

the elapsed model-call duration is still recorded.

Token counts remain unavailable in that case unless the provider supplied them before failing.

### Tests Added

OpenAI adapter:

- verifies input/output token counts are retained after a successful completion.

Ollama adapter:

- verifies prompt/evaluation token counts are mapped to the normalized telemetry attributes.

Migration loop:

- verifies model latency and token usage propagate into MigrationAttempt.

Results persistence:

- verifies telemetry fields are written into the JSONL-compatible result record.

### Step-Specific Verification

Command:

    python -m pytest \
      tests/test_openai_adapter.py \
      tests/test_ollama_adapter.py \
      tests/test_loop.py \
      tests/test_results.py \
      -v

Result:

    32 passed

### Full Harness Regression

Command:

    make test

Result:

    79 passed

No existing Milestone 0–3 behavior was broken.

### Milestone 4 Progress

Completed:

- Step 4.1 — Model telemetry persistence

Not yet completed:

- full-evaluation preflight and API cost protection;
- full 163-problem OpenAI evaluation;
- full 163-problem Ollama evaluation;
- JSONL aggregation;
- pass rate by iteration and model;
- failure taxonomy analysis;
- mean latency/token analysis;
- evaluation plots.

### Next Action

Commit Step 4.1 before beginning the full-evaluation preflight and cost-safety work.


## Step 4.2 — Full-Run Preflight, Cost Protection, and Model Cache

### Status

Completed.

### Goal

Prepare the evaluation harness for the full 163-problem benchmark before launching expensive or long-running model evaluations.

This step added:

- API cost estimation;
- a configurable cost safety limit;
- real-run cost validation;
- persistent model-response caching;
- cache-aware cost accounting.

### Cost Estimation

Created:

    src/migrate_eval/costs.py

The evaluation harness now supports configured per-token pricing for:

    openai:gpt-5.6-terra

Configured rates:

    input:  $2.00 per 1M tokens
    output: $12.00 per 1M tokens

Cost is calculated using the token telemetry persisted in Step 4.1.

If token telemetry or model pricing is unavailable, no cost estimate is produced.

### --max-cost Safety Limit

The CLI now supports:

    --max-cost <USD>

Example:

    migrate-eval run \
      --model openai:gpt-5.6-terra \
      --n 163 \
      --iters 3 \
      --max-cost 3.00

The limit is a soft per-run safety limit.

Cost is checked after each benchmark problem completes.

If the accumulated estimated API cost reaches or exceeds the configured limit, the harness stops before starting the next problem.

This prevents an unexpectedly expensive evaluation from continuing indefinitely.

### Early-Stop Reporting

When a cost-limited run stops early, pass-rate reporting now uses:

    actually evaluated problems

rather than the originally selected problem count.

This prevents incorrect denominators in partial runs.

### Run Metadata

The configured cost limit is recorded in:

    <run_id>.meta.json

under:

    max_cost_usd

### Real OpenAI Preflight

A real five-problem GPT-5.6 Terra evaluation was executed:

    migrate-eval run \
      --model openai:gpt-5.6-terra \
      --n 5 \
      --iters 3 \
      --max-cost 1.00

Results:

    Go/0 PASS iteration 0
    Go/1 PASS iteration 0
    Go/2 PASS iteration 2
    Go/3 PASS iteration 0
    Go/4 PASS iteration 0

Cumulative pass rates:

    iteration 0: 4/5 — 80.0%
    iteration 1: 4/5 — 80.0%
    iteration 2: 5/5 — 100.0%
    iteration 3: 5/5 — 100.0%

Model attempts:

    7

Observed telemetry:

    total input tokens:   1,979
    total output tokens:  1,466
    mean model latency:   4.162 seconds

Estimated API cost:

    $0.0216

The independently calculated token cost matched the CLI estimate.

### Full-Run Cost Estimate

Scaling the five-problem preflight directly to the validated 163-problem benchmark gives an approximate expected cost of:

    ~$0.70

Actual cost will depend on how many repair rounds are required.

A larger safety limit can therefore be used for the official evaluation without materially risking unexpected spend.

### Persistent Model Completion Cache

Created:

    src/migrate_eval/cache.py

Implemented:

    CachedModelAdapter
    completion_cache_key(...)

Cache keys are generated from:

    model name
    +
    exact prompt text

using SHA-256.

This means an identical model/prompt request can reuse the previously generated completion without another provider request.

### Cache Storage

The CLI automatically stores model completions beneath:

    <results-dir>/.cache/

Cache records preserve:

    model
    response
    input_tokens
    output_tokens
    model_duration

### Cache Telemetry

MigrationAttempt now records:

    cache_hit

The field is also persisted in JSONL.

This allows later analysis to distinguish:

    real model calls
    cached model calls

### Cache-Aware Cost Accounting

Cached completions retain their original token counts for reproducibility and analysis.

However:

    cache_hit = true

attempts do not contribute to the current run's estimated API spend.

Therefore rerunning an identical evaluation does not falsely report previously paid API cost as new spend.

### Real Cache Verification

A dedicated temporary results directory was used:

    /tmp/migrate-eval-cache-check

The same real GPT-5.6 Terra evaluation was executed twice.

First execution:

    Go/0 PASS
    Estimated API cost: $0.0018

Second identical execution:

    Go/0 PASS
    Estimated API cost: $0.0000

The second execution reused the disk cache and did not require another paid OpenAI completion.

The temporary directory ensured this verification did not populate the cache intended for the official full evaluation.

### Tests Added

Cost tests cover:

- configured GPT-5.6 Terra pricing;
- token-to-cost calculation;
- unknown-model handling;
- missing token telemetry.

CLI tests cover:

- unsupported pricing rejection;
- cost-limit stopping;
- correct partial-run denominator;
- cached attempts not counted as new API spend.

Cache tests cover:

- stable cache keys;
- cache misses invoking the wrapped model;
- cache hits avoiding repeated model calls;
- token/latency telemetry restoration;
- different prompts producing independent cache entries.

Results tests cover:

- cache-hit persistence in JSONL.

### Step-Specific Verification

Cost/CLI/results targeted suite:

    21 passed

Cache/CLI/loop/results targeted suite:

    35 passed

### Full Harness Regression

Command:

    make test

Result:

    91 passed

No existing Milestone 0–3 behavior was broken.

### Milestone 4 Progress

Completed:

- Step 4.1 — Model telemetry persistence
- Step 4.2 — Full-run preflight, cost protection, and model cache

Remaining:

- Step 4.3 — Full OpenAI evaluation
- Step 4.4 — Full Ollama evaluation
- Step 4.5 — Results aggregation
- Step 4.6 — Evaluation plots and final Milestone 4 verification

### Next Action

Commit Step 4.2.

Then begin the official full 163-problem GPT-5.6 Terra evaluation with up to three repair rounds.


## Step 4.3A — Parallel Evaluation Support

### Status

Completed.

### Goal

Allow independent HumanEval-X benchmark problems to execute concurrently so the full API-based evaluation can finish substantially faster.

Repair iterations for an individual problem remain sequential because each repair depends on the previous compiler or test result.

### Files Modified

    src/migrate_eval/cli.py
    src/migrate_eval/results.py
    tests/test_cli.py

### CLI Option

Added:

    --workers

Default:

    1

Example:

    migrate-eval run \
      --model openai:gpt-5.6-terra \
      --n 163 \
      --iters 3 \
      --workers 4

A default of one worker preserves the original sequential behavior.

### Parallel Execution Design

Parallelism operates across benchmark problems.

For example:

    worker 1 -> Go/0 -> repairs if needed
    worker 2 -> Go/1 -> repairs if needed
    worker 3 -> Go/2 -> repairs if needed
    worker 4 -> Go/3 -> repairs if needed

Each problem's internal repair sequence remains:

    iteration 0
    -> iteration 1
    -> iteration 2
    -> iteration 3

and therefore remains sequential.

### Thread-Safe Model Design

Model adapters contain mutable per-call telemetry including:

    last_input_tokens
    last_output_tokens
    last_model_duration
    last_cache_hit

Therefore a single adapter instance is not shared between worker threads.

Each concurrent benchmark problem receives its own:

    model adapter
    +
    CachedModelAdapter

All workers share the same disk cache directory.

### Result Persistence

Worker threads perform model generation, extraction, repair, and Docker oracle execution.

Completed problem results are returned to the main thread.

The main thread performs:

    JSONL append
    cost accounting
    terminal output

This avoids concurrent JSONL writes.

### Output Ordering

Parallel runs may print problems in completion order rather than task-number order.

Example observed:

    Go/3
    Go/0
    Go/2
    Go/1

This is expected and does not affect benchmark correctness because each record includes its task_id and iteration.

### Cost Limit Behavior

The soft --max-cost limit remains supported.

When multiple workers are active, already-running tasks are allowed to finish after the cost threshold is reached.

No additional problems are submitted after the threshold is detected.

Therefore a parallel run may exceed the soft limit by the cost of already-running problems.

### Run Metadata

The number of configured workers is now stored in:

    <run_id>.meta.json

under:

    workers

### Tests Added

Parallel CLI tests verify:

- two benchmark problems actually execute concurrently;
- final pass-rate aggregation remains correct;
- worker count is persisted in metadata;
- cost-limit detection stops submission of new problems;
- already-running parallel problems are allowed to finish.

### Targeted Verification

Command:

    python -m pytest \
      tests/test_cli.py \
      tests/test_results.py \
      -v

Result:

    21 passed

### Full Harness Regression

Command:

    make test

Result:

    93 passed

### Real Parallel OpenAI Smoke Test

Command:

    migrate-eval run \
      --model openai:gpt-5.6-terra \
      --n 4 \
      --iters 0 \
      --workers 4 \
      --max-cost 0.10

A temporary results directory was used so the official benchmark cache remained untouched.

Results:

    Go/0 PASS
    Go/1 PASS
    Go/2 COMPILE_ERROR
    Go/3 PASS

pass@1:

    3/4
    75.0%

Estimated API cost:

    $0.0060

The tasks completed in non-sequential order, confirming actual concurrent execution.

### Conclusion

Parallel benchmark execution is ready for the full OpenAI evaluation.

Recommended configuration:

    OpenAI: 4 workers

Local Ollama evaluation will initially remain at:

    1 worker

because multiple simultaneous local generations may compete for the same GPU and unified memory.

### Next Action

Run the official 163-problem GPT-5.6 Terra evaluation with up to three repair rounds and four concurrent workers.


## Step 4.3 — Full OpenAI Evaluation

### Status

Completed.

### Goal

Run GPT-5.6 Terra across the complete validated HumanEval-X Java-to-Go benchmark with up to three repair iterations.

### Evaluation Configuration

Model:

    openai:gpt-5.6-terra

Validated benchmark size:

    163 problems

Excluded benchmark item:

    Go/95

Repair configuration:

    iteration 0 = initial migration
    iterations 1-3 = repair rounds

Concurrent workers:

    4

Cost safety limit:

    $3.00

Command:

    migrate-eval run \
      --model openai:gpt-5.6-terra \
      --n 163 \
      --iters 3 \
      --workers 4 \
      --max-cost 3.00

### Result Files

JSONL:

    results/openai__gpt-5.6-terra/
    20260914T125653Z-c85029de.jsonl

Metadata:

    results/openai__gpt-5.6-terra/
    20260914T125653Z-c85029de.meta.json

### Run Integrity Validation

JSONL records:

    176

Unique benchmark tasks:

    163

Missing tasks:

    none

Unexpected tasks:

    none

Duplicate task/iteration records:

    none

Tasks missing iteration 0:

    none

Cache hits:

    0

The official run therefore contains a fresh model evaluation for the complete validated benchmark.

### Cumulative Pass Rate

    iteration 0: 153 / 163 — 93.9%
    iteration 1: 161 / 163 — 98.8%
    iteration 2: 162 / 163 — 99.4%
    iteration 3: 162 / 163 — 99.4%

Absolute improvement from iteration 0 to final:

    +5.5 percentage points

Initial failures:

    10

Failures repaired:

    9 / 10
    90%

### Initial Failure Taxonomy

At iteration 0:

    PASS           153
    COMPILE_ERROR    6
    TEST_FAIL        4

No initial failures were classified as:

    TIMEOUT
    EXTRACT_ERROR
    MODEL_ERROR

### Repair Progress

After repair iteration 1:

    161 / 163 PASS

Therefore the first repair round recovered:

    8 of the 10 initial failures

After repair iteration 2:

    162 / 163 PASS

The second repair round recovered:

    1 additional failure

Iteration 3 produced:

    no additional passes

### Final Failure Taxonomy

Final status:

    PASS       162
    TEST_FAIL    1

Only one benchmark problem remained unresolved:

    Go/160

Final status:

    TEST_FAIL

Final iteration:

    3

### Model Telemetry

Total input tokens:

    60,917

Total output tokens:

    34,052

Mean model-call latency:

    3.98 seconds

Total model attempts:

    176

### API Cost

Reported evaluation cost:

    $0.5305

The full 163-problem GPT-5.6 Terra benchmark therefore remained well below the configured:

    $3.00

safety limit.

### Main Finding

GPT-5.6 Terra achieved:

    93.9%

single-shot pass@1 on the validated 163-problem Java-to-Go benchmark.

Allowing test-driven repair increased cumulative pass@1 to:

    99.4%

The repair loop successfully recovered:

    9 / 10

initially failing migrations.

Most of the improvement occurred during the first repair iteration.

### Milestone 4 Progress

Completed:

- Step 4.1 — Model telemetry persistence
- Step 4.2 — Full-run preflight, cost protection, and model cache
- Step 4.3A — Parallel evaluation support
- Step 4.3 — Full OpenAI evaluation

Remaining:

- Step 4.4 — Full Ollama evaluation
- Step 4.5 — Results aggregation
- Step 4.6 — Evaluation plots and final Milestone 4 verification

### Next Action

Commit the validated GPT-5.6 Terra full-evaluation results and audit update.

Then begin Step 4.4 — Full Ollama Evaluation.


## Step 4.4 — Full Ollama Evaluation

### Status

Completed.

### Goal

Run the local qwen2.5-coder:14b model across the complete validated HumanEval-X Java-to-Go benchmark with up to three repair iterations.

### Evaluation Configuration

Model:

    ollama:qwen2.5-coder:14b

Validated benchmark size:

    163 problems

Excluded benchmark item:

    Go/95

Repair configuration:

    iteration 0 = initial migration
    iterations 1-3 = repair rounds

Concurrent workers:

    2

Command:

    migrate-eval run \
      --model ollama:qwen2.5-coder:14b \
      --n 163 \
      --iters 3 \
      --workers 2

### Worker Selection Preflight

A small four-problem timing comparison was performed before the full run.

One worker:

    4/4 PASS
    elapsed time: 1:20.95

Two workers:

    4/4 PASS
    elapsed time: 39.18 seconds

Two workers were therefore approximately:

    2.07x faster

for the measured sample.

The official evaluation used:

    2 workers

### Result Files

JSONL:

    results/ollama__qwen2.5-coder__14b/
    20260914T132926Z-8fc0f7f9.jsonl

Metadata:

    results/ollama__qwen2.5-coder__14b/
    20260914T132926Z-8fc0f7f9.meta.json

### Run Integrity Validation

JSONL records:

    256

Unique benchmark tasks:

    163

Missing tasks:

    none

Unexpected tasks:

    none

Duplicate task/iteration records:

    none

Tasks missing iteration 0:

    none

The full validated benchmark is therefore represented exactly once at iteration 0, with repair attempts recorded where required.

### Cumulative Pass Rate

    iteration 0: 118 / 163 — 72.4%
    iteration 1: 138 / 163 — 84.7%
    iteration 2: 140 / 163 — 85.9%
    iteration 3: 141 / 163 — 86.5%

Absolute improvement from iteration 0 to final:

    +14.1 percentage points

Initial failures:

    45

Failures repaired:

    23 / 45
    51.1%

### Repair Progress

The first repair iteration recovered:

    20 additional problems

Pass count therefore increased from:

    118
    to
    138

The second repair iteration recovered:

    2 additional problems

Pass count increased to:

    140

The third repair iteration recovered:

    1 additional problem

Final pass count:

    141

Most repair-loop improvement therefore occurred during the first repair iteration.

### Initial Failure Taxonomy

At iteration 0:

    PASS            118
    COMPILE_ERROR    30
    TEST_FAIL        15

No initial failures were classified as:

    TIMEOUT
    EXTRACT_ERROR
    MODEL_ERROR

### Final Failure Taxonomy

After all repair rounds:

    PASS            141
    COMPILE_ERROR     9
    TEST_FAIL        13

Residual failures:

    22

Final COMPILE_ERROR tasks:

    Go/10
    Go/12
    Go/26
    Go/29
    Go/32
    Go/38
    Go/44
    Go/124
    Go/127

Final TEST_FAIL tasks:

    Go/7
    Go/16
    Go/30
    Go/87
    Go/89
    Go/96
    Go/104
    Go/117
    Go/134
    Go/136
    Go/145
    Go/149
    Go/160

### Model Telemetry

Total input tokens recorded:

    101,202

Total output tokens recorded:

    32,010

Mean recorded model latency:

    5.24 seconds

### Cache Usage

Cache hits:

    29

These attempts reused previously cached completions for an identical:

    model
    +
    prompt

combination.

The cache does not change the generated response associated with that exact prompt; it avoids recomputing the same completion.

The benchmark pass-rate calculation therefore remains valid.

However, cached calls should not be treated as fresh runtime measurements.

For later latency analysis, Step 4.5 will distinguish:

    all recorded attempts

from:

    cache_hit == false

fresh model calls.

This prevents cache reuse from distorting model-latency comparisons.

### Main Finding

qwen2.5-coder:14b achieved:

    72.4%

single-shot pass@1 on the validated 163-problem Java-to-Go benchmark.

Allowing up to three test-driven repair rounds increased cumulative pass@1 to:

    86.5%

The repair loop recovered:

    23 / 45
    51.1%

initially failing migrations.

The absolute improvement:

    +14.1 percentage points

was larger than the absolute repair improvement observed for GPT-5.6 Terra, although the final overall pass rate remained substantially lower.

### Full Model Comparison So Far

GPT-5.6 Terra:

    iteration 0: 93.9%
    iteration 3: 99.4%
    improvement: +5.5 percentage points

qwen2.5-coder:14b:

    iteration 0: 72.4%
    iteration 3: 86.5%
    improvement: +14.1 percentage points

Interpretation:

The stronger model started much closer to the benchmark ceiling, leaving fewer failures available for repair.

The local Qwen model began with substantially more failures, and the repair loop recovered a larger absolute share of benchmark problems.

### Milestone 4 Progress

Completed:

- Step 4.1 — Model telemetry persistence
- Step 4.2 — Full-run preflight, cost protection, and model cache
- Step 4.3A — Parallel evaluation support
- Step 4.3 — Full OpenAI evaluation
- Step 4.4 — Full Ollama evaluation

Remaining:

- Step 4.5 — Results aggregation
- Step 4.6 — Evaluation plots and final Milestone 4 verification

### Next Action

Commit the validated Ollama full-evaluation audit.

Then begin Step 4.5 — Results Aggregation.


## Step 4.5 — Results Aggregation

### Status

Completed.

### Goal

Convert raw evaluation JSONL records into reusable tabular summaries for:

- cumulative pass@1 by repair iteration
- initial and final failure taxonomy
- token and latency telemetry
- model-level comparison metrics

### Implementation

Extended:

    src/migrate_eval/results.py

with the following analysis functions.

#### load_results

Loads one or more evaluation JSONL files into a pandas DataFrame.

Required record fields:

    task_id
    model
    iteration
    status

Adds:

    source_file

to preserve result-file provenance.

#### cumulative_pass_rates

Calculates cumulative pass@1 by:

    model
    iteration

A task counts as passed at iteration i if it has produced a PASS at any iteration <= i.

Returned fields:

    model
    iteration
    passed
    total
    pass_rate

#### failure_taxonomy

Produces initial and final status distributions for each model.

Initial status:

    iteration 0

Final status:

    PASS if the task succeeded during any allowed iteration

otherwise:

    status of the task's latest attempt

Returned fields:

    model
    stage
    status
    count
    total
    rate

#### telemetry_summary

Aggregates model-call telemetry by model.

Returned measurements include:

    attempts
    fresh_attempts
    cache_hits
    total_input_tokens
    total_output_tokens
    mean_input_tokens
    mean_output_tokens
    mean_model_latency
    mean_fresh_model_latency

Fresh-call latency excludes:

    cache_hit == true

attempts.

This allows runtime comparisons to avoid treating cache retrieval as fresh model execution.

#### evaluation_summary

Combines pass-rate and telemetry results into one row per model.

Includes:

    total_tasks
    initial_passed
    final_passed
    initial_failures
    repaired_failures
    pass_rate_i0
    pass_rate_i1
    pass_rate_i2
    pass_rate_i3
    improvement_pp
    repair_recovery_rate

plus the telemetry summary fields.

### Unit Tests

Extended:

    tests/test_results.py

Results-analysis tests now cover:

- loading one JSONL file
- loading multiple JSONL files
- cumulative pass counting
- independent model aggregation
- initial/final failure taxonomy
- successful repair represented as final PASS
- token aggregation
- cache aggregation
- latency aggregation
- fresh-call latency
- combined model evaluation summary

Result-specific test suite:

    21 passed

### Full Project Regression Test

Command:

    python -m pytest

Result:

    103 passed

No existing project tests regressed.

### Real Evaluation Validation

Loaded official full runs:

    GPT-5.6 Terra
    qwen2.5-coder:14b

Combined records:

    432

Models:

    ollama:qwen2.5-coder:14b
    openai:gpt-5.6-terra

### Cumulative Pass@1

qwen2.5-coder:14b:

    iteration 0: 118 / 163 — 72.4%
    iteration 1: 138 / 163 — 84.7%
    iteration 2: 140 / 163 — 85.9%
    iteration 3: 141 / 163 — 86.5%

GPT-5.6 Terra:

    iteration 0: 153 / 163 — 93.9%
    iteration 1: 161 / 163 — 98.8%
    iteration 2: 162 / 163 — 99.4%
    iteration 3: 162 / 163 — 99.4%

These values exactly reproduce the original evaluation-run summaries.

### Failure Taxonomy

qwen2.5-coder:14b initial:

    PASS            118
    COMPILE_ERROR    30
    TEST_FAIL        15

qwen2.5-coder:14b final:

    PASS            141
    COMPILE_ERROR     9
    TEST_FAIL        13

GPT-5.6 Terra initial:

    PASS            153
    COMPILE_ERROR     6
    TEST_FAIL         4

GPT-5.6 Terra final:

    PASS            162
    TEST_FAIL         1

### Model Comparison

qwen2.5-coder:14b:

    tasks: 163
    passes: 118 -> 141
    repaired failures: 23 / 45
    repair recovery rate: 51.1%
    absolute improvement: +14.1 percentage points

GPT-5.6 Terra:

    tasks: 163
    passes: 153 -> 162
    repaired failures: 9 / 10
    repair recovery rate: 90.0%
    absolute improvement: +5.5 percentage points

### Telemetry

qwen2.5-coder:14b:

    attempts: 256
    fresh attempts: 227
    cache hits: 29
    input tokens: 101,202
    output tokens: 32,010
    mean input tokens/attempt: 395.3
    mean output tokens/attempt: 125.0
    mean recorded model latency: 5.240 s
    mean fresh-call model latency: 5.070 s

GPT-5.6 Terra:

    attempts: 176
    fresh attempts: 176
    cache hits: 0
    input tokens: 60,917
    output tokens: 34,052
    mean input tokens/attempt: 346.1
    mean output tokens/attempt: 193.5
    mean recorded model latency: 3.980 s
    mean fresh-call model latency: 3.980 s

### Interpretation

GPT-5.6 Terra has substantially higher initial and final benchmark accuracy.

The repair loop recovered:

    90.0%

of Terra's initially failing tasks.

The repair loop recovered:

    51.1%

of Qwen's initially failing tasks.

Qwen gained more absolute percentage points because it began with substantially more failures available for repair.

Terra reached:

    99.4%

final cumulative pass@1.

Qwen reached:

    86.5%

final cumulative pass@1.

### Milestone 4 Progress

Completed:

- Step 4.1 — Model telemetry persistence
- Step 4.2 — Full-run preflight, cost protection, and cache
- Step 4.3A — Parallel evaluation workers
- Step 4.3 — Full OpenAI evaluation
- Step 4.4 — Full Ollama evaluation
- Step 4.5 — Results aggregation

Remaining:

- Step 4.6 — Evaluation plots and final Milestone 4 verification

### Next Action

Create the Milestone 4 evaluation plots from the reusable aggregation functions:

    pass rate vs repair iteration
    failure taxonomy at initial and final stages

Then perform final Milestone 4 verification.


## Step 4.6 — Evaluation Plots and Final Milestone 4 Verification

### Status

Completed.

### Goal

Produce the final visual evaluation artifacts required for Milestone 4 and verify the complete evaluation pipeline.

### Plotting Script

Created:

    scripts/plot_results.py

The script loads evaluation JSONL files through the reusable aggregation layer in:

    src/migrate_eval/results.py

and generates the required plots.

### Plot 1 — Pass Rate vs Repair Iteration

Generated:

    results/plots/pass_rate_vs_iteration.png

The plot shows cumulative pass@1 for both evaluated models across iterations 0–3.

GPT-5.6 Terra:

    iteration 0: 93.9%
    iteration 1: 98.8%
    iteration 2: 99.4%
    iteration 3: 99.4%

qwen2.5-coder:14b:

    iteration 0: 72.4%
    iteration 1: 84.7%
    iteration 2: 85.9%
    iteration 3: 86.5%

The plot was visually inspected and confirmed to match the underlying evaluation results.

### Plot 2 — Failure Taxonomy

Generated:

    results/plots/failure_taxonomy.png

The chart compares initial and final failure counts.

qwen2.5-coder:14b:

    initial failures: 45
        COMPILE_ERROR: 30
        TEST_FAIL: 15

    final failures: 22
        COMPILE_ERROR: 9
        TEST_FAIL: 13

GPT-5.6 Terra:

    initial failures: 10
        COMPILE_ERROR: 6
        TEST_FAIL: 4

    final failures: 1
        COMPILE_ERROR: 0
        TEST_FAIL: 1

The plot was visually inspected and confirmed to match the aggregation output.

### Static Analysis Cleanup

The pandas iteration code in:

    evaluation_summary

was adjusted to avoid Pylance attribute warnings from dynamically generated `itertuples()` namedtuple fields.

The implementation now uses:

    itertuples(index=False, name=None)

for explicit tuple unpacking.

Result-specific regression test:

    21 passed

### Final Regression Test

Command:

    python -m pytest

Result:

    103 passed

No regressions were detected.

The plotting script also passed Python bytecode compilation:

    python -m py_compile scripts/plot_results.py

### Final Evaluation Summary

GPT-5.6 Terra:

    initial pass@1: 93.9%
    final pass@1: 99.4%
    improvement: +5.5 percentage points
    failures repaired: 9 / 10
    repair recovery rate: 90.0%

qwen2.5-coder:14b:

    initial pass@1: 72.4%
    final pass@1: 86.5%
    improvement: +14.1 percentage points
    failures repaired: 23 / 45
    repair recovery rate: 51.1%

### Milestone 4 Exit Criteria

Full evaluation across the validated 163-problem benchmark:

    complete

Two evaluated models:

    complete

Cumulative pass@1 at iterations 0–3:

    complete

Failure taxonomy:

    complete

Token and latency telemetry:

    complete

Results aggregation:

    complete

Pass-rate plot:

    complete

Failure-taxonomy plot:

    complete

README results table:

    complete

Full regression suite:

    103 passed

### Milestone 4 Status

MILESTONE 4 — FULL EVALUATION: COMPLETE

The project now has reproducible full-benchmark measurements showing both single-shot migration performance and the effect of test-driven repair across two substantially different model configurations.


# Milestone 5 — Ship It

## Step 5.1 — Final README and Architecture

### Status

Completed.

### Goal

Turn the Milestone 4 evaluation README into the final project README and document the complete migrate-eval workflow clearly enough for someone outside the project to understand and run it.

### Files Modified

    README.md
    docs/PROJECT-AUDIT.md

### Files Added

    docs/images/migrate-eval-architecture.png

### README Updates

The README now includes:

- project motivation and Java-to-Go evaluation scope;
- architecture overview;
- repository structure;
- evaluation pipeline diagram;
- explanation of the migration and repair loop;
- full benchmark results for both evaluated models;
- pass@1 by repair iteration;
- failure taxonomy;
- evaluation plots;
- latency and token telemetry;
- installation instructions;
- CLI usage examples for Ollama and OpenAI;
- reproducibility and JSONL result structure;
- model completion caching;
- Docker sandbox design;
- oracle validation and Go/95 exclusion;
- repair-prompt design;
- evaluation metric;
- project limitations;
- real Go/2 repair trace;
- possible next steps;
- HumanEval-X / CodeGeeX credits;
- MIT licence reference.

### Architecture Diagram

Added:

    docs/images/migrate-eval-architecture.png

The diagram shows the full evaluation path:

    HumanEval-X
        ->
    Initial Migration Prompt
        ->
    LLM
        ->
    Go Code Extraction
        ->
    Docker Test Oracle
        ->
    PASS / FAIL

PASS results are persisted to JSONL.

Failures are sent through the repair prompt and looped back to the model for another attempt.

### README Style Decision

The final README was intentionally kept factual and technical rather than written as marketing copy.

The introduction, project motivation, results interpretation, and architecture explanation were written in a direct engineering-project style.

### Verification

The complete pytest suite was run after the README changes and passed successfully.

The architecture image was also verified in the rendered Markdown preview.

### Milestone 5 Progress

Completed:

- Step 5.1 — Final README and architecture

Remaining:

- Step 5.2 — Demo recording / GIF
- Step 5.3 — GitHub Actions CI
- Step 5.4 — Reproducibility and release verification
- Step 5.5 — Project launch

### Next Action

Create a short demo showing a real migration progressing from failure to PASS through the repair loop.

## Step 5.2 — Repair-Loop Demo

### Status

Completed.

### Goal

Add a short visual demonstration of the repair loop showing a real benchmark problem progressing from failure to a passing Go implementation.

### Files Added

    scripts/demo_repair.py
    docs/demo/migrate-eval-repair.gif

### Files Modified

    README.md
    docs/PROJECT-AUDIT.md

### Demo Problem

Task:

    Go/2

Model:

    openai:gpt-5.6-terra

Observed repair trace:

    iteration 0 — COMPILE_ERROR
    iteration 1 — TEST_FAIL
    iteration 2 — PASS

Iteration 0 failed because the generated Go implementation attempted to use the remainder operator with a float64 value.

Iteration 1 fixed compilation but still failed the target Go tests.

Iteration 2 corrected the behavior and passed the HumanEval-X Go test suite.

### Demo Script

Created:

    scripts/demo_repair.py

The script:

- loads the real HumanEval-X Java and Go benchmark data;
- selects Go/2;
- uses the existing GPT-5.6 Terra model adapter;
- uses the persistent model completion cache;
- runs the normal migrate-eval repair loop;
- displays each iteration status;
- shows a short compiler/test feedback excerpt for failed iterations.

The demo therefore uses the same migration, extraction, repair, and Docker oracle path as the evaluation harness.

### Cache Behavior

The recorded demo reused previously generated model responses from:

    results/.cache

All three completions were cache hits.

This allows the real evaluation trace to be demonstrated without repeating paid OpenAI requests.

### Demo Artifact

Created:

    docs/demo/migrate-eval-repair.gif

The GIF is embedded near the top of the README.

The rendered README was visually checked and the animation displays correctly.

### Verification

Demo script syntax check:

    python -m py_compile scripts/demo_repair.py

Result:

    PASS

Real demo execution:

    COMPILE_ERROR
    -> TEST_FAIL
    -> PASS

### Milestone 5 Progress

Completed:

- Step 5.1 — Final README and architecture
- Step 5.2 — Repair-loop demo

Remaining:

- Step 5.3 — GitHub Actions CI
- Step 5.4 — Reproducibility and release verification
- Step 5.5 — Project launch

### Next Action

Add GitHub Actions continuous integration so the harness pytest suite runs automatically on pushes and pull requests.

## Step 5.2 — Repair-Loop Demo

### Status

Completed.

### Implemented

Added:

    scripts/demo_repair.py
    docs/demo/migrate-eval-repair.gif

The demo uses the real Go/2 repair trace with GPT-5.6 Terra:

    iteration 0 — COMPILE_ERROR
    iteration 1 — TEST_FAIL
    iteration 2 — PASS

The demo script uses the normal migrate-eval pipeline and reuses cached model responses so the recording does not require new paid OpenAI calls.

The GIF is embedded near the top of README.md and was verified in the Markdown preview.

### Verification

    python -m py_compile scripts/demo_repair.py
    python -m pytest

The demo was also executed successfully and produced:

    COMPILE_ERROR -> TEST_FAIL -> PASS

### Milestone 5 Progress

Completed:

- Step 5.1 — Final README and architecture
- Step 5.2 — Repair-loop demo

Remaining:

- Step 5.3 — GitHub Actions CI
- Step 5.4 — Reproducibility and release verification
- Step 5.5 — Project launch

### Next Action

Add GitHub Actions CI for the pytest suite.

## Step 5.3 — GitHub Actions CI

### Status

Completed.

### Goal

Add continuous integration so the migrate-eval pytest suite runs automatically on pushes and pull requests.

### Files Added

    .github/workflows/tests.yml

### CI Workflow

The GitHub Actions workflow runs on:

    push
    pull_request

The workflow performs:

1. repository checkout;
2. Python 3.12 setup;
3. project installation with development dependencies;
4. Go Docker oracle image build;
5. pytest execution.

### CI Design

The workflow intentionally does not run:

    make setup

because the full setup target also requires:

    Ollama
    qwen2.5-coder:14b

These are not required for the harness test suite and would make CI unnecessarily heavy.

The CI workflow does not use:

    OpenAI API credentials
    real OpenAI requests
    real Ollama requests

Model behavior in pytest remains mocked.

Docker is built because the test suite contains integration tests for the real Go execution oracle.

### Verification

Local pytest suite:

    PASS

GitHub Actions workflow:

    PASS

Verified workflow stages:

    Check out repository
    Set up Python
    Install project
    Build Go test image
    Run tests

The workflow completed successfully on GitHub after being pushed to the main branch.

### Milestone 5 Progress

Completed:

- Step 5.1 — Final README and architecture
- Step 5.2 — Repair-loop demo
- Step 5.3 — GitHub Actions CI

Remaining:

- Step 5.4 — Reproducibility and release verification
- Step 5.5 — Project launch

### Next Action

Perform the final reproducibility, security, repository, and release-readiness checks before publishing the project as finished.
