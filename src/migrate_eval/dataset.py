"""HumanEval-X dataset loading and canonical Go assembly."""

from __future__ import annotations

import gzip
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class GoImport:
    """One Go import specification."""

    raw: str
    path: str
    selector: str


_IMPORT_RE = re.compile(
    r'^(?:(?P<alias>[A-Za-z_][A-Za-z0-9_]*|[._])\s+)?'
    r'"(?P<path>[^"]+)"$'
)

_IMPORT_BLOCK_RE = re.compile(
    r'(?ms)^\s*import\s*\(\s*.*?^\s*\)\s*'
)

_SINGLE_IMPORT_RE = re.compile(
    r'(?m)^\s*import\s+'
    r'(?:(?:[A-Za-z_][A-Za-z0-9_]*|[._])\s+)?'
    r'"[^"]+"\s*$'
)

_PACKAGE_RE = re.compile(
    r'(?m)^\s*package\s+main\s*$'
)

# HumanEval-X occasionally omits standard-library imports even though the
# canonical Go implementation uses the package. These mappings are used only
# while assembling known canonical benchmark solutions, never to repair
# model-generated code.
_STANDARD_LIBRARY_SELECTORS = {
    "bytes": "bytes",
    "fmt": "fmt",
    "math": "math",
    "rand": "math/rand",
    "regexp": "regexp",
    "sort": "sort",
    "strconv": "strconv",
    "strings": "strings",
    "time": "time",
    "unicode": "unicode",
    "utf8": "unicode/utf8",
    "md5": "crypto/md5",
}

_SCAN_IGNORED_RE = re.compile(
    r'//[^\n]*'
    r'|/\*.*?\*/'
    r'|`.*?`'
    r'|"(?:\\.|[^"\\])*"',
    re.DOTALL,
)


def load_go_problems(path: str | Path) -> list[dict[str, Any]]:
    """Load HumanEval-X Go JSONL.GZ records."""

    path = Path(path)

    with gzip.open(path, "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def _parse_go_imports(import_text: str) -> list[GoImport]:
    """Parse import specifications from Go source text."""

    imports: list[GoImport] = []

    for line in import_text.splitlines():
        stripped = line.strip()

        if not stripped:
            continue

        if stripped in {"import (", "(", ")"}:
            continue

        if stripped.startswith("import "):
            stripped = stripped[len("import "):].strip()

        match = _IMPORT_RE.fullmatch(stripped)

        if match is None:
            continue

        path = match.group("path")
        explicit_alias = match.group("alias")

        if explicit_alias:
            selector = explicit_alias
        else:
            selector = path.rsplit("/", 1)[-1].split(".", 1)[0]

        raw = (
            f'{explicit_alias} "{path}"'
            if explicit_alias
            else f'"{path}"'
        )

        imports.append(
            GoImport(
                raw=raw,
                path=path,
                selector=selector,
            )
        )

    return imports


def _strip_package_and_imports(text: str) -> str:
    """Remove package main and top-level import declarations."""

    text = _PACKAGE_RE.sub("", text, count=1)
    text = _IMPORT_BLOCK_RE.sub("", text, count=1)
    text = _SINGLE_IMPORT_RE.sub("", text, count=1)

    return text.strip()


def _render_go_imports(imports: list[GoImport]) -> str:
    """Render imports as valid Go syntax."""

    if not imports:
        return ""

    if len(imports) == 1:
        return f"import {imports[0].raw}\n"

    lines = ["import ("]

    for item in imports:
        lines.append(f"    {item.raw}")

    lines.append(")")

    return "\n".join(lines) + "\n"


def _scan_code(text: str) -> str:
    """Remove comments and string literals before selector detection."""

    return _SCAN_IGNORED_RE.sub(" ", text)


def _selector_is_used(selector: str, body: str) -> bool:
    """Return whether body references selector.Symbol."""

    if selector in {"_", "."}:
        return True

    return bool(
        re.search(
            rf"\b{re.escape(selector)}\s*\.",
            _scan_code(body),
        )
    )


def _required_imports(
    candidate_texts: list[str],
    body: str,
) -> list[GoImport]:
    """Keep used imports and infer missing standard-library imports."""

    candidates: list[GoImport] = []
    seen_paths: set[str] = set()

    for text in candidate_texts:
        for item in _parse_go_imports(text):
            if item.path in seen_paths:
                continue

            seen_paths.add(item.path)
            candidates.append(item)

    required = [
        item
        for item in candidates
        if _selector_is_used(item.selector, body)
    ]

    required_paths = {
        item.path
        for item in required
    }

    required_selectors = {
        item.selector
        for item in required
    }

    scan_body = _scan_code(body)

    for selector, path in _STANDARD_LIBRARY_SELECTORS.items():
        if selector in required_selectors:
            continue

        if not re.search(
            rf"\b{re.escape(selector)}\s*\.",
            scan_body,
        ):
            continue

        if path in required_paths:
            continue

        required.append(
            GoImport(
                raw=f'"{path}"',
                path=path,
                selector=selector,
            )
        )

        required_paths.add(path)
        required_selectors.add(selector)

    return required


def build_canonical_go_files(
    problem: dict[str, Any],
) -> tuple[str, str]:
    """Build canonical HumanEval-X solution.go and solution_test.go."""

    prompt = problem.get("prompt") or ""
    problem_imports = problem.get("import") or ""
    declaration = problem.get("declaration") or ""
    canonical_solution = problem.get("canonical_solution") or ""
    test_setup = problem.get("test_setup") or ""
    test = problem.get("test") or ""

    # HumanEval-X prompts may contain helper functions required by the target
    # function. Therefore canonical validation must retain the full prompt,
    # not just declaration + canonical_solution.
    if prompt.strip():
        source_scaffold = _strip_package_and_imports(prompt)
    else:
        source_scaffold = declaration.strip()

    source_body = (
        source_scaffold.rstrip()
        + "\n"
        + canonical_solution.lstrip()
    )

    source_imports = _required_imports(
        [problem_imports, prompt],
        source_body,
    )

    source_import_block = _render_go_imports(
        source_imports
    )

    go_code = "package main\n\n"

    if source_import_block:
        go_code += source_import_block + "\n"

    go_code += source_body.rstrip() + "\n"

    test_body_setup = _strip_package_and_imports(
        test_setup
    )

    test_body = (
        test_body_setup.rstrip()
        + "\n"
        + test.lstrip()
    ).strip()

    # Problem imports are also candidates for tests because some HumanEval-X
    # tests use a package that appears only in the problem import field.
    test_imports = _required_imports(
        [test_setup, problem_imports],
        test_body,
    )

    test_import_block = _render_go_imports(
        test_imports
    )

    go_test = "package main\n\n"

    if test_import_block:
        go_test += test_import_block + "\n"

    go_test += test_body.rstrip() + "\n"

    return go_code, go_test
