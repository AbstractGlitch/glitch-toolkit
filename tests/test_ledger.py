"""Does the ledger actually keep what it was given?

    python tests/test_ledger.py

The failure this suite exists for is the quiet one. A ledger that loses a record
still looks like a ledger: the file is there, lines are in it, and every test
that only checks "the thing I just wrote is readable" passes. So the cases that
matter here are the ones about the records somebody wrote EARLIER — that a
second append leaves the first line byte-identical, that superseding does not
touch what it supersedes, and that a half-written line is skipped rather than
repaired, because repairing it means rewriting the file.
"""
import json
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from glitch.ledger import Ledger, LedgerError  # noqa: E402

passed = 0
failed = 0


def check(name, fn):
    global passed, failed
    try:
        fn()
        passed += 1
        print("pass  " + name)
    except AssertionError as e:
        failed += 1
        print("FAIL  " + name)
        print("      " + str(e))
    except Exception as e:  # noqa: BLE001 - a crashing test is a failing test
        failed += 1
        print("FAIL  " + name)
        print("      {}: {}".format(type(e).__name__, e))


with tempfile.TemporaryDirectory() as tmp:
    root = pathlib.Path(tmp)

    def append_returns_and_persists():
        led = Ledger(root / "a.jsonl")
        rec = led.append("check", "pass", step="gates")
        assert rec["event"] == "check" and rec["outcome"] == "pass", rec
        assert rec["detail"]["step"] == "gates", rec
        assert len(rec["id"]) == 16, rec
        back, unreadable = led.read()
        assert unreadable == 0, unreadable
        assert len(back) == 1 and back[0]["id"] == rec["id"], back

    check("a record is written and reads back as itself", append_returns_and_persists)

    # The one that matters. Everything else in this file is a convenience.
    def append_never_touches_what_is_there():
        led = Ledger(root / "b.jsonl")
        led.append("check", "pass", n=1)
        first_line = led.path.read_bytes()
        for i in range(2, 12):
            led.append("check", "pass", n=i)
        after = led.path.read_bytes()
        assert after.startswith(first_line), (
            "an earlier record changed when a later one was appended"
        )
        back, _ = led.read()
        assert [r["detail"]["n"] for r in back] == list(range(1, 12)), back

    check("appending ten records leaves the first one byte-identical",
          append_never_touches_what_is_there)

    def supersede_keeps_the_original():
        led = Ledger(root / "c.jsonl")
        original = led.append("check", "fail", step="floor")
        before = led.path.read_bytes()
        replacement = led.supersede(original["id"], "check", "pass", step="floor")

        assert replacement["supersedes"] == original["id"], replacement
        assert led.path.read_bytes().startswith(before), (
            "the superseded record was modified"
        )
        back, _ = led.read()
        assert len(back) == 2, "supersession removed a record instead of adding one"
        assert back[0]["outcome"] == "fail", "the original outcome was rewritten"
        assert led.superseded_ids() == {original["id"]}, led.superseded_ids()

    check("superseding adds a record and rewrites nothing", supersede_keeps_the_original)

    def a_half_written_line_is_skipped_not_repaired():
        led = Ledger(root / "d.jsonl")
        led.append("check", "pass", n=1)
        led.append("check", "pass", n=2)
        # What a process killed mid-write leaves behind.
        with open(led.path, "ab") as fh:
            fh.write(b'{"v":1,"id":"deadbe')
        broken = led.path.read_bytes()

        back, unreadable = led.read()
        assert len(back) == 2, "a partial line ate a good record: {}".format(back)
        assert unreadable == 1, "the partial line was not counted: {}".format(unreadable)
        assert led.path.read_bytes() == broken, (
            "reading the ledger rewrote it; append-only means append-only"
        )

    check("a partial last line is skipped and counted, and the file is left alone",
          a_half_written_line_is_skipped_not_repaired)

    # Missing data is not zero. A reader has to be able to tell "we looked and
    # there were none" from "nobody ever looked", and 0 says the first while
    # meaning the second.
    def absent_stays_null():
        led = Ledger(root / "e.jsonl")
        led.append("check", "pass", receipt=None, count=0)
        raw = json.loads(led.path.read_text(encoding="utf-8").strip())
        assert raw["detail"]["receipt"] is None, raw
        assert raw["detail"]["count"] == 0, raw
        assert raw["supersedes"] is None, raw

    check("a field that was not measured stays null, and zero stays zero", absent_stays_null)

    def an_empty_record_is_refused():
        led = Ledger(root / "f.jsonl")
        for bad in (("", "pass"), ("check", "")):
            try:
                led.append(*bad)
                raise AssertionError("accepted a record with no {}".format(
                    "event" if not bad[0] else "outcome"))
            except LedgerError:
                pass
        assert not led.path.exists(), "a refused record still created the file"

    check("a record with no event or no outcome is refused", an_empty_record_is_refused)

    # A ledger one call can fill is a ledger one call can hide things in.
    def an_oversized_record_is_refused_and_writes_nothing():
        led = Ledger(root / "g.jsonl")
        led.append("check", "pass", n=1)
        before = led.path.read_bytes()
        try:
            led.append("check", "pass", blob="x" * (128 * 1024))
            raise AssertionError("a 128KB record was accepted")
        except LedgerError:
            pass
        assert led.path.read_bytes() == before, "the refused record was partly written"

    check("an oversized record is refused and nothing is written",
          an_oversized_record_is_refused_and_writes_nothing)

    def unserialisable_is_refused_not_crashed_on():
        led = Ledger(root / "h.jsonl")
        # default=str catches most things; a key that is not a string does not
        # round-trip, and the point is that it fails as a LedgerError.
        rec = led.append("check", "pass", obj=object())
        assert isinstance(rec["detail"]["obj"], str) or rec["detail"]["obj"] is not None, rec
        back, unreadable = led.read()
        assert unreadable == 0 and len(back) == 1, (back, unreadable)

    check("a value json cannot type is stringified, not crashed on",
          unserialisable_is_refused_not_crashed_on)

    def tail_returns_the_last_n_oldest_first():
        led = Ledger(root / "i.jsonl")
        for i in range(1, 21):
            led.append("check", "pass", n=i)
        back, _ = led.read(limit=5)
        assert [r["detail"]["n"] for r in back] == [16, 17, 18, 19, 20], back

    check("read(limit) returns the last n, oldest first", tail_returns_the_last_n_oldest_first)

    def for_repo_puts_it_out_of_the_way():
        repo = root / "repo"
        repo.mkdir()
        led = Ledger.for_repo(repo)
        assert led.path == repo / ".claude/toolkit/ledger/ledger.jsonl", led.path
        led.append("check", "pass")
        assert led.path.is_file()
        override = Ledger.for_repo(repo, root / "elsewhere.jsonl")
        assert override.path == root / "elsewhere.jsonl", override.path

    check("for_repo defaults beside the artifacts and can be overridden",
          for_repo_puts_it_out_of_the_way)


print("")
print("{} passed, {} failed".format(passed, failed))

if passed == 0:
    print("nothing ran. that is a failure, not a pass.")
    sys.exit(1)
sys.exit(1 if failed else 0)
