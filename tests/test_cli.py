"""Does the Build Path checker actually check anything?

    python tests/test_cli.py

The failure this suite exists for is the one the checker itself is about. A
check that only looks for files on disk passes the moment the reader copies an
artifact into place, whether or not the artifact works, and whether or not it
has any teeth left. It would be green for every reader, forever, and it would
mean nothing.

So the case that matters here is not "an installed artifact passes", which
anyone would write. It is SABOTAGE below: the artifacts are present, they run,
they exit 0, and they refuse nothing. A checker worth selling has to fail that,
and this suite is the only thing standing between shipping one that does not.

It builds a throwaway repo in the system temp directory, installs the real
artifacts into it, and drives the real CLI as a subprocess. Nothing here
reimplements the checker's logic, because a second copy of the logic would agree
with the first copy about everything including its bugs.
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
PACKAGE = HERE.parent / "src" / "glitch"
# The CLI is driven as a subprocess, by file path, exactly as a reader running a
# bare copy would. Nothing here imports it, so the suite proves the same thing
# about the installed console script and about the single copied file.
GLITCH = PACKAGE / "cli.py"
TOOLKIT = PACKAGE / "_assets"

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


def glitch(repo, *args):
    p = subprocess.run(
        [sys.executable, str(GLITCH), "--repo", str(repo)] + list(args),
        capture_output=True,
        text=True,
        timeout=300,
    )
    return p.returncode, p.stdout + p.stderr


SCRIPTS = ("check_lanes.py", "gate_check.py", "rules_check.py", "fleet.py", "token_audit.py",
           "plan_check.py")
SKILLS = ("lane-claim", "gate-check", "fleet-msg", "fleet-sync")


def install(repo):
    """Put the real artifacts where a reader would put them, and do the work.

    Four of the six steps are checked against the reader's own files rather
    than against ours, because for those four the file IS the work: a rules
    file that holds, a desk table with one committer, a floor measured twice, a
    plan somebody else approved. A fixture that only copied our scripts in would
    fail those four correctly and prove nothing about anything else.

    FLOOR.md and PLAN.md are written here rather than copied from the templates,
    because both templates deliberately do not pass. See
    floor_template_does_not_pass and plan_template_does_not_pass.
    """
    (repo / ".claude/toolkit/scripts").mkdir(parents=True, exist_ok=True)
    (repo / ".claude/skills").mkdir(parents=True, exist_ok=True)
    for name in SCRIPTS:
        shutil.copy(TOOLKIT / "scripts" / name, repo / ".claude/toolkit/scripts" / name)
    for name in SKILLS:
        shutil.copytree(TOOLKIT / "skills" / name, repo / ".claude/skills" / name)
    shutil.copy(TOOLKIT / "templates" / "CLAUDE.ecom.md", repo / "CLAUDE.md")
    shutil.copy(TOOLKIT / "templates" / "FLEET.md", repo / "FLEET.md")
    (repo / "FLOOR.md").write_text(
        "2026-01-14  floor 31,400 tokens  (before)\n"
        "2026-01-16  floor 19,050 tokens  (after cutting two hooks)\n",
        encoding="utf-8",
    )
    (repo / "PLAN.md").write_text(PLAN, encoding="utf-8")


# A plan that answers what a plan has to answer: two people, two dates, a scope
# list with more than one line in it, and verification written so it could come
# back no. Deliberately about something other than this toolkit, because it
# stands in for a stranger's plan rather than describing our own.
PLAN = """## Plan: move the receipt store off the volume

**Written** 2026-01-14 by Dana
**Approved** 2026-01-15 by Sam
**Stages** 2

### What we are NOT doing

- Touching the checkout route. The money path is not in this round.
- Migrating the accounts store. Parked rather than cancelled.
- Adding a second writer. The single writer assumption stays.

### What we ARE doing

- Write the reader behind a flag, reading from both stores.
- Backfill, then flip the flag.

### How we will know it worked

- The dual read suite runs against a copy of the live store and reports a count.
- A receipt written before the flip is still readable after it, proved by a case
  that reads one back.

<!-- deviations:start -->
<!-- deviations:end -->
"""


# One short circuit per artifact, each chosen to leave it running and exiting 0
# while removing its ability to refuse. The injected line differs because the
# functions differ; what they have in common is that nothing errors.
# The two below are narrower than SABOTAGE and that is the point of them.
#
# SABOTAGE guts a whole function: the artifact runs, exits 0 and refuses nothing
# at all. Real drift does not look like that. It looks like an artifact that
# still refuses nine things and has quietly stopped refusing the tenth, which
# the total lobotomy above cannot distinguish from a healthy one. Both entries
# here remove exactly one ability and leave everything else working.
#
# Both are failures observed on 8 September 2026 in this repository.
PARTIAL_SABOTAGE = [
    # gate_check stopped noticing that a run left a suite out. Found by pointing
    # this package's own gate at this package's own test runner: the runner
    # prints "1 suite(s) skipped. That is not a pass." and exits 0, and the gate
    # answered "trustworthy green" while reporting the first suite's count as
    # the total.
    ("gates", ".claude/toolkit/scripts/gate_check.py",
     "    skipped = detect_skips(output)", "    skipped = None",
     "announced a skipped suite"),
    # plan_check stopped noticing a step that states its own price. The step
    # tagged "mechanical, no writing, no judgement" cost two releases.
    ("plan", ".claude/toolkit/scripts/plan_check.py",
     "COST = [", "COST = []  # gutted\nUNUSED = [",
     "called itself mechanical"),
]


SABOTAGE = [
    (".claude/toolkit/scripts/check_lanes.py", "def cmd_check(args) -> int:", "    return 0"),
    (".claude/toolkit/scripts/gate_check.py", "def cmd_run(args) -> int:", "    return 0"),
    (".claude/toolkit/scripts/rules_check.py", "def judge(rules):", "    return []"),
    (".claude/toolkit/scripts/fleet.py", "def require(desks, slug, what):", "    return None"),
    (".claude/toolkit/scripts/token_audit.py", "def check_record(path):", "    return 0"),
    (".claude/toolkit/scripts/plan_check.py", "def judge(plan):", "    return []"),
]


def sabotage(repo):
    """Leave every artifact running and exiting 0, but unable to refuse.

    This is the shape of a real regression, not a contrived one: somebody
    short-circuits a function while debugging, the script still runs, every
    wrapper around it still reports success, and the protection is gone with no
    error anywhere.
    """
    for rel, signature, short in SABOTAGE:
        path = repo / rel
        source = path.read_text(encoding="utf-8")
        assert signature in source, "cannot sabotage {}: {} is gone".format(rel, signature)
        path.write_text(
            source.replace(signature, signature + "\n" + short + "  # sabotage", 1),
            encoding="utf-8",
        )


def receipts(output):
    return [ln.strip() for ln in output.splitlines() if "GLITCH-RECEIPT" in ln]


with tempfile.TemporaryDirectory() as tmp:
    repo = pathlib.Path(tmp) / "repo"
    repo.mkdir()

    # Day one. Nothing installed, and the two shipped steps must say so.
    def uninstalled():
        code, out = glitch(repo, "check", "--all")
        assert code == 1, "expected exit 1 on an empty repo, got {}".format(code)
        assert not receipts(out), "an empty repo was issued a receipt"
        assert "is not installed" in out, out

    check("an empty repo fails and is issued no receipt", uninstalled)

    # While three of the steps were unwritten, status printed "not shipped
    # yet" against each of them and counted them, so the path never described a
    # plan in the present tense. All six ship now, so that branch has no live
    # instance left, and this asserts the other side of the same promise: the
    # count is real and nothing here is being announced early.
    def status_counts_honestly():
        code, out = glitch(repo, "status")
        assert code == 0, code
        assert "6 of 6 steps have shipped" in out, out
        assert "not shipped yet" not in out, out

    check("status counts the steps that shipped, and all six have", status_counts_honestly)

    install(repo)

    def installed():
        code, out = glitch(repo, "check", "--all")
        assert code == 0, "expected exit 0 after install, got {}\n{}".format(code, out)
        got = receipts(out)
        assert len(got) == 6, "expected six receipts, got {}".format(got)
        assert all(r.startswith("GLITCH-RECEIPT 1 ") and " PASS " in r for r in got), got

    check("control: installed artifacts pass and are issued receipts", installed)

    # The reason this file exists.
    def toothless():
        before = receipts(glitch(repo, "check", "--all")[1])
        sabotage(repo)
        code, out = glitch(repo, "check", "--all")
        assert code == 1, (
            "SABOTAGED artifacts were accepted (exit {}). They run and exit 0 but "
            "refuse nothing, so the checker is only looking for files.".format(code)
        )
        assert not receipts(out), "a receipt was issued for artifacts that refuse nothing"
        assert "refusing nothing" in out or "decoration" in out, out
        assert before, "the control produced no receipts, so this proves nothing"

    check("SABOTAGE: artifacts that run but refuse nothing are rejected", toothless)

    # Rebuild clean for the remaining cases.
    shutil.rmtree(repo)
    repo.mkdir()
    install(repo)

    def half_installed():
        shutil.move(str(repo / ".claude/skills/lane-claim"), str(repo / "lane-claim-moved"))
        try:
            code, out = glitch(repo, "check", "lanes")
            assert code == 1, "a half-installed step passed (exit {})".format(code)
            assert not receipts(out), "a receipt was issued for a half-installed step"
        finally:
            shutil.move(str(repo / "lane-claim-moved"), str(repo / ".claude/skills/lane-claim"))

    check("a working script with no skill beside it is not complete", half_installed)

    def deterministic():
        first = receipts(glitch(repo, "check", "gates")[1])
        second = receipts(glitch(repo, "check", "gates")[1])
        assert first == second, "the same installation produced two receipts:\n{}\n{}".format(
            first, second
        )
        assert first, "no receipt to compare"

    check("the same installation always produces the same receipt", deterministic)

    def content_addressed():
        before = receipts(glitch(repo, "check", "gates")[1])
        target = repo / ".claude/toolkit/scripts/gate_check.py"
        original = target.read_bytes()
        target.write_bytes(original + b"\n# edited by the reader\n")
        try:
            after = receipts(glitch(repo, "check", "gates")[1])
            assert after and before, "missing a receipt to compare"
            assert after != before, (
                "editing the artifact did not change the receipt, so the hash is not "
                "describing the installation it claims to describe"
            )
        finally:
            target.write_bytes(original)
        restored = receipts(glitch(repo, "check", "gates")[1])
        assert restored == before, "restoring the artifact did not restore the receipt"

    check("editing an artifact changes its receipt, restoring it changes it back", content_addressed)

    # The docstring promises the reader that checking their repo does not write
    # to it. check_lanes.py resolves .claude/lanes against the working
    # directory, so getting this wrong would leave claim files behind in a
    # stranger's project every time they ran a check.
    def read_only():
        before = sorted(p.relative_to(repo).as_posix() for p in repo.rglob("*") if p.is_file())
        glitch(repo, "check", "--all")
        glitch(repo, "status")
        after = sorted(p.relative_to(repo).as_posix() for p in repo.rglob("*") if p.is_file())
        assert before == after, "checking the repo changed it: {}".format(
            sorted(set(after) - set(before)) or sorted(set(before) - set(after))
        )

    check("checking a repo writes nothing into it", read_only)

    def unknown_step():
        code, out = glitch(repo, "check", "no-such-step")
        assert code == 2, code
        assert "no such step" in out, out
        assert not receipts(out), out

    check("an unknown step id is refused, not guessed at", unknown_step)

    def artifact(name, *args):
        p = subprocess.run(
            [sys.executable, str(repo / ".claude/toolkit/scripts" / name)] + list(args),
            capture_output=True,
            text=True,
            timeout=300,
        )
        return p.returncode, p.stdout + p.stderr

    # A starter that its own checker refuses would be the worst possible first
    # five minutes: the reader downloads the file we told them to start from,
    # runs the check we told them to run, and it says no.
    def templates_pass_their_own_checkers():
        for name in ("CLAUDE.ecom.md", "CLAUDE.saas.md"):
            code, out = artifact("rules_check.py", "check", str(TOOLKIT / "templates" / name))
            assert code == 0, "{} fails rules_check.py:\n{}".format(name, out)
        code, out = artifact(
            "fleet.py", "--fleet", str(TOOLKIT / "templates" / "FLEET.md"), "desks"
        )
        assert code == 0, "the FLEET.md template fails fleet.py desks:\n" + out

    check("the starter templates pass the checkers that read them",
          templates_pass_their_own_checkers)

    # And the one that must not. FLOOR.md holds numbers that can only be the
    # reader's, so a template that passed unedited would let somebody complete
    # the floor step by downloading a file and measuring nothing.
    def floor_template_does_not_pass():
        code, out = artifact("token_audit.py", "--record", str(TOOLKIT / "templates" / "FLOOR.md"))
        assert code != 0, (
            "the FLOOR.md template passes unedited, so the floor step can be "
            "completed without measuring anything:\n" + out
        )

    check("the floor template does not pass itself", floor_template_does_not_pass)

    # And the other one that must not, for the same reason one step further on.
    # A plan is a decision somebody made about their own work, so a template
    # that passed unedited would let the last step be completed by downloading
    # a file and deciding nothing. It is also the file plan_check.py names in
    # its own docstring as the thing it exists to catch, which makes this the
    # one template whose refusal is load bearing.
    def plan_template_does_not_pass():
        code, out = artifact("plan_check.py", "check", str(TOOLKIT / "templates" / "PLAN.md"))
        assert code != 0, (
            "the PLAN.md template passes unedited, so the plan step can be "
            "completed without planning anything:\n" + out
        )

    check("the plan template does not pass itself", plan_template_does_not_pass)

    # Four steps are checked against the reader's own work rather than against
    # a file we shipped. If those checks only looked at our scripts, the steps
    # would be complete the moment somebody downloaded them, which is the whole
    # thing this path is not.
    def readers_own_work_is_checked():
        cases = [
            ("rules", "CLAUDE.md",
             "<!-- rules:start -->\n- Write clean, maintainable code.\n<!-- rules:end -->\n"),
            ("fleet", "FLEET.md",
             "<!-- desks:start -->\n| desk | owns | commits |\n| --- | --- | --- |\n"
             "| a | one | yes |\n| b | two | yes |\n<!-- desks:end -->\n"),
            ("floor", "FLOOR.md", "2026-01-14  floor 31,400 tokens\n"),
            ("plan", "PLAN.md",
             "## Plan: ship it\n\n"
             "**Written** 2026-01-14 by Dana\n**Approved** 2026-01-14 by Dana\n\n"
             "### What we are NOT doing\n\n- <thing we are not touching>\n\n"
             "### What we ARE doing\n\n- Ship it.\n\n"
             "### How we will know it worked\n\n- The tests pass.\n"),
        ]
        for step, name, broken in cases:
            path = repo / name
            original = path.read_bytes()
            path.write_text(broken, encoding="utf-8")
            try:
                code, out = glitch(repo, "check", step)
                assert code == 1, "{}: a broken {} passed (exit {})".format(step, name, code)
                assert not receipts(out), "{}: a receipt was issued for a broken {}".format(
                    step, name)
            finally:
                path.write_bytes(original)

        code, out = glitch(repo, "check", "--all")
        assert code == 0, "restoring the work files did not restore the pass:\n" + out
        assert len(receipts(out)) == 6, receipts(out)

    check("a step whose work is the reader's own file checks that file",
          readers_own_work_is_checked)

    # An installed token_audit.py from before --record and --transcripts existed.
    # Appendix A printed one until 2026-08-27 and readers typed it out, but this
    # fixture no longer stands for the appendix, because the appendix no longer
    # carries a listing and the behaviour has to outlive it either way: old
    # copies are on disks, in gists and in other people's repositories, and will
    # be for years. Without this the reader gets argparse complaining about an
    # unrecognised argument and no way to tell which file is the problem.
    #
    # It asserts the flags are named and asserts nothing about where the file
    # came from, because the check is no longer allowed to claim it knows.
    def an_older_token_audit_is_named_not_crashed_on():
        path = repo / ".claude/toolkit/scripts/token_audit.py"
        original = path.read_bytes()
        source = original.decode("utf-8")
        for flag in ('ap.add_argument("--record"', 'ap.add_argument("--transcripts"'):
            i = source.index(flag)
            j = source.index("\n", source.index(")", i))
            source = source[:i] + "pass" + source[j:]
        path.write_text(source, encoding="utf-8")
        try:
            code, out = glitch(repo, "check", "floor")
            assert code == 1, "an older token_audit.py passed the floor step (exit {})".format(code)
            assert not receipts(out), "a receipt was issued for a token_audit.py that cannot record"
            for flag in ("--record", "--transcripts"):
                assert flag in out, "the failure does not name the flag it needs:\n" + out
            assert "token_audit.py" in out, "the failure does not name the file:\n" + out
            assert "Traceback" not in out, "the reader got a traceback instead of a sentence:\n" + out
        finally:
            path.write_bytes(original)

        code, out = glitch(repo, "check", "floor")
        assert code == 0, "restoring token_audit.py did not restore the pass:\n" + out

    check("a token_audit.py without the flags this step needs is named, not crashed on",
          an_older_token_audit_is_named_not_crashed_on)

    # Appendix A tells the reader that where they keep the script is a matter of
    # taste, and then prints every example as "python tools/token_audit.py".
    # SCRIPT_DIRS did not include tools/, so following the book exactly produced
    # a check that said the file was not installed. This is the case that would
    # have caught it: the artifact is in the directory the documentation typed,
    # and nowhere else.
    def the_directory_the_book_uses_is_searched():
        source = repo / ".claude/toolkit/scripts/token_audit.py"
        moved = repo / "tools" / "token_audit.py"
        moved.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(moved))
        try:
            code, out = glitch(repo, "check", "floor")
            assert code == 0, (
                "token_audit.py in tools/, where Appendix A puts it, was not found:\n" + out
            )
            assert receipts(out), "no receipt for a correctly installed token_audit.py:\n" + out
        finally:
            shutil.move(str(moved), str(source))
            moved.parent.rmdir()

    check("the directory the book's own examples use is searched",
          the_directory_the_book_uses_is_searched)



# `install` is the one command that writes into somebody else's repository, so
# the two things worth proving about it are both refusals: it must not claim a
# step is done when the work is the reader's, and it must not quietly replace a
# file the reader has edited.
with tempfile.TemporaryDirectory() as tmp:
    fresh = pathlib.Path(tmp) / "fresh"
    fresh.mkdir()

    def install_writes_the_artifacts():
        code, out = glitch(fresh, "install")
        assert code == 0, "install exited {}\n{}".format(code, out)
        for name in SCRIPTS:
            assert (fresh / ".claude/toolkit/scripts" / name).is_file(), name + " not written"
        for name in SKILLS:
            assert (fresh / ".claude/skills" / name / "SKILL.md").is_file(), name + " not written"
        # Templates are reading material, and must not land among the scripts.
        assert (fresh / ".claude/toolkit/templates/FLOOR.md").is_file(), out
        assert not (fresh / ".claude/toolkit/scripts/templates").exists(), (
            "templates were installed into the scripts directory"
        )

    check("install writes the artifacts, and templates are not scripts",
          install_writes_the_artifacts)

    # The important one. Four of the six steps are the reader's own file, so a
    # repo that has only run the installer has done none of them. If this ever
    # goes green, `install` has started handing out completions it did not earn
    # and the Build Path has become "you ran a command".
    def install_completes_nothing_of_the_readers():
        code, out = glitch(fresh, "check", "--all")
        assert code == 1, "a freshly installed repo passed every step:\n" + out
        got = receipts(out)
        assert len(got) == 2, (
            "expected receipts only for the two steps that are purely our "
            "artifacts, got {}:\n{}".format(got, out)
        )
        for step in ("rules", "fleet", "floor", "plan"):
            assert " " + step + " " not in " ".join(got), (
                step + " was issued a receipt without the reader writing anything:\n" + out
            )

    check("install completes none of the four steps that are the reader's own work",
          install_completes_nothing_of_the_readers)

    def install_does_not_overwrite():
        edited = fresh / ".claude/toolkit/scripts/gate_check.py"
        mine = edited.read_text(encoding="utf-8") + "\n# a line the reader added\n"
        edited.write_text(mine, encoding="utf-8")

        code, out = glitch(fresh, "install")
        assert code == 0, out
        assert edited.read_text(encoding="utf-8") == mine, (
            "install replaced an edited artifact without being asked"
        )
        assert "kept" in out, "install did not report what it left alone:\n" + out

        code, out = glitch(fresh, "install", "--force")
        assert code == 0, out
        assert edited.read_text(encoding="utf-8") != mine, (
            "--force did not replace the edited artifact"
        )

    check("install keeps an edited artifact, and --force replaces it",
          install_does_not_overwrite)


def one_refusal_removed():
    """Each artifact keeps every ability but one, and must still be caught.

    The step is run on a healthy repo first. That control is the half that
    matters: a check that fires on a healthy tree is as broken as one that
    never fires, and this suite would happily prove the wrong thing without
    it. Both halves are asserted for every entry.
    """
    for step, rel, needle, replacement, expected in PARTIAL_SABOTAGE:
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp)
            install(repo)

            code, out = glitch(repo, "check", step)
            assert code == 0, (
                "control: step '{}' does not pass on a healthy repo, so the "
                "sabotage below proves nothing:\n{}".format(step, out)
            )

            target = repo / rel
            text = target.read_text(encoding="utf-8")
            assert needle in text, (
                "the sabotage for '{}' no longer matches {}: looked for {!r}. "
                "The artifact changed and this test stopped testing it."
                .format(step, rel, needle)
            )
            target.write_text(text.replace(needle, replacement, 1), encoding="utf-8")

            code, out = glitch(repo, "check", step)
            assert code != 0, (
                "step '{}' passed with one refusal removed from {}. It still "
                "refuses everything else, which is what real drift looks "
                "like:\n{}".format(step, rel, out)
            )
            assert expected in out, (
                "step '{}' failed, but not for the removed refusal: expected "
                "{!r} in the output.\n{}".format(step, expected, out)
            )


check("an artifact that lost ONE refusal and kept the rest is still caught",
      one_refusal_removed)


print("")
print("{} passed, {} failed".format(passed, failed))

if passed == 0:
    print("nothing ran. that is a failure, not a pass.")
    sys.exit(1)
sys.exit(1 if failed else 0)
