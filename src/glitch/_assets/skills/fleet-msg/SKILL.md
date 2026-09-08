---
name: fleet-msg
description: Send a message from this session to another desk in the same project, and read the messages waiting for this one. Backed by a file queue at .claude/fleet/, one file per message, so two desks sending at the same moment cannot overwrite each other. Refuses an address that is not in the project's desk table. Use whenever someone runs /fleet-msg, asks to tell another chat something, asks whether anything is waiting, opens a session and should check its mail, or asks how the sessions are supposed to talk to each other.
---

# Fleet messages

## The failure this replaces

Two sessions and one shared notes file. Both open it, both append, the second
write wins, and the first message is gone with nothing anywhere reporting an
error. It is the same bug as two sessions editing one source file, and it has
the same fix: stop editing a shared file.

Every message here is its own file, created exclusively. Two desks sending in
the same second get two files. There is no merge, so there is nothing to lose.

## First: which desk are you?

State it in one line before doing anything else. If it is not obvious from the
task, ask once and then keep using it. Every command below needs it, and a
message sent from the wrong desk is worse than an unsent one, because somebody
will reply to the wrong session.

The desks are in `FLEET.md`. Read the table, do not guess a slug:

```bash
python scripts/fleet.py desks
```

## Check your mail on open

```bash
python scripts/fleet.py inbox --me <your-desk>
```

Act on what is there. Then archive it, so the next check shows only what is new:

```bash
python scripts/fleet.py archive --me <your-desk>
```

Archive **after** acting, not before. A message archived unread is a message
nobody will ever read again.

## Send

```bash
python scripts/fleet.py send --to <desk> --from <your-desk> \
  --subject "one line" --body "what they need to do, and where"
```

Keep the body short and actionable. Say the file, the command, or the decision.
A message that summarises a conversation is a message the other desk has to
interpret.

## Handing work over

Do not use `send` for a handoff. Use `handoff`, which refuses to write one
unless it has all three parts:

```bash
python scripts/fleet.py handoff --from <your-desk> --to <desk> \
  --did "what changed" \
  --verified "the exact command and what it printed, or: not verified" \
  --next "what they should pick up"
```

`--verified` is the part every improvised handoff leaves out, and it is the part
the receiving desk actually needs. "It works" is not a value for it. The command
and its output is.

## An address that is not a desk

`send` refuses a slug that is not in the table, and this is deliberate. If it
created the directory instead, the message would sit in an inbox nobody opens
while the sender believed it had arrived. A refusal costs you five seconds. A
message delivered into a hole costs you the day somebody spends waiting for it.

## Honest limits

- **It cannot wake a closed session.** A message waits until that desk is opened
  and checks. Nothing on your machine can make a closed chat read its mail. Say
  so when you send: the other desk gets it when it next opens.
- **It has no delivery receipt.** You know the file was written. You do not know
  it was read.
- **It does not know whether a handoff is true.** It refuses one that is missing
  its parts. It cannot check that `--verified` describes a command anyone ran.
- **It is not a durable record of decisions.** Messages are for what somebody
  should do next. A decision that has to survive belongs in a file in the repo
  that the next session will read anyway.
