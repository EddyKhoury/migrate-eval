from migrate_eval.dataset import (
    build_canonical_go_files,
    build_migration_problems,
)


def make_problem(test: str) -> dict[str, str]:
    return {
        "prompt": (
            'import (\n'
            '    "math"\n'
            ')\n\n'
            'func Example(x float64) float64 {\n'
        ),
        "import": 'import (\n    "math"\n)\n',
        "declaration": "\nfunc Example(x float64) float64 {\n",
        "canonical_solution": "    return math.Abs(x)\n}\n",
        "test_setup": (
            'package main\n\n'
            'import (\n'
            '    "testing"\n'
            ')\n'
        ),
        "test": test,
    }


def test_canonical_solution_receives_used_problem_import():
    problem = make_problem(
        "func TestExample(t *testing.T) {}\n"
    )

    go_code, _ = build_canonical_go_files(problem)

    assert '"math"' in go_code
    assert "func Example" in go_code


def test_test_receives_problem_import_when_used():
    problem = make_problem(
        """
func TestExample(t *testing.T) {
    _ = math.Abs(1.0)
}
"""
    )

    _, go_test = build_canonical_go_files(problem)

    assert '"math"' in go_test


def test_test_does_not_receive_unused_problem_import():
    problem = make_problem(
        """
func TestExample(t *testing.T) {
    _ = Example(1.0)
}
"""
    )

    _, go_test = build_canonical_go_files(problem)

    assert '"math"' not in go_test


def test_test_does_not_duplicate_existing_import():
    problem = make_problem(
        """
func TestExample(t *testing.T) {
    _ = math.Abs(1.0)
}
"""
    )

    problem["test_setup"] = (
        'package main\n\n'
        'import (\n'
        '    "testing"\n'
        '    "math"\n'
        ')\n'
    )

    _, go_test = build_canonical_go_files(problem)

    assert go_test.count('"math"') == 1


def test_prompt_helper_function_is_preserved():
    problem = make_problem(
        "func TestExample(t *testing.T) {}\n"
    )

    problem["prompt"] = """
func Helper(x float64) float64 {
    return x * 2
}

func Example(x float64) float64 {
"""

    problem["import"] = ""
    problem["canonical_solution"] = (
        "    return Helper(x)\n"
        "}\n"
    )

    go_code, _ = build_canonical_go_files(problem)

    assert "func Helper" in go_code
    assert "return Helper(x)" in go_code


def test_missing_strings_import_is_inferred():
    problem = make_problem(
        "func TestExample(t *testing.T) {}\n"
    )

    problem["prompt"] = (
        "func ExampleText(value string) []string {\n"
    )
    problem["import"] = ""
    problem["canonical_solution"] = (
        '    return strings.Split(value, " ")\n'
        '}\n'
    )

    go_code, _ = build_canonical_go_files(problem)

    assert '"strings"' in go_code


def test_unused_source_import_is_removed():
    problem = make_problem(
        "func TestExample(t *testing.T) {}\n"
    )

    problem["canonical_solution"] = (
        "    return x\n"
        "}\n"
    )

    go_code, _ = build_canonical_go_files(problem)

    assert '"math"' not in go_code


def test_unused_test_import_is_removed():
    problem = make_problem(
        """
func TestExample(t *testing.T) {
    _ = Example(1.0)
}
"""
    )

    problem["test_setup"] = (
        'package main\n\n'
        'import (\n'
        '    "testing"\n'
        '    "crypto/md5"\n'
        ')\n'
    )

    _, go_test = build_canonical_go_files(problem)

    assert '"testing"' in go_test
    assert '"crypto/md5"' not in go_test

def test_build_migration_problems_pairs_java_and_go_by_task_index():
    java_problems = [
        {
            "task_id": "Java/1",
            "prompt": "JAVA ONE START\n",
            "canonical_solution": "JAVA ONE END",
        },
        {
            "task_id": "Java/0",
            "prompt": "JAVA ZERO START\n",
            "canonical_solution": "JAVA ZERO END",
        },
    ]

    go_problems = [
        {
            "task_id": "Go/0",
            "prompt": "",
            "import": "",
            "declaration": "func Zero() int {",
            "canonical_solution": "",
            "test_setup": "package main\n",
            "test": "func TestZero() {}\n",
        },
        {
            "task_id": "Go/1",
            "prompt": "",
            "import": "",
            "declaration": "func One() int {",
            "canonical_solution": "",
            "test_setup": "package main\n",
            "test": "func TestOne() {}\n",
        },
    ]

    problems = build_migration_problems(
        java_problems,
        go_problems,
    )

    assert [problem.task_id for problem in problems] == [
        "Go/0",
        "Go/1",
    ]


def test_build_migration_problem_contains_required_migration_data():
    java_problems = [
        {
            "task_id": "Java/0",
            "prompt": "JAVA PROMPT\n",
            "canonical_solution": "JAVA SOLUTION",
        }
    ]

    go_problems = [
        {
            "task_id": "Go/0",
            "prompt": "",
            "import": "",
            "declaration": "func Example() int {",
            "canonical_solution": "",
            "test_setup": "package main\n",
            "test": "func TestExample() {}\n",
        }
    ]

    problems = build_migration_problems(
        java_problems,
        go_problems,
    )

    problem = problems[0]

    assert problem.task_id == "Go/0"
    assert problem.java_code == "JAVA PROMPT\nJAVA SOLUTION"
    assert problem.go_signature == "func Example() int {"
    assert "package main" in problem.go_test
    assert "func TestExample()" in problem.go_test


def test_build_migration_problems_excludes_requested_tasks():
    java_problems = [
        {
            "task_id": "Java/95",
            "prompt": "JAVA",
            "canonical_solution": "SOLUTION",
        }
    ]

    go_problems = [
        {
            "task_id": "Go/95",
            "prompt": "",
            "import": "",
            "declaration": "func Example() bool {",
            "canonical_solution": "",
            "test_setup": "package main\n",
            "test": "func TestExample() {}\n",
        }
    ]

    problems = build_migration_problems(
        java_problems,
        go_problems,
        excluded_task_ids={"Go/95"},
    )

    assert problems == []


def test_build_migration_problems_rejects_mismatched_task_sets():
    java_problems = [
        {
            "task_id": "Java/0",
            "prompt": "JAVA",
            "canonical_solution": "SOLUTION",
        }
    ]

    go_problems = [
        {
            "task_id": "Go/1",
            "prompt": "",
            "import": "",
            "declaration": "func Example() int {",
            "canonical_solution": "",
            "test_setup": "package main\n",
            "test": "func TestExample() {}\n",
        }
    ]

    try:
        build_migration_problems(
            java_problems,
            go_problems,
        )
    except ValueError as exc:
        assert str(exc) == (
            "Java and Go HumanEval-X task sets do not match"
        )
    else:
        raise AssertionError("Expected ValueError")
