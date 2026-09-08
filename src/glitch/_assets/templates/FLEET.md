# FLEET.md

Who exists, what each one owns, and which single desk is allowed to commit.

Start with two desks. Not five. A fleet is worth having at the point where one
session cannot hold the whole job in its head, and that point arrives with the
second desk, not the fifth. Two desks that each own something beat five that all
own everything.

The table below is the address book. `fleet.py` reads it, and it refuses to send
to a slug that is not in it, because a message to an address nobody watches is
worse than no message: the sender believes it arrived.

<!-- desks:start -->
| desk | owns | commits |
| --- | --- | --- |
| orchestrator | the branch, the release, and what ships | yes |
| build | the application code and its tests | no |
<!-- desks:end -->

## The one rule that is not recoverable

Exactly one desk commits. `fleet.py desks` refuses a table with none and a table
with two, and that refusal is not pedantry. Every other mistake a fleet makes
can be undone by reading a file and writing it again. Two desks pushing over
each other in one checkout cannot, and it will happen on the day you are moving
fastest.

The other desks finish their work, run their gate, and hand off. They do not
push.

## Opening a session

```
python fleet.py inbox --me build
```

Read it, do it, then archive it so the next check shows only new mail:

```
python fleet.py archive --me build
```

## Closing a session

Never close on a paragraph. Hand off in the shape, so the next desk can tell
what is done from what was intended:

```
python fleet.py handoff --from build --to orchestrator \
  --did "..." \
  --verified "the exact command and what it printed, or: not verified" \
  --next "..."
```

`--verified` is the one people leave out, which is the one the next desk needs.
`fleet.py` will not write the handoff without it.

## Adding a desk

Add a row. Give it something to own that no other desk owns. If you cannot write
what it owns in one line without overlapping another desk, you do not need the
desk, you need the existing one to be clearer about its job.

## What this does not do

Nothing here wakes a closed session. A message waits in the inbox until that
desk opens and checks its mail. Any arrangement that appears to deliver in real
time is really two people sitting at two open windows.
