"""Does the read-only server stay read-only, and does it write the record down?

    python tests/test_mcp_server.py          # needs the [mcp] extra

Skips cleanly when the SDK is absent, because the base package does not depend
on it and a suite that fails for a missing optional dependency trains people to
ignore red.

Two cases carry this file. WRITES_NOTHING drives every tool against a repository
and then compares the whole tree, byte for byte, against a snapshot taken
first — the ledger being the single permitted exception, named explicitly rather
than filtered by a pattern that could quietly grow. And REFUSAL_IS_RECORDED
checks the case a record is easiest to lose: not the answer that worked, but the
one where the server said no.

The last test starts the real console script as a subprocess and speaks the real
protocol to it, because everything above it imports Python objects and would
pass just as happily if the thing were unable to serve at all.
"""
import asyncio
import hashlib
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

try:
    import mcp.types as types  # noqa: F401
    from mcp import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client
except ImportError:
    print("skip  the MCP SDK is not installed; run: pip install 'abstractglitch-toolkit[mcp]'")
    sys.exit(0)

from glitch import cli, mcp_server  # noqa: E402
from glitch.ledger import Ledger  # noqa: E402

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


def snapshot(root, ignore):
    """Every file under root, with a hash, except the paths named."""
    out = {}
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        if rel in ignore or any(rel.startswith(i.rstrip("/") + "/") for i in ignore):
            continue
        out[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def install_into(repo):
    """Use the real install command, so the fixture is a real installation."""
    import subprocess

    subprocess.run(
        [sys.executable, str(pathlib.Path(cli.__file__)), "--repo", str(repo), "install"],
        capture_output=True,
        check=True,
        timeout=120,
    )


with tempfile.TemporaryDirectory() as tmp:
    root = pathlib.Path(tmp)

    def every_tool_says_read_only():
        tools = mcp_server.describe_tools()
        assert len(tools) == 3, [t.name for t in tools]
        for t in tools:
            assert t.annotations is not None, t.name + " has no annotations"
            assert t.annotations.read_only_hint is True, t.name + " is not marked read-only"
            assert t.annotations.destructive_hint is False, t.name + " is not marked non-destructive"
            assert t.input_schema.get("additionalProperties") is False, (
                t.name + " accepts arguments it does not declare"
            )

    check("every tool is declared read-only and non-destructive", every_tool_says_read_only)

    repo = root / "repo"
    repo.mkdir()
    install_into(repo)
    ledger_path = repo / ".claude/toolkit/ledger/ledger.jsonl"
    tools = mcp_server.GlitchTools(repo, Ledger(ledger_path))

    def status_reports_all_six():
        out = tools.status()
        assert len(out["steps"]) == 6, out
        assert out["total"] == 6, out
        # A freshly installed repo has done two of the six; the other four are
        # the reader's own files. If this ever reads 6, install started lying.
        assert out["passing"] == 2, "expected 2 passing after a bare install: {}".format(out)
        for s in out["steps"]:
            if s["installed_and_refusing"]:
                assert s["first_failure"] is None, s
        assert out["ledger"]["written"] is True, out["ledger"]

    check("status reports six steps and two passing after a bare install", status_reports_all_six)

    def check_issues_receipts_only_for_passes():
        out = tools.check()
        assert len(out["results"]) == 6, out
        assert out["all_passed"] is False, "a bare install passed every step"
        for r in out["results"]:
            if r["passed"]:
                assert r["receipt"] and r["receipt"].startswith("GLITCH-RECEIPT "), r
            else:
                assert r["receipt"] is None, "a failing step was issued a receipt: {}".format(r)

    check("check issues a receipt for a pass and null for a failure",
          check_issues_receipts_only_for_passes)

    def one_step_can_be_checked():
        out = tools.check("gates")
        assert len(out["results"]) == 1 and out["results"][0]["id"] == "gates", out
        assert out["all_passed"] is True, out

    check("a single step can be checked by id", one_step_can_be_checked)

    # The record is easiest to lose exactly where it is most wanted.
    def refusal_is_recorded():
        before, _ = tools.ledger.read()
        out = tools.check("nonsense")
        assert "error" in out and "nonsense" in out["error"], out
        assert sorted(out["steps"]) == sorted(s.id for s in cli.STEPS), out
        after, _ = tools.ledger.read()
        assert len(after) == len(before) + 1, "the refusal was not written down"
        last = after[-1]
        assert last["outcome"] == "refused", last
        assert last["detail"]["requested"] == "nonsense", last

    check("an unknown step is refused, and the refusal is in the ledger", refusal_is_recorded)

    def ledger_tail_reports_supersession_without_applying_it():
        first = tools.ledger.append("check", "fail", step="floor")
        tools.ledger.supersede(first["id"], "check", "pass", step="floor")
        out = tools.ledger_tail(limit=200)
        ids = [r["id"] for r in out["records"]]
        assert first["id"] in ids, "a superseded record was hidden from the tail"
        got = [r for r in out["records"] if r["id"] == first["id"]][0]
        assert got["is_superseded"] is True, got
        assert got["outcome"] == "fail", "the superseded record was rewritten"
        assert out["unreadable_lines"] == 0, out

    check("the tail shows a superseded record and says so",
          ledger_tail_reports_supersession_without_applying_it)

    # The one that would make this server a liability rather than a product.
    def writes_nothing_but_the_ledger():
        clean = root / "clean"
        clean.mkdir()
        install_into(clean)
        led = clean / ".claude/toolkit/ledger/ledger.jsonl"
        ignore = {led.relative_to(clean).as_posix()}

        before = snapshot(clean, ignore)
        assert before, "the fixture repository is empty; this test would prove nothing"

        t = mcp_server.GlitchTools(clean, Ledger(led))
        t.status()
        t.check()
        t.check("gates")
        t.check("no-such-step")
        t.ledger_tail()

        after = snapshot(clean, ignore)
        changed = [k for k in before if before[k] != after.get(k)]
        added = [k for k in after if k not in before]
        removed = [k for k in before if k not in after]
        assert not changed, "the server modified: {}".format(changed)
        assert not added, "the server created: {}".format(added)
        assert not removed, "the server deleted: {}".format(removed)
        assert led.is_file(), "the ledger, the one permitted write, was not written"

    check("running every tool changes nothing in the repository but the ledger",
          writes_nothing_but_the_ledger)

    def no_ledger_writes_nothing_at_all():
        quiet = root / "quiet"
        quiet.mkdir()
        install_into(quiet)
        before = snapshot(quiet, set())

        t = mcp_server.GlitchTools(quiet, None)
        out = t.status()
        assert out["ledger"]["written"] is False, out["ledger"]
        assert "no-ledger" in out["ledger"]["reason"], out["ledger"]
        tail = t.ledger_tail()
        assert tail["records"] == [] and "error" in tail, tail

        after = snapshot(quiet, set())
        assert before == after, "--no-ledger still wrote something"

    check("--no-ledger answers questions and writes nothing anywhere",
          no_ledger_writes_nothing_at_all)

    def an_unknown_tool_is_a_keyerror_not_a_guess():
        try:
            tools.dispatch("glitch_delete_everything", {})
            raise AssertionError("an unknown tool name was dispatched")
        except KeyError:
            pass

    check("an unknown tool name is refused rather than guessed at",
          an_unknown_tool_is_a_keyerror_not_a_guess)

    # Everything above imports Python objects. This starts the real script and
    # speaks the real protocol, because a server that cannot serve would pass
    # every test above it.
    def it_actually_serves_over_stdio():
        served = root / "served"
        served.mkdir()
        install_into(served)

        async def talk():
            params = StdioServerParameters(
                command=sys.executable,
                args=["-m", "glitch.mcp_server", "--repo", str(served)],
                env=None,
            )
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    listed = await session.list_tools()
                    names = sorted(t.name for t in listed.tools)
                    result = await session.call_tool("glitch_check", {"step": "gates"})
                    return names, result

        names, result = asyncio.run(asyncio.wait_for(talk(), timeout=120))
        assert names == ["glitch_check", "glitch_ledger_tail", "glitch_status"], names
        assert not result.is_error, result
        body = result.content[0].text
        assert "GLITCH-RECEIPT" in body, body
        assert (served / ".claude/toolkit/ledger/ledger.jsonl").is_file(), (
            "a real session left no record"
        )

    check("the console script serves tools over stdio and records the call",
          it_actually_serves_over_stdio)


print("")
print("{} passed, {} failed".format(passed, failed))

if passed == 0:
    print("nothing ran. that is a failure, not a pass.")
    sys.exit(1)
sys.exit(1 if failed else 0)
