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


def load_go_problems(path: str | Path) -> list[dict[str, Any]]:
    """Load HumanEval-X Go JSONL.GZ records."""

    path = Path(path)

    with gzip.open(path, "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def _parse_go_imports(import_text: str) -> list[GoImport]:
    """Parse import specifications from a HumanEval-X Go import block."""

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
            # Standard Go imports normally use the final path component as
            # their selector. Splitting on "." also handles paths such as
            # gopkg.in/yaml.v3 -> yaml for our simple benchmark use case.
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


def _render_go_imports(imports: list[GoImport]) -> str:
    """Render Go imports as a valid import declaration."""

    if not imports:
        return ""

    if len(imports) == 1:
        return f"import {imports[0].raw}\n"

    lines = ["import ("]

    for item in imports:
        lines.append(f"    {item.raw}")

    lines.append(")")

    return "\n".join(lines) + "\n"


def _missing_test_imports(
    problem_imports: str,
    test_setup: str,
    test: str,
) -> list[GoImport]:
    """Find problem imports referenced by tests but absent from test_setup."""

    available = _parse_go_imports(problem_imports)
    existing = _parse_go_imports(test_setup)

    existing_paths = {
        item.path
        for item in existing
    }

    needed: list[GoImport] = []

    for item in available:
        if item.path in existing_paths:
            continue

        # Normal Go package usage is selector.Symbol.
        # Blank and dot imports are not needed by the current benchmark
        # assembly rule and are therefore not automatically copied.
        if item.selector in {"_", "."}:
            continue

        selector_used = re.search(
            rf"\b{re.escape(item.selector)}\s*\.",
            test,
        )

        if selector_used:
            needed.append(item)

    return needed


def build_canonical_go_files(
    problem: dict[str, Any],
) -> tuple[str, str]:
    """Build solution.go and solution_test.go for a canonical Go problem."""

    problem_imports = problem.get("import") or ""
    declaration = problem.get("declaration") or ""
    canonical_solution = problem.get("canonical_solution") or ""
    test_setup = problem.get("test_setup") or ""
    test = problem.get("test") or ""

    go_code = (
        "package main\n\n"
        + problem_imports
        + declaration
        + canonical_solution
    )

    extra_test_imports = _missing_test_imports(
        problem_imports,
        test_setup,
        test,
    )

    rendered_extra_imports = _render_go_imports(
        extra_test_imports
    )

    go_test = (
        test_setup
        + "\n"
        + rendered_extra_imports
        + test
    )

    return go_code, go_test
