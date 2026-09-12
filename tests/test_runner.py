from pathlib import Path
from migrate_eval.runner import RunResult, RunStatus


def test_run_status_contains_expected_failure_taxonomy():
    assert [status.value for status in RunStatus] == [
        "PASS",
        "COMPILE_ERROR",
        "TEST_FAIL",
        "TIMEOUT",
        "EXTRACT_ERROR",
        "MODEL_ERROR",
    ]


def test_run_result_stores_execution_information():
    result = RunResult(
        status=RunStatus.PASS,
        stdout="ok",
        stderr="",
        duration=0.42,
    )

    assert result.status is RunStatus.PASS
    assert result.stdout == "ok"
    assert result.stderr == ""
    assert result.duration == 0.42


def test_run_go_tests_passes_valid_go_code():
    from migrate_eval.runner import run_go_tests

    go_code = """package main

func Add(a int, b int) int {
    return a + b
}
"""

    go_test = """package main

import "testing"

func TestAdd(t *testing.T) {
    got := Add(2, 3)

    if got != 5 {
        t.Fatalf("Add(2, 3) = %d; want 5", got)
    }
}
"""

    result = run_go_tests(go_code, go_test)

    assert result.status is RunStatus.PASS
    assert result.duration >= 0


def test_run_go_tests_classifies_failed_assertion_as_test_fail():
    from migrate_eval.runner import run_go_tests

    go_code = """package main

func Add(a int, b int) int {
    return a - b
}
"""

    go_test = """package main

import "testing"

func TestAdd(t *testing.T) {
    got := Add(2, 3)

    if got != 5 {
        t.Fatalf("Add(2, 3) = %d; want 5", got)
    }
}
"""

    result = run_go_tests(go_code, go_test)

    assert result.status is RunStatus.TEST_FAIL
    assert result.duration >= 0


def test_run_go_tests_classifies_invalid_go_as_compile_error():
    from migrate_eval.runner import run_go_tests

    go_code = """package main

func Add(a int, b int) int {
    return a + b
"""

    go_test = """package main

import "testing"

func TestAdd(t *testing.T) {
    got := Add(2, 3)

    if got != 5 {
        t.Fatalf("Add(2, 3) = %d; want 5", got)
    }
}
"""

    result = run_go_tests(go_code, go_test)

    assert result.status is RunStatus.COMPILE_ERROR
    assert result.duration >= 0


def test_run_go_tests_classifies_infinite_loop_as_timeout():
    from migrate_eval.runner import run_go_tests

    go_code = """package main

func Hang() {
    for {
    }
}
"""

    go_test = """package main

import "testing"

func TestHang(t *testing.T) {
    Hang()
}
"""

    result = run_go_tests(
        go_code,
        go_test,
        timeout=15.0,
    )

    assert result.status is RunStatus.TIMEOUT
    assert result.duration >= 15.0


def test_run_go_tests_cleans_up_temporary_directory(monkeypatch):
    import migrate_eval.runner as runner

    original_temporary_directory = runner.tempfile.TemporaryDirectory
    created_directories = []

    def tracking_temporary_directory(*args, **kwargs):
        temporary_directory = original_temporary_directory(*args, **kwargs)
        created_directories.append(Path(temporary_directory.name))
        return temporary_directory

    monkeypatch.setattr(
        runner.tempfile,
        "TemporaryDirectory",
        tracking_temporary_directory,
    )

    go_code = """package main

func Add(a int, b int) int {
    return a + b
}
"""

    go_test = """package main

import "testing"

func TestAdd(t *testing.T) {
    if Add(2, 3) != 5 {
        t.Fatal("unexpected result")
    }
}
"""

    result = runner.run_go_tests(go_code, go_test)

    assert result.status is runner.RunStatus.PASS
    assert len(created_directories) == 1
    assert not created_directories[0].exists()


def test_classify_syntax_error_fixture_as_compile_error():
    from migrate_eval.runner import _classify_failed_go_test

    fixture = Path("tests/fixtures/runner/syntax_error.txt").read_text()

    status = _classify_failed_go_test("", fixture)

    assert status is RunStatus.COMPILE_ERROR


def test_classify_undefined_identifier_fixture_as_compile_error():
    from migrate_eval.runner import _classify_failed_go_test

    fixture = Path("tests/fixtures/runner/undefined_error.txt").read_text()

    status = _classify_failed_go_test(fixture, "")

    assert status is RunStatus.COMPILE_ERROR


def test_classify_failed_test_fixture_as_test_fail():
    from migrate_eval.runner import _classify_failed_go_test

    fixture = Path("tests/fixtures/runner/test_failure.txt").read_text()

    status = _classify_failed_go_test(fixture, "")

    assert status is RunStatus.TEST_FAIL
