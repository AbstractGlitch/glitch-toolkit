"""An append-only record of what was asked and what was answered.

This is the part that is meant to outlive the tool. A check that runs and prints
is gone the moment the terminal scrolls; a check that runs and is written down
is still evidence a year later, when somebody asks what this agent was allowed
to do and what it actually did.

Four rules, taken from the diagnostic rule registry in `codex/` because they
were already argued there and they were right:

  * Append only. Nothing in this file rewrites a line it did not just write.
  * Supersession, never deletion. A later record can say it replaces an earlier
    one, and both stay. `supersede()` is the only way to do it, and it writes a
    new record rather than touching the old.
  * Missing data is not zero. A field that was not measured is `null`, never 0
    and never an empty string, so a reader can tell "we looked and found none"
    from "we never looked".
  * Confidence is a word with a reason, never a number nobody computed.

Standard library only, and no import of anything MCP. The ledger is the durable
part of this product and it is not allowed to depend on the transport that
happens to be writing into it today.

Concurrency, stated rather than assumed. Records are appended in "a" mode as a
single line each, which POSIX makes atomic for writes below the pipe buffer, so
two writers interleave records but never corrupt one. There is no lock and no
sequence counter: the file's own order is the order, and identity is a random
id rather than a position, precisely so that two writers cannot disagree about
whose record is number seven.
"""
import datetime
import json
import os
import pathlib
import uuid

LEDGER_VERSION = 1

# Where the record goes when nobody says otherwise. Beside the artifacts rather
# than at the repository root, because it is machine-written and a reader should
# not have to wonder whether they are supposed to edit it. They are not.
DEFAULT_RELATIVE_PATH = ".claude/toolkit/ledger/ledger.jsonl"

# A line longer than this is refused rather than written. The cap exists because
# a tool argument can be arbitrarily large and a ledger that can be filled by one
# call is a ledger that can be used to hide the record above it.
MAX_RECORD_BYTES = 64 * 1024


class LedgerError(Exception):
    """A record could not be written. Never raised for a record that WAS written."""


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class Ledger:
    """An append-only JSONL file.

    Construct it with the path to the file, not to the repository. `for_repo`
    is the convenience that knows the default location.
    """

    def __init__(self, path):
        self.path = pathlib.Path(path)

    @classmethod
    def for_repo(cls, repo, path=None):
        repo = pathlib.Path(repo).resolve()
        return cls(pathlib.Path(path) if path else repo / DEFAULT_RELATIVE_PATH)

    def append(self, event, outcome, supersedes=None, **fields):
        """Write one record and return it.

        `event` is what happened, `outcome` is how it came out. Both are
        required and neither is allowed to be empty, because a record that says
        only that something occurred is not evidence of anything.

        Anything else is passed through in `detail`. A value of None survives as
        null: see the note about missing data above.
        """
        if not event or not outcome:
            raise LedgerError("a record needs both an event and an outcome")

        record = {
            "v": LEDGER_VERSION,
            "id": uuid.uuid4().hex[:16],
            "at": _now(),
            "event": str(event),
            "outcome": str(outcome),
            "supersedes": supersedes,
            "detail": fields or {},
        }

        try:
            line = json.dumps(record, ensure_ascii=False, sort_keys=True, default=str)
        except (TypeError, ValueError) as e:
            raise LedgerError("record is not serialisable: {}".format(e))

        encoded = (line + "\n").encode("utf-8")
        if len(encoded) > MAX_RECORD_BYTES:
            raise LedgerError(
                "record is {} bytes, over the {} byte cap".format(
                    len(encoded), MAX_RECORD_BYTES
                )
            )

        self.path.parent.mkdir(parents=True, exist_ok=True)
        # "ab" and one write() call. Not "w", not a read-modify-write, and not a
        # temp file replaced over the top: each of those can lose records that
        # were already durable, which is the one thing this file must never do.
        with open(self.path, "ab") as fh:
            fh.write(encoded)
            fh.flush()
            os.fsync(fh.fileno())
        return record

    def supersede(self, record_id, event, outcome, **fields):
        """Record that an earlier record has been overtaken.

        The earlier record is not touched, not marked, and not removed. Reading
        the ledger and applying supersession is the reader's job, which is what
        keeps the file itself honest.
        """
        if not record_id:
            raise LedgerError("supersede needs the id of the record it replaces")
        return self.append(event, outcome, supersedes=record_id, **fields)

    def read(self, limit=None):
        """Return records oldest first, skipping any line that will not parse.

        A partial last line is the normal shape of a process killed mid-write.
        It is skipped and counted, never repaired in place: repairing it would
        mean rewriting the file, and this class does not do that.
        """
        if not self.path.exists():
            return [], 0

        records, unreadable = [], 0
        with open(self.path, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except ValueError:
                    unreadable += 1
                    continue
                if isinstance(obj, dict):
                    records.append(obj)
                else:
                    unreadable += 1

        if limit is not None:
            records = records[-limit:]
        return records, unreadable

    def superseded_ids(self):
        """Every id that some later record claims to replace."""
        records, _ = self.read()
        return set(r.get("supersedes") for r in records if r.get("supersedes"))
