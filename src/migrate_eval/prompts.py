from migrate_eval.runner import RunResult


INITIAL_PROMPT_TEMPLATE = """You are migrating a Java implementation to Go.

Java implementation:

```java
{java_code}
```

Implement exactly this Go function signature:

```go
{go_signature}
```

Requirements:
- Preserve the behavior of the Java implementation.
- Implement exactly the supplied Go function signature.
- Use package main.
- Return only one Go code block.
- Do not include tests.
- Do not include a main function.
- Do not include explanations or commentary outside the Go code block.
"""


REPAIR_OUTPUT_MAX_LINES = 60


def initial(java_code: str, go_signature: str) -> str:
    return INITIAL_PROMPT_TEMPLATE.format(
        java_code=java_code,
        go_signature=go_signature,
    )


def _repair_feedback(run_result: RunResult) -> str:
    sections: list[tuple[str, list[str]]] = []

    if run_result.stdout.strip():
        sections.append(
            (
                "STDOUT",
                run_result.stdout.strip().splitlines(),
            )
        )

    if run_result.stderr.strip():
        sections.append(
            (
                "STDERR",
                run_result.stderr.strip().splitlines(),
            )
        )

    if not sections:
        return "(no compiler or test output was captured)"

    remaining = REPAIR_OUTPUT_MAX_LINES
    rendered: list[str] = []
    truncated = False

    for index, (label, lines) in enumerate(sections):
        if remaining == 0:
            truncated = True
            break

        rendered.append(f"{label}:")

        line_count = min(len(lines), remaining)
        rendered.extend(lines[:line_count])
        remaining -= line_count

        if line_count < len(lines):
            truncated = True
            break

        if remaining == 0 and index < len(sections) - 1:
            truncated = True
            break

    if truncated:
        rendered.append("...[output truncated]...")

    return "\n".join(rendered)


def repair(go_code: str, run_result: RunResult) -> str:
    feedback = _repair_feedback(run_result)

    return f"""You are repairing a Go implementation that failed its target-language validation.

Current Go implementation:

```go
{go_code}
```

Validation status:

{run_result.status.value}

Compiler/test output:

```text
{feedback}
```

Fix the Go implementation so that it passes the existing tests.

Requirements:
- Preserve the intended behavior and existing required function signatures.
- Return the complete corrected Go source, not a patch or partial snippet.
- Return exactly one Go code block.
- Use package main.
- Do not include tests.
- Do not include a main function.
- Do not include explanations or commentary outside the Go code block.
"""