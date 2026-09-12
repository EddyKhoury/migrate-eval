"""Sandboxed execution of generated Go code."""

from __future__ import annotations

import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class RunStatus(str, Enum):
    """Outcome categories used by the migration evaluation harness."""

    PASS = "PASS"
    COMPILE_ERROR = "COMPILE_ERROR"
    TEST_FAIL = "TEST_FAIL"
    TIMEOUT = "TIMEOUT"
    EXTRACT_ERROR = "EXTRACT_ERROR"
    MODEL_ERROR = "MODEL_ERROR"


@dataclass(frozen=True)
class RunResult:
    """Result of one target-language test execution."""

    status: RunStatus
    stdout: str
    stderr: str
    duration: float


def _classify_failed_go_test(stdout: str, stderr: str) -> RunStatus:
    """Classify a non-zero `go test` result."""

    output = f"{stdout}\n{stderr}".lower()

    compile_markers = (
        "[build failed]",
        "syntax error:",
        "undefined:",
        "declared and not used",
        "cannot use ",
    )

    if any(marker in output for marker in compile_markers):
        return RunStatus.COMPILE_ERROR

    return RunStatus.TEST_FAIL


def _timeout_output(value: str | bytes | None) -> str:
    """Normalize output captured from subprocess.TimeoutExpired."""

    if value is None:
        return ""

    if isinstance(value, bytes):
        return value.decode(errors="replace")

    return value


def run_go_tests(
    go_code: str,
    go_test: str,
    *,
    timeout: float = 30.0,
    image: str = "migrate-eval-go:latest",
) -> RunResult:
    """Run Go source and tests inside the Docker sandbox."""

    start = time.monotonic()

    with tempfile.TemporaryDirectory(prefix="migrate-eval-") as temp_dir:
        workdir = Path(temp_dir)

        # Write the temporary Go project on the host.
        # It will be mounted read-only inside Docker at /src.
        (workdir / "solution.go").write_text(
            go_code,
            encoding="utf-8",
        )

        (workdir / "solution_test.go").write_text(
            go_test,
            encoding="utf-8",
        )

        # HumanEval-X Go tests use github.com/stretchr/testify.
        # The dependency itself is baked into the Docker image so runtime
        # execution can remain completely network-isolated.
        (workdir / "go.mod").write_text(
            (
                "module migrateeval\n\n"
                "go 1.25\n\n"
                "require github.com/stretchr/testify v1.9.0\n"
            ),
            encoding="utf-8",
        )

        container_name = f"migrate-eval-{uuid.uuid4().hex}"

        command = [
            "docker",
            "run",
            "--rm",
            "--name",
            container_name,

            # Resource restrictions.
            "--cpus=1",
            "--memory=512m",

            # Generated code must never access the network.
            "--network=none",

            # Keep the container filesystem read-only.
            "--read-only",

            # Go needs writable temporary space for compilation,
            # generated binaries, go.sum, and build cache.
            "--tmpfs",
            "/tmp:rw,exec,nosuid,size=256m",

            # Store Go's build cache in the writable tmpfs.
            "--env",
            "GOCACHE=/tmp/go-cache",

            # Never attempt dependency downloads during benchmark execution.
            "--env",
            "GOPROXY=off",

            # The benchmark runs without contacting the public checksum DB.
            "--env",
            "GOSUMDB=off",

            # Host-created source files are visible inside the container
            # but cannot be modified by generated code.
            "--volume",
            f"{workdir}:/src:ro",

            # Docker image. Must appear exactly once.
            image,

            # Run the actual benchmark command inside the container.
            "sh",
            "-c",
            (
                "mkdir -p /tmp/work "
                "&& cp /src/solution.go /tmp/work/solution.go "
                "&& cp /src/solution_test.go /tmp/work/solution_test.go "
                "&& cp /src/go.mod /tmp/work/go.mod "
                "&& cd /tmp/work "
                "&& go test -mod=mod ./... -count=1"
            ),
        ]

        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )

        except subprocess.TimeoutExpired as exc:
            # Killing the local Docker CLI process does not necessarily stop
            # the running container, so force-remove it explicitly.
            subprocess.run(
                [
                    "docker",
                    "rm",
                    "-f",
                    container_name,
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            return RunResult(
                status=RunStatus.TIMEOUT,
                stdout=_timeout_output(exc.stdout),
                stderr=_timeout_output(exc.stderr),
                duration=time.monotonic() - start,
            )

        duration = time.monotonic() - start

        if completed.returncode == 0:
            status = RunStatus.PASS
        else:
            status = _classify_failed_go_test(
                completed.stdout,
                completed.stderr,
            )

        return RunResult(
            status=status,
            stdout=completed.stdout,
            stderr=completed.stderr,
            duration=duration,
        )
