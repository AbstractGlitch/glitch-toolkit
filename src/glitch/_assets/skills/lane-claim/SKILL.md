---
name: lane-claim
description: Claim files before editing them when more than one Claude session shares a working tree, and check whether anyone else is already in a file. Prevents the silent overwrite where two sessions edit the same file, the second write wins, there is no merge conflict and no error, and the lost work reads as a completed task. Use whenever someone runs /lane-claim, before editing files in a repo that several sessions or agents share, when asked who is working on what, when work seems to have vanished or reverted for no reason, or when starting a session in a tree that other sessions are also using.
---

# Lane claims

## The failure this prevents

Several Claude sessions in one working tree overwrite each other. There is **no merge conflict and no
error**, because each session reads, edits, and writes a whole file in a window of seconds. The second
write silently wins.

The damage is not the lost edit. It is that the session whose work was destroyed reports the task as
complete, and it was complete, for about ninety seconds. Nobody notices until someone goes looking for
a feature that is not there.

## Before you edit anything

```bash
python scripts/check_lanes.py check <paths...> --lane <your-lane>
```

Exit 0 means clear. Exit 1 means one of two things:

- **Claimed by another lane.** Do not edit. Route the work to that lane, or ask its operator to
  release. Forcing past a live claim recreates the exact bug.
- **Recently modified.** Nobody claimed it, but someone touched it in the last thirty minutes. This
  catches the session that never claims anything, which is most of them. Treat it as a question, not
  a verdict: check whether that edit was yours.

## Claiming

```bash
python scripts/check_lanes.py claim <lane> <paths...> --note "what you are doing"
```

Claims are one file per lane under `.claude/lanes/`, so two sessions writing claims at the same
moment never touch the same file. A single shared claims file would race, which is the bug this
exists to prevent, one level up.

Globs are expanded at claim time so a claim names real files rather than a pattern that will mean
something different tomorrow.

## Releasing, and why it matters as much as claiming

```bash
python scripts/check_lanes.py release <lane>
```

**Release when you finish the increment, not when you close the session.** A stale claim is not
harmlessly cautious. It makes every other lane route around files that are actually free, and the
cost of that compounds quietly: work gets deferred, then re-planned, then done somewhere worse.

`status` flags any claim older than four hours. If you see one of yours, either release it or refresh
it. Both are fine. Leaving it is not.

## What this cannot do

State it to the user rather than letting them assume otherwise:

- **It cannot see other sessions.** It sees claims they wrote and mtimes on disk. A session that
  never claims anything is invisible to the claim layer, which is why the mtime check exists.
- **mtime evidence is advisory.** A recent mtime means someone touched the file. It does not mean
  they are still in it, and an untouched file does not mean nobody is about to write it.
- **It locks nothing.** There is no enforcement. It informs; the operator decides.
- **It does not help across machines.** Claims are files in the repo. If they are not committed or
  shared, another machine sees none of them.

The honest summary: this converts an invisible failure into a visible warning. It does not make the
failure impossible.

## When the answer is a worktree instead

If two lanes genuinely need to build at the same time, claims are not enough. Build tooling takes
process-level locks, so a second `npm run build` in the same checkout fails outright no matter who
claimed what. Give one lane its own git worktree instead.
