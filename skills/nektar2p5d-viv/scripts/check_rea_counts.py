#!/usr/bin/env python3
import re
import sys
from pathlib import Path

COUNT_LINE_RE = re.compile(r"^\s*(\d+)\s+.*\b[Ll]ines?\b.*\bfollow\b")
PARAM_RE = re.compile(r"^\s*(\d+)\s+PARAMETERS\s+FOLLOW\b", re.IGNORECASE)
PASSIVE_SCALAR_SENTINEL = re.compile(r"Lines of passive scalar data follows", re.IGNORECASE)


def check_parameter_block(lines):
    issues = []
    for i, line in enumerate(lines):
        m = PARAM_RE.search(line)
        if not m:
            continue
        expected = int(m.group(1))
        actual = 0
        j = i + 1
        while j < len(lines):
            if PASSIVE_SCALAR_SENTINEL.search(lines[j]):
                break
            if lines[j].strip():
                actual += 1
            j += 1
        if j == len(lines):
            issues.append((i + 1, f"PARAMETERS FOLLOW found, but end sentinel not found"))
        if actual != expected:
            issues.append((i + 1, f"PARAMETERS FOLLOW mismatch: expected {expected}, found {actual}"))
    return issues


def check_generic_count_blocks(lines):
    issues = []
    checks = []
    for i, line in enumerate(lines):
        m = COUNT_LINE_RE.search(line)
        if not m:
            continue
        expected = int(m.group(1))
        start = i + 1
        end = start + expected
        if end > len(lines):
            issues.append((i + 1, f"line-count block overflow: expected {expected} lines after header"))
            continue
        # Record checks for reporting
        checks.append((i + 1, expected, line.strip()))
    return issues, checks


def main():
    if len(sys.argv) != 2:
        print("Usage: check_rea_counts.py <file.rea>")
        return 2

    p = Path(sys.argv[1])
    if not p.exists():
        print(f"ERROR: file not found: {p}")
        return 2

    lines = p.read_text(errors="ignore").splitlines()

    issues = []
    issues.extend(check_parameter_block(lines))
    generic_issues, checks = check_generic_count_blocks(lines)
    issues.extend(generic_issues)

    print(f"File: {p}")
    print(f"Detected count-headers: {len(checks)}")
    if checks:
        print("Count-headers (line: expected):")
        for ln, exp, raw in checks:
            print(f"  L{ln}: {exp} :: {raw}")

    if issues:
        print("\nMISMATCHES:")
        for ln, msg in issues:
            print(f"  L{ln}: {msg}")
        return 1

    print("\nOK: no count mismatch detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
