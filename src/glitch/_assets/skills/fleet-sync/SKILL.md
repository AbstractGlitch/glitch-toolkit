---
name: fleet-sync
description: The protocol every session in a multi-desk project runs, so opening, working, handing off and closing look the same at every desk instead of each one improvising. Covers identifying which desk you are, reading only the current state rather than the whole history, doing the work under the project's rules, writing back before going idle, and handing off in a shape the next desk can act on. Use whenever someone runs /fleet-sync, a session opens in a project with a FLEET.md, a session is about to go idle or be compacted, work needs handing between desks, or someone asks how the sessions should coordinate.
---

# Fleet sync

One protocol, run identically by every desk. The point is not ceremony. It is
that a session which opens next week, or a compacted version of this one, can
pick the work up from the repository alone.

## 1. Identify

Say which desk you are, in one line, before anything else.

```bash
python scripts/fleet.py desks
```

If the task does not make it obvious, ask once. Everything below depends on it.

## 2. On open, read the current state and stop

Read what is true now. Do not read the history.

- the project's rules file, `CLAUDE.md`
- whatever file holds the current picture, and only the recent part of it
- your inbox: `python scripts/fleet.py inbox --me <your-desk>`

The archive of everything that ever happened is for the day you need it. Reading
it every session is what makes a session slow, and a slow session is one that
starts making the mistakes this protocol exists to prevent. **Read the delta,
not the history.**

## 3. Do the work

Under the project's rules, not your recollection of them. If the change touches
something a gate covers, run the gate and read what it printed.

## 4. Write back before you go idle

Two things, in this order:

1. **The repository.** A decision that lives only in this conversation did not
   happen. Anything the next session must know goes in a file it will open
   anyway. Append; do not rewrite somebody else's entry.
2. **The handoff**, in the fixed shape:

```bash
python scripts/fleet.py handoff --from <your-desk> --to <desk> \
  --did "what changed" \
  --verified "the exact command and what it printed, or: not verified" \
  --next "what they should pick up"
```

`fleet.py` refuses a handoff missing any of the three, because the missing one
is always `--verified`, and that is the one the next desk needs in order to know
what is actually done.

## 5. Route through the desk that owns it

Send to the desk that owns the thing, which is what the `owns` column in
`FLEET.md` is for. If nobody owns it, that is the finding: say so rather than
sending it to whoever is open.

## 6. One desk commits

`FLEET.md` names it and `fleet.py desks` refuses a table that names none or two.
If you are not that desk, finish, verify, hand off, and stop. Do not push.

Every other mistake a fleet makes is recoverable by reading a file and writing
it again. Two desks pushing over each other in one checkout is not, and it
happens on the day everyone is moving fastest.

## 7. Compact early

When a session starts re-reading files it already read this session, or its
turns start stacking up, checkpoint with step 4 and then compact. Compacting
summarises the conversation and keeps the thread; it is not a restart, and it
does not touch the files. Do it at a task boundary, before the session feels
heavy, never after it stops responding.

Because step 4 is done, nothing is lost either way.

## Honest limits

- **This standardises behaviour, not delivery.** It cannot wake a closed
  session, and it cannot make another desk read its inbox.
- **It cannot tell whether a write-back is accurate.** It only makes the absence
  of one visible.
- **It does not decide who owns what.** That is `FLEET.md`, and it is a decision
  somebody has to make rather than a thing a tool can infer.
- **A protocol is not a gate.** Nothing here prevents a desk from skipping a
  step. What it does is remove the excuse that the shape was unclear.
