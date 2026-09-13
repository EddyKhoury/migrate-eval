from migrate_eval.dataset import MigrationProblem
from migrate_eval.loop import migrate_once
from migrate_eval.runner import RunResult, RunStatus


class FakeModel:
    name = "fake-model"

    def __init__(
        self,
        response: str = "",
        error: Exception | None = None,
    ) -> None:
        self.response = response
        self.error = error
        self.prompts = []

    def complete(self, prompt: str) -> str:
        self.prompts.append(prompt)

        if self.error is not None:
            raise self.error

        return self.response


def make_problem() -> MigrationProblem:
    return MigrationProblem(
        task_id="Go/0",
        java_code=(
            "public static int add(int a, int b) {\n"
            "    return a + b;\n"
            "}"
        ),
        go_signature="func Add(a int, b int) int {",
        go_test="package main\n\nfunc TestAdd() {}\n",
    )


def test_migrate_once_runs_complete_single_shot_pipeline():
    problem = make_problem()

    model = FakeModel(
        response=(
            "```go\n"
            "func Add(a int, b int) int {\n"
            "    return a + b\n"
            "}\n"
            "```"
        )
    )

    runner_calls = []

    def fake_runner(*, go_code: str, go_test: str) -> RunResult:
        runner_calls.append(
            {
                "go_code": go_code,
                "go_test": go_test,
            }
        )

        return RunResult(
            status=RunStatus.PASS,
            stdout="ok",
            stderr="",
            duration=0.1,
        )

    attempt = migrate_once(
        problem,
        model,
        runner=fake_runner,
    )

    assert attempt.task_id == "Go/0"
    assert attempt.model_name == "fake-model"
    assert attempt.run_result.status is RunStatus.PASS

    assert len(model.prompts) == 1
    assert problem.java_code in model.prompts[0]
    assert problem.go_signature in model.prompts[0]

    assert runner_calls == [
        {
            "go_code": (
                "package main\n\n"
                "func Add(a int, b int) int {\n"
                "    return a + b\n"
                "}\n"
            ),
            "go_test": problem.go_test,
        }
    ]


def test_migrate_once_returns_model_error_without_running_tests():
    problem = make_problem()

    model = FakeModel(
        error=RuntimeError("model unavailable"),
    )

    runner_called = False

    def fake_runner(*, go_code: str, go_test: str) -> RunResult:
        nonlocal runner_called
        runner_called = True
        raise AssertionError("runner should not be called")

    attempt = migrate_once(
        problem,
        model,
        runner=fake_runner,
    )

    assert attempt.run_result.status is RunStatus.MODEL_ERROR
    assert attempt.go_code is None
    assert attempt.raw_response is None
    assert "model unavailable" in attempt.run_result.stderr
    assert runner_called is False


def test_migrate_once_returns_extract_error_without_running_tests():
    problem = make_problem()

    model = FakeModel(
        response="package main",
    )

    runner_called = False

    def fake_runner(*, go_code: str, go_test: str) -> RunResult:
        nonlocal runner_called
        runner_called = True
        raise AssertionError("runner should not be called")

    attempt = migrate_once(
        problem,
        model,
        runner=fake_runner,
    )

    assert attempt.run_result.status is RunStatus.EXTRACT_ERROR
    assert attempt.go_code is None
    assert attempt.raw_response == "package main"
    assert runner_called is False


def test_migrate_once_preserves_runner_failure_status():
    problem = make_problem()

    model = FakeModel(
        response=(
            "```go\n"
            "func Add(a int, b int) int {\n"
            "    return a - b\n"
            "}\n"
            "```"
        )
    )

    def fake_runner(*, go_code: str, go_test: str) -> RunResult:
        return RunResult(
            status=RunStatus.TEST_FAIL,
            stdout="--- FAIL",
            stderr="",
            duration=0.2,
        )

    attempt = migrate_once(
        problem,
        model,
        runner=fake_runner,
    )

    assert attempt.run_result.status is RunStatus.TEST_FAIL
    assert attempt.run_result.stdout == "--- FAIL"


def test_migrate_once_runs_with_real_go_oracle():
    problem = MigrationProblem(
        task_id="Go/integration",
        java_code=(
            "public static int add(int a, int b) {\n"
            "    return a + b;\n"
            "}"
        ),
        go_signature="func Add(a int, b int) int {",
        go_test=(
            "package main\n\n"
            'import "testing"\n\n'
            "func TestAdd(t *testing.T) {\n"
            "    if Add(2, 3) != 5 {\n"
            '        t.Fatal("unexpected result")\n'
            "    }\n"
            "}\n"
        ),
    )

    model = FakeModel(
        response=(
            "```go\n"
            "func Add(a int, b int) int {\n"
            "    return a + b\n"
            "}\n"
            "```"
        )
    )

    attempt = migrate_once(
        problem,
        model,
    )

    assert attempt.run_result.status is RunStatus.PASS