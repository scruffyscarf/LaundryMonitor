#!/usr/bin/env python3
"""Fail CI if any function has cyclomatic complexity above threshold."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", default="backend/src", help="Path to analyze")
    parser.add_argument(
        "--max-complexity",
        type=int,
        default=8,
        help="Maximum allowed cyclomatic complexity",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    target = Path(args.path)

    if not target.exists():
        print(f"ERROR: path not found: {target}", file=sys.stderr)
        return 2

    cmd = ["radon", "cc", str(target), "-j"]
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True)

    if proc.returncode != 0:
        print("ERROR: radon failed", file=sys.stderr)
        if proc.stdout:
            print(proc.stdout, file=sys.stderr)
        if proc.stderr:
            print(proc.stderr, file=sys.stderr)
        return proc.returncode

    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        print(f"ERROR: failed to parse radon output: {exc}", file=sys.stderr)
        return 2

    violations: list[tuple[str, str, int, int]] = []

    for file_path, blocks in payload.items():
        for block in blocks:
            complexity = int(block.get("complexity", 0))
            if complexity > args.max_complexity:
                violations.append(
                    (
                        file_path,
                        block.get("name", "<unknown>"),
                        int(block.get("lineno", 0)),
                        complexity,
                    )
                )

    if violations:
        print(
            f"Complexity gate failed: found {len(violations)} function(s) "
            f"with complexity > {args.max_complexity}."
        )
        for file_path, name, lineno, complexity in violations:
            print(f" - {file_path}:{lineno} `{name}` complexity={complexity}")
        return 1

    print(
        "Complexity gate passed: all analyzed functions have "
        f"complexity <= {args.max_complexity}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
