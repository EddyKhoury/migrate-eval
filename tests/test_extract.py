import pytest

from migrate_eval.extract import ExtractionError, go_block


def test_extracts_single_go_fenced_block():
    response = """
Here is the migration:

```go
func Add(a int, b int) int {
    return a + b
}
```
"""

    result = go_block(response)

    assert result == (
        "package main\n\n"
        "func Add(a int, b int) int {\n"
        "    return a + b\n"
        "}\n"
    )


def test_uses_last_go_fenced_block():
    response = """
```go
func Add(a int, b int) int {
    return a - b
}
```

Correction:

```go
func Add(a int, b int) int {
    return a + b
}
```
"""

    result = go_block(response)

    assert "return a + b" in result
    assert "return a - b" not in result


def test_uses_whole_response_when_no_go_fence_exists():
    response = """
func Add(a int, b int) int {
    return a + b
}
"""

    result = go_block(response)

    assert "func Add(a int, b int) int {" in result
    assert "return a + b" in result


def test_replaces_existing_package_declaration():
    response = """
```go
package generated

func Add(a int, b int) int {
    return a + b
}
```
"""

    result = go_block(response)

    assert result.startswith("package main\n")
    assert "package generated" not in result


def test_does_not_duplicate_package_main():
    response = """
package main

func Add(a int, b int) int {
    return a + b
}
"""

    result = go_block(response)

    assert result.count("package main") == 1


def test_supports_custom_package_name():
    response = """
func Add(a int, b int) int {
    return a + b
}
"""

    result = go_block(response, package_name="migration")

    assert result.startswith("package migration\n")


def test_empty_response_raises_extraction_error():
    with pytest.raises(ExtractionError):
        go_block("")


def test_package_only_response_raises_extraction_error():
    with pytest.raises(ExtractionError):
        go_block("package main")