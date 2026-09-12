from migrate_eval.dataset import build_canonical_go_files


def make_problem(test: str) -> dict[str, str]:
    return {
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


def test_canonical_solution_receives_problem_imports():
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

    assert 'import "math"' in go_test


def test_test_does_not_receive_unused_problem_import():
    problem = make_problem(
        """
func TestExample(t *testing.T) {
    _ = Example(1.0)
}
"""
    )

    _, go_test = build_canonical_go_files(problem)

    assert 'import "math"' not in go_test


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
