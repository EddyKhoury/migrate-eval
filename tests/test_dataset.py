from migrate_eval.dataset import build_canonical_go_files


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
