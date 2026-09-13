INITIAL_PROMPT_TEMPLATE = """You are migrating a function from Java to Go.

Convert the Java implementation below into Go.

Requirements:
- Implement exactly the provided Go function signature.
- Preserve the behavior of the Java implementation.
- Return only one Go code block.
- Do not include tests.
- Do not include a main function.
- Do not include explanations.
- Use package main.

Java implementation:

```java
{java_code}
```

Required Go function signature:

```go
{go_signature}
```
"""


def initial(java_code: str, go_signature: str) -> str:
    """Build the initial Java-to-Go migration prompt."""

    return INITIAL_PROMPT_TEMPLATE.format(
        java_code=java_code.strip(),
        go_signature=go_signature.strip(),
    )