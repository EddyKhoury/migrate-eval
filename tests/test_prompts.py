from migrate_eval.prompts import initial, repair
from migrate_eval.runner import RunResult, RunStatus


def test_initial_prompt_contains_java_code():
    java_code = """
    public static int add(int a, int b) {
        return a + b;
    }
    """

    prompt = initial(
        java_code=java_code,
        go_signature="func Add(a int, b int) int {",
    )

    assert "public static int add" in prompt
    assert "return a + b;" in prompt


def test_initial_prompt_contains_go_signature():
    prompt = initial(
        java_code="public static int add(int a, int b) { return a + b; }",
        go_signature="func Add(a int, b int) int {",
    )

    assert "func Add(a int, b int) int {" in prompt


def test_initial_prompt_instructs_code_only_output():
    prompt = initial(
        java_code="public static int add(int a, int b) { return a + b; }",
        go_signature="func Add(a int, b int) int {",
    )

    assert "Return only one Go code block." in prompt
    assert "Do not include tests." in prompt
    assert "Do not include a main function." in prompt


def test_initial_prompt_requires_package_main():
    prompt = initial(
        java_code="public static int add(int a, int b) { return a + b; }",
        go_signature="func Add(a int, b int) int {",
    )

    assert "Use package main." in prompt


def test_repair_prompt_contains_current_go_code():
    result = RunResult(
        status=RunStatus.COMPILE_ERROR,
        stdout="",
        stderr="undefined: strings",
        duration=0.1,
    )

    go_code = """package main

func Example() string {
    return strings.TrimSpace(" hello ")
}
"""

    prompt = repair(go_code, result)

    assert go_code in prompt


def test_repair_prompt_contains_failure_status_and_output():
    result = RunResult(
        status=RunStatus.TEST_FAIL,
        stdout="expected 5, got 4",
        stderr="",
        duration=0.1,
    )

    prompt = repair("package main\n", result)

    assert "TEST_FAIL" in prompt
    assert "expected 5, got 4" in prompt


def test_repair_prompt_includes_stdout_and_stderr():
    result = RunResult(
        status=RunStatus.COMPILE_ERROR,
        stdout="stdout message",
        stderr="stderr message",
        duration=0.1,
    )

    prompt = repair("package main\n", result)

    assert "STDOUT:" in prompt
    assert "stdout message" in prompt
    assert "STDERR:" in prompt
    assert "stderr message" in prompt


def test_repair_prompt_truncates_long_failure_output():
    output = "\n".join(f"line {i}" for i in range(1, 81))

    result = RunResult(
        status=RunStatus.TEST_FAIL,
        stdout=output,
        stderr="",
        duration=0.1,
    )

    prompt = repair("package main\n", result)

    assert "line 60" in prompt
    assert "line 61" not in prompt
    assert "...[output truncated]..." in prompt


def test_repair_prompt_requires_full_code_only_response():
    result = RunResult(
        status=RunStatus.COMPILE_ERROR,
        stdout="",
        stderr="compile error",
        duration=0.1,
    )

    prompt = repair("package main\n", result)

    assert "complete corrected Go source" in prompt
    assert "exactly one Go code block" in prompt
    assert "Use package main" in prompt
    assert "Do not include tests" in prompt
    assert "Do not include a main function" in prompt
    assert "Do not include explanations" in prompt