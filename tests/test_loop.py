from migrate_eval.dataset import MigrationProblem
from migrate_eval.loop import migrate, migrate_once
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
        self.prompts: list[str] = []

    def complete(self, prompt: str) -> str:
        self.prompts.append(prompt)

        if self.error is not None:
            raise self.error

        return self.response


class SequenceModel:
    name = "sequence-model"

    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.prompts: list[str] = []

    def complete(self, prompt: str) -> str:
        self.prompts.append(prompt)

        if not self.responses:
            raise AssertionError("No fake model response remaining")

        return self.responses.pop(0)


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
    assert attempt.iteration == 0
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
    assert attempt.iteration == 0
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
    assert attempt.iteration == 0
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
    assert attempt.iteration == 0


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
    assert attempt.iteration == 0


def test_migrate_stops_immediately_when_initial_attempt_passes():
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

    runner_calls = 0

    def fake_runner(*, go_code: str, go_test: str) -> RunResult:
        nonlocal runner_calls
        runner_calls += 1

        return RunResult(
            status=RunStatus.PASS,
            stdout="ok",
            stderr="",
            duration=0.1,
        )

    attempts = migrate(
        problem,
        model,
        iters=3,
        runner=fake_runner,
    )

    assert len(attempts) == 1
    assert attempts[0].iteration == 0
    assert attempts[0].run_result.status is RunStatus.PASS
    assert len(model.prompts) == 1
    assert runner_calls == 1


def test_migrate_repairs_failed_code_and_stops_on_pass():
    problem = make_problem()

    model = SequenceModel(
        responses=[
            (
                "```go\n"
                "func Add(a int, b int) int {\n"
                "    return a - b\n"
                "}\n"
                "```"
            ),
            (
                "```go\n"
                "func Add(a int, b int) int {\n"
                "    return a + b\n"
                "}\n"
                "```"
            ),
        ]
    )

    runner_results = [
        RunResult(
            status=RunStatus.TEST_FAIL,
            stdout="expected 5, got -1",
            stderr="",
            duration=0.1,
        ),
        RunResult(
            status=RunStatus.PASS,
            stdout="ok",
            stderr="",
            duration=0.1,
        ),
    ]

    def fake_runner(*, go_code: str, go_test: str) -> RunResult:
        return runner_results.pop(0)

    attempts = migrate(
        problem,
        model,
        iters=3,
        runner=fake_runner,
    )

    assert len(attempts) == 2
    assert [attempt.iteration for attempt in attempts] == [0, 1]

    assert attempts[0].run_result.status is RunStatus.TEST_FAIL
    assert attempts[1].run_result.status is RunStatus.PASS

    assert len(model.prompts) == 2

    repair_prompt = model.prompts[1]

    assert "return a - b" in repair_prompt
    assert "TEST_FAIL" in repair_prompt
    assert "expected 5, got -1" in repair_prompt


def test_migrate_respects_maximum_repair_iterations():
    problem = make_problem()

    response = (
        "```go\n"
        "func Add(a int, b int) int {\n"
        "    return a - b\n"
        "}\n"
        "```"
    )

    model = SequenceModel(
        responses=[
            response,
            response,
            response,
            response,
        ]
    )

    def fake_runner(*, go_code: str, go_test: str) -> RunResult:
        return RunResult(
            status=RunStatus.TEST_FAIL,
            stdout="still failing",
            stderr="",
            duration=0.1,
        )

    attempts = migrate(
        problem,
        model,
        iters=3,
        runner=fake_runner,
    )

    assert len(attempts) == 4

    assert [attempt.iteration for attempt in attempts] == [
        0,
        1,
        2,
        3,
    ]

    assert all(
        attempt.run_result.status is RunStatus.TEST_FAIL
        for attempt in attempts
    )

    assert len(model.prompts) == 4


def test_migrate_with_zero_repairs_matches_single_shot_behavior():
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
            stdout="failed",
            stderr="",
            duration=0.1,
        )

    attempts = migrate(
        problem,
        model,
        iters=0,
        runner=fake_runner,
    )

    assert len(attempts) == 1
    assert attempts[0].iteration == 0
    assert attempts[0].run_result.status is RunStatus.TEST_FAIL
    assert len(model.prompts) == 1


def test_migrate_stops_when_no_go_code_is_available_for_repair():
    problem = make_problem()

    model = FakeModel(
        response="package main",
    )

    runner_called = False

    def fake_runner(*, go_code: str, go_test: str) -> RunResult:
        nonlocal runner_called
        runner_called = True
        raise AssertionError("runner should not be called")

    attempts = migrate(
        problem,
        model,
        iters=3,
        runner=fake_runner,
    )

    assert len(attempts) == 1
    assert attempts[0].run_result.status is RunStatus.EXTRACT_ERROR
    assert attempts[0].go_code is None
    assert len(model.prompts) == 1
    assert runner_called is False


def test_migrate_rejects_negative_iteration_count():
    problem = make_problem()
    model = FakeModel()

    try:
        migrate(
            problem,
            model,
            iters=-1,
        )
    except ValueError as exc:
        assert str(exc) == "iters must be >= 0"
    else:
        raise AssertionError("Expected ValueError")