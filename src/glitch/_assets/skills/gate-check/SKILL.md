---
name: gate-check
description: Run a test suite, build, or lint gate and judge whether its green result actually means anything. Catches a runner that exited 0 without reporting what it ran, a suite that ran zero tests, and a gate that certified a working tree which changed underneath it while it ran. Use whenever someone runs /gate-check, before trusting a passing test run, when asked to verify a change is safe, when a suite went green but the feature is still broken, when tests pass suspiciously fast, or before declaring an increment complete.
---

# Gate check

## Why a green run is not evidence

A gate reports two things and you only ever read one of them. It reports pass or fail, and it
reports what it covered. The second one is the one that lies.

Three real instances, all in the harness and none in the product:

- A quiet flag passed to an already-quiet test runner became `-qq`, which deletes the summary line.
  Every wrapper script logged a successful run with no test count. Forty tests had never executed
  anywhere, six of them on the security boundary.
- A "closing regression" ran a narrower selection than CI did, and passed on the part that had not
  changed.
- A suite ran while three edits landed underneath it. The green described a tree that no longer
  existed.

## Running a gate

```bash
python scripts/gate_check.py run --name pytest --watch backend -- python -m pytest
python scripts/gate_check.py run --name build --watch frontend/src -- npm run build
```

Everything after `--` is the command. `--watch` is the directory whose files must hold still; repeat
it for more than one. It reports three verdicts:

| Verdict | Means |
|---|---|
| exit code | The only thing most people check. Necessary, not sufficient. |
| reported count | Did the runner say what it ran? `UNKNOWN` is a warning, not a pass. Zero is a failure. |
| tree held still | Did any watched file change between start and finish? |

Exit 0 only when all three are clean. `--warn-ok` downgrades the count warning if your runner is
genuinely silent by design, but set that deliberately and never as a reflex.

## Reading the result

**"no test count found in output"** does not mean the tests failed. It means the run proved nothing.
Go and look at what it ran. This is the single most common way a suite reports success for work it
never touched.

**"N file(s) changed while the gate ran"** voids the result. Re-running is not the fix. If edits are
still landing, the next edit will arrive during the re-run prompted by the first, and you will chase
that loop for as long as you are willing to. Stop the writers, then run the gate. This is a
scheduling problem, not a tooling one.

## The check this does not do

**It does not tell you whether the gate covers your change.** A suite can run two hundred tests,
report all of them, hold the tree still, and touch none of the code you edited. Compare the gate's
scope against your diff yourself:

```bash
git diff --name-only HEAD
```

If nothing in that list is exercised by what ran, the green is real and irrelevant.

## Other limits

- Count detection is pattern-based across pytest, jest, vitest, playwright, and go. An unrecognised
  runner reports `UNKNOWN`, which is a prompt to look rather than a verdict.
- mtime is the change signal, so a tool that rewrites a file with identical bytes still trips it.
  Add noisy output directories to `IGNORE_DIRS` or narrow `--watch`.
- It says nothing about whether the tests are any good. It only says whether they ran.

## Before declaring an increment complete

Run the gate through this, and record the exact command, the exit code, and the reported count. A
result nobody wrote down is a result nobody can check. Never report a suite as passing unless it was
actually executed and you read what it said.
