"""A fleet of chats that can address each other, and a handoff with a fixed shape.

    python fleet.py desks                          who exists, who commits
    python fleet.py inbox --me build               your unread messages
    python fleet.py send --to build --from ops --subject "..."     body on stdin
    python fleet.py handoff --from build --to ops --did "..." --verified "..." --next "..."
    python fleet.py archive --me build             mark what you read as read

Two problems, and they are the same problem twice.

  1. ONE SHARED FILE. Every desk writes its messages into one notes file, two
     desks write at once, and the second write wins silently. That is chapter
     four again, and the fix is the same: never edit a shared file. One file
     per message, created exclusively, so a collision is impossible rather than
     unlikely.

  2. AN IMPROVISED HANDOFF. Every chat invents its own way of saying it is
     done, so the next desk gets a paragraph and has to guess what was actually
     verified. `handoff` refuses to write one without all three parts: what was
     done, what was actually run, and what is next.

An address that is not a desk is refused. A message sent to a slug nobody
watches is not delivered anywhere; it sits in a directory no one opens, and the
sender believes it arrived. So the desk table is the authority, and sending to
an unknown desk is an error rather than a new directory.

WHAT THIS CANNOT DO:

  * It cannot wake a closed session. A message waits in the inbox until that
    desk opens and checks. Nothing on your machine can make a closed chat read
    its mail, and any tool that claims otherwise is describing a scheduler.
  * It does not know whether a desk did what it said in a handoff. It only
    refuses a handoff that does not say.
  * It is not a queue with delivery guarantees. It is files in directories,
    which is why it survives every session being closed at once.

Standard library only. Everything it writes stays under `.claude/fleet/`.
"""
import argparse
import errno
import os
import pathlib
import re
import sys
import time

START = "<!-- desks:start -->"
END = "<!-- desks:end -->"
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*$")
YES = {"yes", "y", "true"}
NO = {"no", "n", "false", "-", ""}


class Desk:
    def __init__(self, slug, owns, commits):
        self.slug = slug
        self.owns = owns
        self.commits = commits


def read_desks(path):
    """Parse the desk table. Returns (desks, error)."""
    if not path.is_file():
        return [], (
            "no desk table at {}. A fleet with no written table is a fleet where\n"
            "  every desk believes it is allowed to commit.".format(path)
        )

    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    start = end = None
    for i, line in enumerate(lines):
        if START in line and start is None:
            start = i
        elif END in line and start is not None and end is None:
            end = i
    if start is None or end is None:
        return [], "{} has no {} ... {} block".format(path, START, END)

    desks = []
    for line in lines[start + 1:end]:
        row = line.strip()
        if not row.startswith("|"):
            continue
        cells = [c.strip() for c in row.strip("|").split("|")]
        if len(cells) < 3:
            continue
        slug = cells[0].lower()
        if slug in ("desk", "") or set(slug) <= set("-: "):
            continue  # the header row and the separator under it
        desks.append(Desk(slug, cells[1], cells[2].strip().lower()))
    return desks, None


def judge_desks(desks):
    """Return a list of complaints about the table itself."""
    out = []
    if len(desks) < 2:
        out.append("a fleet needs at least two desks. Found {}.".format(len(desks)))

    seen = set()
    for d in desks:
        if not SLUG.match(d.slug):
            out.append("'{}' is not a usable address. Lower case, digits and hyphens.".format(d.slug))
        if d.slug in seen:
            out.append("'{}' is listed twice. Two desks with one address share an inbox.".format(d.slug))
        seen.add(d.slug)
        if d.commits not in YES and d.commits not in NO:
            out.append("'{}' answers '{}' to commits. Say yes or no.".format(d.slug, d.commits))

    committers = [d.slug for d in desks if d.commits in YES]
    if not committers:
        out.append(
            "nobody is allowed to commit. Decide who is, and write it in the table.\n"
            "  Every other mistake a fleet makes is recoverable. This one is the one\n"
            "  where two desks push over each other."
        )
    elif len(committers) > 1:
        out.append(
            "{} desks are allowed to commit: {}. Pick one.".format(
                len(committers), ", ".join(committers))
        )
    return out


def bus_root(fleet_path):
    return fleet_path.resolve().parent / ".claude" / "fleet"


def resolve(args):
    """Load and validate the table, or explain why not. Returns (desks, root, error)."""
    path = pathlib.Path(args.fleet)
    desks, error = read_desks(path)
    if error:
        return None, None, error
    complaints = judge_desks(desks)
    if complaints:
        return None, None, "\n".join("  " + c for c in complaints)
    return desks, bus_root(path), None


def require(desks, slug, what):
    known = [d.slug for d in desks]
    if slug in known:
        return None
    return (
        "'{}' is not a desk, so there is nowhere to {}.\n"
        "  Desks: {}\n"
        "  A message to an address nobody watches is worse than no message: the\n"
        "  sender believes it arrived.".format(slug, what, ", ".join(known))
    )


def write_message(root, to, body):
    """One file per message, created exclusively. Two senders cannot collide."""
    box = root / to / "inbox"
    box.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%S")
    for n in range(1000):
        target = box / "{}-{}-{}.md".format(stamp, os.getpid(), n)
        try:
            fd = os.open(str(target), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except OSError as e:
            if e.errno == errno.EEXIST:
                continue
            raise
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(body)
        return target
    raise RuntimeError("could not create a message file in " + str(box))


def envelope(sender, to, subject, body):
    return "From: {}\nTo: {}\nTime: {}\nSubject: {}\n\n{}\n".format(
        sender, to, time.strftime("%Y-%m-%d %H:%M"), subject, body.rstrip("\n"))


# ------------------------------------------------------------------ commands


def cmd_desks(args):
    path = pathlib.Path(args.fleet)
    desks, error = read_desks(path)
    if error:
        print(error)
        return 1
    complaints = judge_desks(desks)

    print("")
    print("  {:<16} {:<40} {}".format("desk", "owns", "commits"))
    for d in desks:
        print("  {:<16} {:<40} {}".format(d.slug, d.owns[:40], d.commits or "-"))
    print("")

    if complaints:
        for c in complaints:
            print("  FAIL  " + c)
        print("")
        return 1
    print("  the table holds: {} desks, one of them commits.".format(len(desks)))
    print("")
    return 0


def cmd_send(args):
    desks, root, error = resolve(args)
    if error:
        print(error)
        return 1
    for slug, what in ((args.to, "deliver"), (getattr(args, "from"), "send from")):
        bad = require(desks, slug, what)
        if bad:
            print(bad)
            return 1

    body = args.body if args.body is not None else sys.stdin.read()
    if not body.strip():
        print("empty message. Say the thing, or do not send it.")
        return 1

    target = write_message(root, args.to, envelope(getattr(args, "from"), args.to, args.subject, body))
    print("sent to {}: {}".format(args.to, target))
    print("They see it when that session next opens and checks. Nothing here wakes it.")
    return 0


def cmd_handoff(args):
    desks, root, error = resolve(args)
    if error:
        print(error)
        return 1
    for slug, what in ((args.to, "deliver"), (getattr(args, "from"), "send from")):
        bad = require(desks, slug, what)
        if bad:
            print(bad)
            return 1

    missing = [name for name in ("did", "verified", "next") if not getattr(args, name).strip()]
    if missing:
        print("a handoff without {} is not a handoff.".format(" or ".join(missing)))
        print("The next desk cannot tell what is done from what was intended.")
        print("  --did       what changed")
        print("  --verified  the exact command you ran and what it said, or 'not verified'")
        print("  --next      what the next desk should pick up")
        return 1

    body = "Done:\n  {}\n\nVerified:\n  {}\n\nNext:\n  {}\n".format(
        args.did.strip(), args.verified.strip(), args.next.strip())
    target = write_message(
        root, args.to, envelope(getattr(args, "from"), args.to, "handoff: " + args.did.strip()[:60], body))
    print("handed off to {}: {}".format(args.to, target))
    return 0


def cmd_inbox(args):
    desks, root, error = resolve(args)
    if error:
        print(error)
        return 1
    bad = require(desks, args.me, "read an inbox")
    if bad:
        print(bad)
        return 1

    box = root / args.me / "inbox"
    files = sorted(box.glob("*.md")) if box.is_dir() else []
    if not files:
        print("no unread messages for {}.".format(args.me))
        return 0
    for f in files:
        print("=" * 70)
        print(f.name)
        print("=" * 70)
        print(f.read_text(encoding="utf-8", errors="replace"))
    print("{} message(s). Act on them, then: python fleet.py archive --me {}".format(
        len(files), args.me))
    return 0


def cmd_archive(args):
    desks, root, error = resolve(args)
    if error:
        print(error)
        return 1
    bad = require(desks, args.me, "archive an inbox")
    if bad:
        print(bad)
        return 1

    box = root / args.me / "inbox"
    done = root / args.me / "read"
    files = sorted(box.glob("*.md")) if box.is_dir() else []
    if not files:
        print("nothing to archive for {}.".format(args.me))
        return 0
    done.mkdir(parents=True, exist_ok=True)
    for f in files:
        f.replace(done / f.name)
    print("archived {} message(s) for {}.".format(len(files), args.me))
    return 0


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--fleet", default="FLEET.md", help="the desk table (default: FLEET.md)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("desks", help="print the desk table and check it")

    s = sub.add_parser("send", help="send a message to a desk")
    s.add_argument("--to", required=True)
    s.add_argument("--from", required=True)
    s.add_argument("--subject", required=True)
    s.add_argument("--body", help="message body (default: read stdin)")

    h = sub.add_parser("handoff", help="hand work to another desk, in the fixed shape")
    h.add_argument("--to", required=True)
    h.add_argument("--from", required=True)
    h.add_argument("--did", default="")
    h.add_argument("--verified", default="")
    h.add_argument("--next", default="")

    i = sub.add_parser("inbox", help="read your unread messages")
    i.add_argument("--me", required=True)

    a = sub.add_parser("archive", help="move what you read out of the inbox")
    a.add_argument("--me", required=True)

    args = ap.parse_args()
    return {
        "desks": cmd_desks,
        "send": cmd_send,
        "handoff": cmd_handoff,
        "inbox": cmd_inbox,
        "archive": cmd_archive,
    }[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
