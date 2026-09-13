import re


class ExtractionError(ValueError):
    """Raised when no usable Go code can be extracted from a model response."""


_GO_FENCE_PATTERN = re.compile(
    r"```go\s*(.*?)```",
    flags=re.IGNORECASE | re.DOTALL,
)

_PACKAGE_LINE_PATTERN = re.compile(
    r"^\s*package\s+\w+\s*$",
    flags=re.MULTILINE,
)


def go_block(response: str, package_name: str = "main") -> str:
    """Extract Go source code from a model response.

    If Go fenced blocks exist, the last one is used.
    Otherwise, the entire response is treated as Go source.

    Any package declaration supplied by the model is removed and replaced
    with the package required by the evaluation harness.
    """

    fenced_blocks = _GO_FENCE_PATTERN.findall(response)

    if fenced_blocks:
        code = fenced_blocks[-1]
    else:
        code = response

    code = _PACKAGE_LINE_PATTERN.sub("", code).strip()

    if not code:
        raise ExtractionError("model response contained no usable Go code")

    return f"package {package_name}\n\n{code}\n"