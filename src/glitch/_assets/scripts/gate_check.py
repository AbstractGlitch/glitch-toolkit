"""Run a verification gate and check whether its green means anything.

Two failures this catches, both observed in the wild:

  1. GREEN WITH NO COUNT. A runner that reported nothing about what it ran, and
     still exited 0. The real instance: a quiet flag passed to an already-quiet
     pytest became -qq, which deletes the summary line. Every wrapper script
     logged a successful run. Forty tests had never executed anywhere.

  2. THE TREE MOVED. The suite ran while edits landed underneath it, so the
     result describes a tree that no longer exists. Re-running is not the fix,
     because the next edit arrives during the re-run prompted by the first.
     This is a scheduling problem, not a tooling one.

    python gate_check.py run --name pytest -- python -m pytest
    python gate_check.py run --name build --watch src -- npm run build

Honest limits:
  * It does not know whether the tests are any good, only whether they ran.
  * Count detection is pattern-based. An unrecognised runner reports UNKNOWN,
    which is a prompt to look, not a failure.
  * mtime is the change signal. A tool that rewrites a file with identical
    content still trips it.
"""
# Lazy annotations, so this file imports on Python 3.9.
#
# The signatures below use `X | None`, which is PEP 604 and needs 3.10. A def's
# annotations are evaluated when the def runs, so without this line the module
# raises TypeError at IMPORT on 3.9 — not at call, which is why it looked fine
# to anyone reading it. CI caught it on the floor version the first time it ran.
#
# This is a shipped artifact: it gets copied into a reader's repository and run
# with THEIR interpreter, which `requires-python` does not govern. So it should
# import as far back as it can rather than as far back as the installer allows.
from __future__ import annotations

import argparse
import os
import pathlib
import re
import subprocess
import sys
import time

IGNORE_DIRS = {
    ".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache",
    ".next", "dist", "build", "coverage", "test-results", ".mypy_cache",
    ".ruff_cache", "playwright-report", ".turbo", ".cache",
}

# Ordered: the first pattern that matches wins.
COUNT_PATTERNS = [
    ("pytest",     re.compile(r"(\d+)\s+passed", re.I)),
    ("pytest",     re.compile(r"collected\s+(\d+)\s+items?", re.I)),
    ("no tests",   re.compile(r"(no tests ran|collected 0 items)", re.I)),
    ("jest/vitest", re.compile(r"Tests:\s+.*?(\d+)\s+passed", re.I)),
    ("playwright", re.compile(r"(\d+)\s+(?:test|spec)s?\s+passed", re.I)),
    ("generic",    re.compile(r"\b(\d+)\s+(?:tests?|specs?|assertions?)\b", re.I)),
    ("go",         re.compile(r"^ok\s+\S+", re.M)),
]


def snapshot(roots: list[str]) -> dict[str, float]:
    out = {}
    for root in roots:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
            for fn in filenames:
                p = os.path.join(dirpath, fn)
                try:
                    out[os.path.normpath(p)] = os.stat(p).st_mtime
                except OSError:
                    pass
    return out


def detect_count(output: str) -> tuple[str, str | None]:
    for label, rx in COUNT_PATTERNS:
        m = rx.search(output)
        if m:
            if label == "no tests":
                return "no tests", "0"
            return label, (m.group(1) if m.groups() else "ok")
    return "UNKNOWN", None


def cmd_run(args) -> int:
    if not args.command:
        raise SystemExit("nothing to run: put the command after --")

    roots = args.watch or ["."]
    print(f"gate: {args.name}")
    print(f"cmd:  {' '.join(args.command)}")
    print(f"watching: {', '.join(roots)}\n")

    before = snapshot(roots)
    t0 = time.time()
    proc = subprocess.run(args.command, capture_output=True, text=True, shell=False)
    elapsed = time.time() - t0
    after = snapshot(roots)

    output = (proc.stdout or "") + "\n" + (proc.stderr or "")
    if not args.quiet:
        tail = output.strip().splitlines()[-15:]
        for line in tail:
            print("  | " + line)
        print()

    verdicts = []

    # 1. exit code
    if proc.returncode != 0:
        verdicts.append(("FAIL", f"exit code {proc.returncode}"))
    else:
        verdicts.append(("ok", "exit code 0"))

    # 2. did it report what it ran
    runner, count = detect_count(output)
    if runner == "UNKNOWN":
        verdicts.append(("WARN", "no test count found in output. Green, but it did not say what it ran."))
    elif runner == "no tests" or count == "0":
        verdicts.append(("FAIL", "the runner reported that it ran zero tests"))
    else:
        verdicts.append(("ok", f"{runner} reported {count}"))

    # 3. did the tree move underneath it
    changed = [p for p, m in after.items() if before.get(p) != m]
    new = [p for p in after if p not in before]
    moved = sorted(set(changed) | set(new))
    if moved:
        verdicts.append(("FAIL", f"{len(moved)} file(s) changed while the gate ran"))
    else:
        verdicts.append(("ok", "tree held still for the whole run"))

    print(f"ran in {elapsed:.1f}s\n")
    print("verdict:")
    worst = 0
    for level, msg in verdicts:
        print(f"  [{level:4}] {msg}")
        worst = max(worst, {"ok": 0, "WARN": 1, "FAIL": 2}[level])

    if moved:
        print("\n  files that changed during the run:")
        for p in moved[:12]:
            print(f"    {os.path.relpath(p)}")
        if len(moved) > 12:
            print(f"    ... and {len(moved) - 12} more")
        print("\n  This result certifies a tree that no longer exists. Re-running is")
        print("  not the fix if edits are still landing. Stop the writers first.")

    if worst == 0:
        print("\nGATE: trustworthy green")
        return 0
    if worst == 1:
        print("\nGATE: green, but unproven. Look before you rely on it.")
        return 0 if args.warn_ok else 1
    print("\nGATE: not trustworthy")
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="run a gate and judge its result")
    r.add_argument("--name", default="gate")
    r.add_argument("--watch", action="append", help="directory to watch for edits (repeatable)")
    r.add_argument("--quiet", action="store_true", help="do not echo the command output")
    r.add_argument("--warn-ok", action="store_true", help="exit 0 on warnings")
    r.add_argument("command", nargs=argparse.REMAINDER)
    r.set_defaults(fn=cmd_run)

    args = ap.parse_args()
    if getattr(args, "command", None) and args.command and args.command[0] == "--":
        args.command = args.command[1:]
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
