"""The Build Path, checked in your own repo.

    glitch install                       put the artifacts in this repository
    glitch status                        what is installed, what is not
    glitch check lanes                   verify one step
    glitch check --all                   every step

Installed as a package this is the `glitch` command. It is also still one file
that runs on its own: copy it into a repository and `status` and `check` work
unchanged, with no install step and nothing on the path. Only `install` needs
the rest of the package, and it says so rather than failing obscurely.

A step is not complete because you read it. It is complete when the artifact it
installs is present AND runs AND can still say no. That last part is the whole
point: an artifact that only ever passes is indistinguishable from one that was
never wired up, which is Chapter 18 in one sentence.

So every check here does three things, and reports which of them failed:

  1. finds the files
  2. runs the artifact and expects it to work
  3. runs it against a deliberately broken case and expects it to REFUSE

If step 3 is missing from a check, that check is decoration.

WHAT THIS CANNOT DO. Stated plainly rather than left for you to assume:

  * The receipt is not tamper proof. It is a line of text you could type
    yourself. Nothing here signs it and nothing on the website can tell the
    difference. The only person a forged receipt fools is the person who forged
    it, which is why it is not worth defending against.
  * It checks that an artifact is installed and working. It cannot check that
    you used it, or that you used it on the right files.
  * It reads your repository and writes nothing into it. The probes that need to
    write run in a temporary directory that is removed afterwards.
  * Nothing leaves your machine. There are no network calls in this file.

Standard library only, on purpose. It has to run in a stranger's repo on the
first day, before they have installed anything at all.
"""
import argparse
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

RECEIPT_VERSION = "1"
RECEIPT_PREFIX = "GLITCH-RECEIPT"

# Where an artifact might reasonably have been installed. Searched in order.
# A list rather than one mandated directory, because this installs into somebody
# else's repository and telling them where their scripts live is not our
# business. The check asks whether it is installed and working, not whether it
# sits in the folder we would have picked.
#
# tools/ is on this list because the book puts it there. Appendix A tells the
# reader that where they keep the script is a matter of taste, and then every
# example it prints is "python tools/token_audit.py". For a day this list did
# not include it, so a reader who followed the book exactly, into the directory
# the book itself typed, was told by the check that the file was not installed.
# That is the worst shape a refusal can take: correct-looking, confidently
# wrong, and pointing at the reader.
#
# The general lesson, and the reason this comment is longer than the list: a
# search path is a promise about other people's habits, and the place to look
# for the habits is the documentation that created them.
SCRIPT_DIRS = [
    ".claude/toolkit/scripts",
    "toolkit/scripts",
    "scripts",
    ".claude/scripts",
    "tools",
    ".claude/tools",
    ".",
]
SKILL_DIRS = [".claude/skills", "skills", ".claude/toolkit/skills"]

# Files the reader writes, rather than files we ship. Three of the five steps
# are checked against the reader's own work, because for those steps the work IS
# the file: a rules file that holds, a desk table with one committer, a floor
# measured twice. Checking only that a script is installed would turn those
# steps into "you downloaded something", which is not a step.
DOC_DIRS = [".", ".claude", "docs"]

TIMEOUT = 120

# Where the artifacts we ship live, once this file is installed as a package.
#
# Resolved from this file's own location rather than through importlib.resources
# so that the property the module docstring claims stays true: copy this single
# file into a repository and `status` and `check` still work, because neither of
# them ever reads this path. Only `install` does, and a bare copied file has
# nothing to install anyway. It says so rather than raising.
ASSETS = pathlib.Path(__file__).resolve().parent / "_assets"

# What `install` writes, and where. The destinations are the first entry of the
# matching search path above, so a fresh install is found by the same lookup a
# reader's hand-placed copy is found by. Change one and the other has to move.
INSTALL_SCRIPTS = ".claude/toolkit/scripts"
INSTALL_SKILLS = ".claude/skills"
# Templates are not scripts and do not go in the scripts directory. They are
# reading material and starting points; nothing on the search path looks here.
INSTALL_TEMPLATES = ".claude/toolkit/templates"


class Result:
    def __init__(self):
        self.evidence = []   # (relative path, sha256 of its bytes)
        self.notes = []
        self.failures = []

    def found(self, path, root):
        rel = path.relative_to(root).as_posix()
        self.evidence.append((rel, _sha256_file(path)))
        return rel

    def note(self, msg):
        self.notes.append(msg)

    def fail(self, msg):
        self.failures.append(msg)

    @property
    def ok(self):
        return not self.failures

    def digest(self):
        # Over the files found, not over the notes. The hash answers "is this
        # the same installation as last time", so it has to change when an
        # artifact changes and must not change because a message was reworded.
        h = hashlib.sha256()
        for rel, sha in sorted(self.evidence):
            h.update(rel.encode("utf-8"))
            h.update(b"\0")
            h.update(sha.encode("ascii"))
            h.update(b"\0")
        return h.hexdigest()


def _sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _find(root, dirs, name):
    for d in dirs:
        candidate = root / d / name
        if candidate.is_file():
            return candidate
    return None


def _run(args, cwd):
    """Run a probe. Returns (exit code, combined output).

    A crash, a timeout and a missing interpreter each come back as a distinct
    negative exit code rather than an exception. The caller's job is to tell a
    person what went wrong, not to print a traceback in somebody else's repo.
    """
    try:
        p = subprocess.run(
            args, cwd=str(cwd), capture_output=True, text=True, timeout=TIMEOUT
        )
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        return -1, "timed out after {}s".format(TIMEOUT)
    except OSError as e:
        return -2, str(e)


# ---------------------------------------------------------------- the checks


def check_rules(root):
    """Chapter 1. A rules file everyone nods at and nobody can violate."""
    r = Result()

    script = _find(root, SCRIPT_DIRS, "rules_check.py")
    if script:
        r.note("found " + r.found(script, root))
    else:
        r.fail("rules_check.py is not installed. Looked in: " + ", ".join(SCRIPT_DIRS))
        return r

    rules_file = _find(root, DOC_DIRS, "CLAUDE.md") or _find(root, DOC_DIRS, "AGENTS.md")
    if not rules_file:
        r.fail(
            "no CLAUDE.md in this repository. This step is the rules file, not the\n"
            "script that reads it. Start from CLAUDE.ecom.md or CLAUDE.saas.md."
        )
        return r
    r.note("found " + r.found(rules_file, root))

    # Their file, not a sample of ours. The digest below covers it, so the step
    # changes state when the rules change, which is the behaviour you want from
    # a file that is supposed to be maintained rather than written once.
    code, out = _run([sys.executable, str(script), "check", str(rules_file)], root)
    if code != 0:
        r.fail("your rules file does not hold yet:\n" + out.strip())
        return r
    r.note("every rule in your CLAUDE.md names something that would break it")

    # The half that matters. A rules_check that accepts anything would have
    # passed the line above too, and would go on passing after somebody
    # replaces the rules with adjectives.
    with tempfile.TemporaryDirectory() as tmp:
        box = pathlib.Path(tmp)
        moods = box / "moods.md"
        moods.write_text(
            "<!-- rules:start -->\n"
            "- Write clean, maintainable code.\n"
            "- Follow best practices where possible.\n"
            "  Violated by: not doing that\n"
            "<!-- rules:end -->\n",
            encoding="utf-8",
        )
        code, out = _run([sys.executable, str(script), "check", str(moods)], box)
        if code == 0:
            r.fail(
                "rules_check.py accepted two rules that cannot be violated. It runs, "
                "but it is refusing nothing, so it would accept a rules file made "
                "entirely of adjectives, which is the file it exists to catch."
            )
        else:
            r.note("refuses a rule with no failing case, which is the whole job")

    return r


def check_plan(root):
    """Chapter 20. Work that was wrong from the moment it was asked for."""
    r = Result()

    script = _find(root, SCRIPT_DIRS, "plan_check.py")
    if script:
        r.note("found " + r.found(script, root))
    else:
        r.fail("plan_check.py is not installed. Looked in: " + ", ".join(SCRIPT_DIRS))
        return r

    plan = _find(root, DOC_DIRS, "PLAN.md")
    if not plan:
        r.fail(
            "no PLAN.md in this repository. This step is the plan, not the script\n"
            "that reads it. Start from the PLAN.md template; it does not pass\n"
            "unedited, which is the point of it."
        )
        return r
    r.note("found " + r.found(plan, root))

    code, out = _run([sys.executable, str(script), "check", str(plan)], root)
    if code != 0:
        r.fail("your plan is not a plan of record yet:\n" + out.strip())
        return r
    r.note("your plan names what it is not doing, who approved it, and how it can fail")

    # The refusal. Every other step in this path catches work that went wrong;
    # this one catches work that was wrong when it was asked for, so a checker
    # that had stopped refusing would leave the one gap none of the others see.
    with tempfile.TemporaryDirectory() as tmp:
        box = pathlib.Path(tmp)
        wishful = box / "wishful.md"
        wishful.write_text(
            "## Plan: <one line>\n\n"
            "**Written** 2026-01-14 by Same Person\n"
            "**Approved** 2026-01-14 by Same Person\n\n"
            "### What we are NOT doing\n\n"
            "- <thing we are not touching>\n\n"
            "### What we ARE doing\n\n"
            "- Ship it.\n\n"
            "### How we will know it worked\n\n"
            "- The tests pass.\n",
            encoding="utf-8",
        )
        code, out = _run([sys.executable, str(script), "check", str(wishful)], box)
        if code == 0:
            r.fail(
                "plan_check.py accepted a plan approved by its own author, with an "
                "empty scope list and 'the tests pass' as its only verification. It "
                "runs, but it is refusing nothing, so it would accept the template "
                "unedited, which is the file it exists to catch."
            )
        else:
            r.note("refuses a plan nobody could fail, which is the whole job")

        # The second refusal, and the narrow one. The plan above fails several
        # ways at once, so it would still be rejected by a checker that had lost
        # any single test. This one is complete, approved by somebody other than
        # its author, and verified by something that can come back false. Its
        # only defect is a step that states its own price.
        #
        # It carries a **Checked** line, and that is load-bearing in two
        # directions. Without one this plan would ALSO be refused for planning
        # around a registry nobody asked, and a fixture with two defects cannot
        # prove which refusal is still working -- gutting the price list would
        # leave it rejected anyway and the sabotage would go unnoticed. That
        # happened on 11 September 2026, during the change that added the
        # second rule, and tests/test_cli.py caught it. It is also the positive
        # control for the new rule: this is what a step reaching outside the
        # repository looks like when somebody did ask.
        #
        # 8 September 2026: a distribution plan tagged a step "mechanical, no
        # writing, no judgement". It cost two releases, neither knowable from
        # the plan. The word was an estimate wearing the clothes of a fact.
        priced = box / "priced.md"
        priced.write_text(
            "## Plan: List the package on the registries\n\n"
            "**Written** 2026-09-08 by A Writer\n"
            "**Approved** 2026-09-08 by A Reviewer\n\n"
            "### What we are NOT doing\n\n"
            "- Publishing the incident writeup; that is its own decision.\n"
            "- Building a plugin wrapper for any client.\n\n"
            "### What we ARE doing\n\n"
            "- List on the official MCP registry. Mechanical, no writing, no judgement.\n"
            "- **Checked** 2026-09-08 the registry API answered with its own server list, so\n"
            "  it is live and accepting.\n\n"
            "### How we will know it worked\n\n"
            "- The registry API returns the server at the version named with status active.\n",
            encoding="utf-8",
        )
        code, out = _run([sys.executable, str(script), "check", str(priced)], box)
        if code == 0:
            r.fail(
                "plan_check.py accepted a step that called itself mechanical with "
                "nothing in the plan measuring that. An unmeasured price is the one "
                "claim in a plan that cannot come back false until you are at the "
                "far end of the work."
            )
        else:
            r.note("refuses a step that states a price nothing measured")

        # The third refusal, and the narrowest. This plan is complete, approved
        # by somebody other than its author, scoped, verified by something that
        # can come back false, and states no price. Its only defect is that it
        # plans around a repository nobody asked whether it was open.
        #
        # 9 September 2026: a repository was chosen as a listing target. Its
        # contributing guide was read and quoted, its entry format derived, its
        # categories compared, the list searched for duplicates. Four checks,
        # four passes, all four against files from a CDN that serves them the
        # same whether a repository is alive or archived. It had been archived
        # on 1 August and pull requests were disabled. The banner was on the
        # page, which nothing had opened; the state was one field in the API,
        # which nothing had asked for.
        #
        # A **Checked** line with a date is what turns that from something you
        # remember doing into something the plan can be missing.
        unchecked = box / "unchecked.md"
        unchecked.write_text(
            "## Plan: get the package in front of people who use this kind of thing\n\n"
            "**Written** 2026-09-09 by A Writer\n"
            "**Approved** 2026-09-09 by A Reviewer\n\n"
            "### What we are NOT doing\n\n"
            "- Paying for placement anywhere. Not this round.\n"
            "- Writing a plugin wrapper for any client.\n\n"
            "### What we ARE doing\n\n"
            "- Open a pull request against the awesome list, in their entry format.\n\n"
            "### How we will know it worked\n\n"
            "- The pull request exists at a URL and its state is open or merged.\n",
            encoding="utf-8",
        )
        code, out = _run([sys.executable, str(script), "check", str(unchecked)], box)
        if code == 0:
            r.fail(
                "plan_check.py accepted a step that opens a pull request against "
                "somebody else's repository with no dated line saying anybody asked "
                "whether it accepts them. A contributing guide reads exactly the "
                "same from a repository archived in August, which is how four "
                "separate checks passed against one."
            )
        else:
            r.note("refuses a step that plans around a target nobody asked")

    return r


def check_fleet(root):
    """Chapter 14. One chat cannot hold a business, and every chat improvises."""
    r = Result()

    script = _find(root, SCRIPT_DIRS, "fleet.py")
    msg = _find(root, SKILL_DIRS, "fleet-msg/SKILL.md")
    sync = _find(root, SKILL_DIRS, "fleet-sync/SKILL.md")

    if script:
        r.note("found " + r.found(script, root))
    else:
        r.fail("fleet.py is not installed. Looked in: " + ", ".join(SCRIPT_DIRS))

    for skill, name in ((msg, "fleet-msg"), (sync, "fleet-sync")):
        if skill:
            r.note("found " + r.found(skill, root))
        else:
            r.fail("the {} skill is not installed. Looked in: {}"
                   .format(name, ", ".join(SKILL_DIRS)))

    if not script:
        return r

    table = _find(root, DOC_DIRS, "FLEET.md")
    if not table:
        r.fail(
            "no FLEET.md in this repository. The desks and the one desk allowed to\n"
            "commit are the work of this step. Start from the FLEET.md template."
        )
        return r
    r.note("found " + r.found(table, root))

    code, out = _run([sys.executable, str(script), "--fleet", str(table), "desks"], root)
    if code != 0:
        r.fail("your desk table does not hold yet:\n" + out.strip())
        return r
    r.note("your desk table names its desks and exactly one of them commits")

    with tempfile.TemporaryDirectory() as tmp:
        box = pathlib.Path(tmp)
        (box / "FLEET.md").write_text(
            "<!-- desks:start -->\n"
            "| desk | owns | commits |\n"
            "| --- | --- | --- |\n"
            "| probe-a | the probe | yes |\n"
            "| probe-b | the other probe | no |\n"
            "<!-- desks:end -->\n",
            encoding="utf-8",
        )

        code, out = _run(
            [sys.executable, str(script), "send", "--to", "probe-b", "--from", "probe-a",
             "--subject", "glitch check", "--body", "a probe from glitch.py"],
            box,
        )
        if code != 0:
            r.fail("fleet.py could not deliver a message between two real desks (exit {}). "
                   "Output:\n{}".format(code, out.strip()))
            return r

        code, out = _run([sys.executable, str(script), "inbox", "--me", "probe-b"], box)
        if code != 0 or "glitch check" not in out:
            r.fail("fleet.py delivered a message that its own inbox cannot find. Output:\n"
                   + out.strip())
            return r
        r.note("delivers between two desks and the receiving desk can read it")

        # Refusal one: an address nobody watches. If this is accepted, the
        # message goes into a directory no session opens while the sender is
        # told it was sent, which is the failure mode worth having a tool for.
        code, out = _run(
            [sys.executable, str(script), "send", "--to", "nobody", "--from", "probe-a",
             "--subject", "x", "--body", "y"],
            box,
        )
        if code == 0:
            r.fail(
                "fleet.py sent to a desk that is not in the table. It runs, but a typo "
                "in an address now delivers into a hole while telling you it arrived."
            )
        else:
            r.note("refuses an address that is not a desk")

        # Refusal two: the only mistake in a shared checkout that is not
        # recoverable.
        (box / "FLEET.md").write_text(
            "<!-- desks:start -->\n"
            "| desk | owns | commits |\n"
            "| --- | --- | --- |\n"
            "| probe-a | the probe | yes |\n"
            "| probe-b | the other probe | yes |\n"
            "<!-- desks:end -->\n",
            encoding="utf-8",
        )
        code, out = _run([sys.executable, str(script), "desks"], box)
        if code == 0:
            r.fail(
                "fleet.py accepted a table where two desks may both commit. That is "
                "the one fleet mistake you cannot undo by reading a file and writing "
                "it again."
            )
        else:
            r.note("refuses a table where two desks may both commit")

    return r


def check_floor(root):
    """Chapter 3. The startup floor is paid on every turn and nobody measured theirs."""
    r = Result()

    script = _find(root, SCRIPT_DIRS, "token_audit.py")
    if script:
        r.note("found " + r.found(script, root))
    else:
        r.fail("token_audit.py is not installed. Looked in: " + ", ".join(SCRIPT_DIRS))
        return r

    # Which token_audit.py is this?
    #
    # Older copies of this script are in circulation and not all of them accept
    # the flags this step uses. Appendix A printed a full listing until
    # 2026-08-27, and copies people typed out of it will be on disks for years
    # after the appendix stopped carrying it. Without this probe such a reader
    # gets argparse shouting about an unrecognised argument and no way to tell
    # which file is the problem.
    #
    # This deliberately does not rank the two copies, and an earlier version of
    # this message did. On 2026-08-27 the ranking would have been backwards: the
    # printed listing carried a fix for project paths containing a space that
    # the shipped file had lost, so the copy with the newer flags was the copy
    # with the older bug. A usage string cannot tell you which file is more
    # correct. It can tell you which flags this step needs, and that is all this
    # says.
    #
    # So ask the script what it accepts before assuming it accepts anything.
    code, usage = _run([sys.executable, str(script), "--help"], root)
    if code != 0:
        r.fail("token_audit.py is installed but will not run (exit {}):\n{}".format(
            code, usage.strip()))
        return r
    missing = [flag for flag in ("--record", "--transcripts") if flag not in usage]
    if missing:
        r.fail(
            "the token_audit.py you installed does not accept " + " or ".join(missing) + ".\n"
            "This step records your floor with --record, and reads a transcript\n"
            "directory that is not the default with --transcripts, so a copy from\n"
            "before those existed cannot answer it. Install the token_audit.py from\n"
            "this step's artifacts over the one you have and run this check again.\n"
            "Nothing you measured with the older copy is wrong. It just cannot be\n"
            "asked these two questions."
        )
        return r

    record = _find(root, DOC_DIRS, "FLOOR.md")
    if not record:
        r.fail(
            "no FLOOR.md in this repository. The number is the work of this step,\n"
            "and a number you did not write down is one you will measure again."
        )
        return r
    r.note("found " + r.found(record, root))

    code, out = _run([sys.executable, str(script), "--record", str(record)], root)
    if code != 0:
        r.fail("your floor record is not two measurements yet:\n" + out.strip())
        return r
    r.note("your floor is recorded twice, with dates, so the change is visible")

    with tempfile.TemporaryDirectory() as tmp:
        box = pathlib.Path(tmp)

        # It can measure. A synthetic transcript with three turns, so this
        # probe does not depend on the reader having sessions on this machine.
        sessions = box / "sessions"
        sessions.mkdir()
        rows = []
        for i in range(3):
            rows.append(json.dumps({
                "type": "assistant",
                "timestamp": "2026-01-14T09:00:0{}".format(i),
                "message": {
                    "id": "msg_{}".format(i),
                    # Named, because a real assistant record always is, and this
                    # fixture stood in for one without it. token_audit.py skips a
                    # turn whose model is missing or synthetic, which is the rule
                    # the command on the site has used since it was written: a
                    # synthetic turn carries no tokens and counting it inflates
                    # the turn count. Across 44,634 real assistant records on the
                    # machine that rule was checked against, none was missing a
                    # model and all 42 synthetic ones were zero. So the rule
                    # costs a reader nothing and this fixture was the only thing
                    # in the repository shaped like a transcript that is not one.
                    "model": "claude-opus-4-8",
                    "usage": {
                        "input_tokens": 12,
                        "cache_read_input_tokens": 20000 + i * 5000,
                        "cache_creation_input_tokens": 400,
                        "output_tokens": 300,
                    },
                    "content": [],
                },
            }))
        (sessions / "probe.jsonl").write_text("\n".join(rows) + "\n", encoding="utf-8")

        code, out = _run([sys.executable, str(script), "--transcripts", str(sessions)], box)
        if code != 0 or "floor" not in out:
            r.fail("token_audit.py could not measure a transcript with three turns "
                   "(exit {}). Output:\n{}".format(code, out.strip()))
            return r
        r.note("measures a session it has never seen before")

        # Refusal one: nothing to read. A measuring tool that reports a
        # confident zero on no data is the false green in measurement form,
        # and it is the one nobody thinks to test for.
        empty = box / "empty"
        empty.mkdir()
        code, out = _run([sys.executable, str(script), "--transcripts", str(empty)], box)
        if code == 0:
            r.fail(
                "token_audit.py reported success on an empty directory. A floor of "
                "nothing is the one answer that is never true, so this installation "
                "would hand you a number it did not measure."
            )
        else:
            r.note("refuses to report a floor it did not measure")

        # Refusal two: one measurement. Measuring once tells you a number;
        # the step is measuring, cutting, and measuring again.
        half = box / "half.md"
        half.write_text("2026-01-14  floor 31,400 tokens\n", encoding="utf-8")
        code, out = _run([sys.executable, str(script), "--record", str(half)], box)
        if code == 0:
            r.fail(
                "token_audit.py accepted a record holding one measurement. One number "
                "is an observation; it cannot show that anything you cut worked."
            )
        else:
            r.note("refuses a record that measured once and stopped")

    return r


def check_lanes(root):
    """Chapter 4. Two writers, one tree, second write wins, nothing errors."""
    r = Result()

    script = _find(root, SCRIPT_DIRS, "check_lanes.py")
    skill = _find(root, SKILL_DIRS, "lane-claim/SKILL.md")

    if script:
        r.note("found " + r.found(script, root))
    else:
        r.fail("check_lanes.py is not installed. Looked in: " + ", ".join(SCRIPT_DIRS))

    if skill:
        r.note("found " + r.found(skill, root))
    else:
        r.fail("the lane-claim skill is not installed. Looked in: " + ", ".join(SKILL_DIRS))

    if not script:
        return r

    # Probe in a scratch directory. check_lanes.py resolves .claude/lanes
    # against the working directory, so running it here would write claim files
    # into the reader's repo as a side effect of checking it. A check that
    # mutates the thing it is checking is not a check.
    with tempfile.TemporaryDirectory() as tmp:
        box = pathlib.Path(tmp)
        (box / "target.txt").write_text("probe\n", encoding="utf-8")

        code, out = _run([sys.executable, str(script), "status"], box)
        if code != 0:
            r.fail("check_lanes.py status exited {} on a clean tree. Output:\n{}"
                   .format(code, out.strip()))
            return r

        # It runs. Now the half that matters: can it still say no? Claim the
        # file as one lane, then ask about it as another. An artifact that
        # cannot refuse is not protecting anything.
        code, out = _run(
            [sys.executable, str(script), "claim", "probe-a", "target.txt",
             "--note", "glitch check"],
            box,
        )
        if code != 0:
            r.fail("check_lanes.py could not record a claim (exit {}). Output:\n{}"
                   .format(code, out.strip()))
            return r

        code, out = _run(
            [sys.executable, str(script), "check", "target.txt", "--lane", "probe-b"], box
        )
        if code == 0:
            r.fail(
                "check_lanes.py let lane probe-b edit a file claimed by probe-a. "
                "It runs, but it is refusing nothing, so it would not have caught "
                "the overwrite it exists to catch."
            )
        else:
            r.note("refuses a cross-lane edit, which is the case that matters")

    return r


def check_gates(root):
    """Chapter 18. A green run that covered nothing."""
    r = Result()

    script = _find(root, SCRIPT_DIRS, "gate_check.py")
    skill = _find(root, SKILL_DIRS, "gate-check/SKILL.md")

    if script:
        r.note("found " + r.found(script, root))
    else:
        r.fail("gate_check.py is not installed. Looked in: " + ", ".join(SCRIPT_DIRS))

    if skill:
        r.note("found " + r.found(skill, root))
    else:
        r.fail("the gate-check skill is not installed. Looked in: " + ", ".join(SKILL_DIRS))

    if not script:
        return r

    with tempfile.TemporaryDirectory() as tmp:
        box = pathlib.Path(tmp)

        # An honest green: exits 0 and says what it ran.
        code, out = _run(
            [sys.executable, str(script), "run", "--name", "glitch-probe", "--",
             sys.executable, "-c", "print('3 passed')"],
            box,
        )
        if code != 0:
            r.fail("gate_check.py rejected an honest green (exit {}). Output:\n{}"
                   .format(code, out.strip()))
            return r

        # The canary. Exits 0, reports nothing about what it ran. That is the
        # real quiet-flag bug from Chapter 18, and a gate_check that passes this
        # one is broken in the exact way it was written to detect.
        code, out = _run(
            [sys.executable, str(script), "run", "--name", "glitch-canary", "--",
             sys.executable, "-c", "print('done')"],
            box,
        )
        if code == 0:
            r.fail(
                "gate_check.py accepted a run that exited 0 and reported no count. "
                "That is the false green it exists to catch, so on this installation "
                "it is decoration."
            )
        else:
            r.note("catches a green run that reported no count, which is the whole job")

        # The second canary. A runner that says what it ran AND says what it
        # skipped, then exits 0. Observed on 8 Sep 2026 in this package's own
        # test runner: "1 suite(s) skipped. That is not a pass." followed by
        # exit 0, and the gate answered "trustworthy green" while reporting the
        # first suite's count as the total. Ten tests unrun, certified.
        #
        # A skip is not a failure, so the right verdict is WARN rather than
        # FAIL: green, unproven, and non-zero unless the caller passes
        # --warn-ok to accept it deliberately.
        code, out = _run(
            [sys.executable, str(script), "run", "--name", "glitch-skip", "--quiet", "--",
             sys.executable, "-c", "print('18 passed'); print('1 suite(s) skipped')"],
            box,
        )
        if code == 0:
            r.fail(
                "gate_check.py called a run trustworthy that announced a skipped "
                "suite and exited 0. A count that excludes what was skipped is "
                "not a count, and on this installation the gate cannot see it."
            )
        else:
            r.note("catches a green run that quietly left a suite out")

    return r


# ----------------------------------------------------------------- the path


class Step:
    def __init__(self, sid, title, chapter, problem, shipped, check=None, artifacts=()):
        self.id = sid
        self.title = title
        self.chapter = chapter
        self.problem = problem
        self.shipped = shipped
        self.check = check
        self.artifacts = artifacts


# Five steps, and all five ship. This table is the honest one: while three of
# them were unwritten it said so in those words rather than describing a plan in
# the present tense, which is what TOOLKIT.md warns against. If a sixth step is
# added before its artifacts exist, it goes in here with shipped=False and the
# path says so again.
STEPS = [
    Step("rules", "Rules that hold", 1,
         "A rules file everyone nods at and nobody can violate",
         shipped=True, check=check_rules,
         artifacts=("rules_check.py", "CLAUDE.ecom.md", "CLAUDE.saas.md")),
    Step("lanes", "Two writers, one tree", 4,
         "Two sessions edit one file, the second write wins, nothing errors",
         shipped=True, check=check_lanes,
         artifacts=("lane-claim/SKILL.md", "check_lanes.py")),
    Step("fleet", "Stand up your fleet", 14,
         "One chat cannot hold a business, and every chat improvises its handoff",
         shipped=True, check=check_fleet,
         artifacts=("fleet.py", "fleet-msg/SKILL.md", "fleet-sync/SKILL.md", "FLEET.md")),
    Step("gates", "A gate that covered your change", 18,
         "A green run that covered nothing",
         shipped=True, check=check_gates,
         artifacts=("gate-check/SKILL.md", "gate_check.py")),
    Step("floor", "Know your floor", 3,
         "The startup floor is paid on every turn and nobody measures theirs",
         shipped=True, check=check_floor,
         artifacts=("token_audit.py", "settings.template.json", "FLOOR.md")),
    # Last, and the only one that is not about catching something. Every step
    # above it is detection: a guard that runs after something happened. Work
    # that was wrong when it was asked for trips none of them, because there is
    # nothing to catch. It goes at the end because it is the hardest to do
    # honestly, not because it happens last; in the work it happens first.
    Step("plan", "Wrong before you started", 20,
         "Work that was wrong the moment it was asked for passes every other check",
         shipped=True, check=check_plan,
         artifacts=("plan_check.py", "PLAN.md")),
]

BY_ID = dict((s.id, s) for s in STEPS)
SHIPPED = [s for s in STEPS if s.shipped]


def receipt_for(step_id, digest):
    return "{} {} {} PASS {}".format(RECEIPT_PREFIX, RECEIPT_VERSION, step_id, digest)


def run_check(step, root):
    print("")
    print("  {}   (chapter {})".format(step.title, step.chapter))
    print("  {}".format(step.problem))
    print("")

    if not step.shipped:
        print("  NOT SHIPPED YET. Nothing to check.")
        print("  Artifacts when it lands: " + ", ".join(step.artifacts))
        return True

    result = step.check(root)
    for n in result.notes:
        print("    ok    " + n)
    for f in result.failures:
        for i, line in enumerate(f.splitlines()):
            print(("    FAIL  " if i == 0 else "          ") + line)

    print("")
    if result.ok:
        print("  PASS")
        print("  " + receipt_for(step.id, result.digest()))
    else:
        print("  FAIL. Nothing to paste until the above is fixed.")
    return result.ok


def cmd_status(args):
    root = pathlib.Path(args.repo).resolve()
    print("")
    print("  The Build Path, in {}".format(root))
    print("")

    for step in STEPS:
        if not step.shipped:
            mark = "....."
            note = "not shipped yet"
        else:
            result = step.check(root)
            mark = " ok  " if result.ok else "FAIL "
            note = "installed and refusing" if result.ok else result.failures[0].splitlines()[0]
        print("  [{}] {:<8} {:<34} {}".format(mark, step.id, step.title, note))

    print("")
    print("  {} of {} steps have shipped.".format(len(SHIPPED), len(STEPS)))
    print("  Run: glitch check <step>")
    print("")
    return 0


def cmd_check(args):
    root = pathlib.Path(args.repo).resolve()

    if args.all:
        steps = STEPS
    elif args.step in BY_ID:
        steps = [BY_ID[args.step]]
    else:
        print("no such step: {}".format(args.step))
        print("steps: " + ", ".join(s.id for s in STEPS))
        return 2

    results = [run_check(s, root) for s in steps]
    print("")
    return 0 if all(results) else 1


def cmd_install(args):
    """Copy the shipped artifacts into a repository.

    Two things this deliberately does not do.

    It does not write the reader's own files. FLEET.md, FLOOR.md, PLAN.md and
    CLAUDE.md are the work of four of the six steps, and a command that wrote
    them would turn those steps into "you ran an installer". The templates are
    copied to a templates/ folder beside the scripts so they can be read and
    started from, and `check` will still fail until the reader has written the
    real thing. FLOOR.md and PLAN.md ship deliberately unpassable.

    It does not overwrite. An artifact already present is left exactly as it is
    and reported as such, because the file in a reader's repo may be one they
    have edited, and silently replacing it is the kind of irreversible write
    this whole toolkit exists to argue against. --force is the way to say yes.
    """
    root = pathlib.Path(args.repo).resolve()

    if not ASSETS.is_dir():
        print("")
        print("  Nothing to install: this is a bare copy of the checker, not the")
        print("  installed package. `status` and `check` still work.")
        print("")
        return 2

    written, kept = [], []

    def place(src, dest):
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists() and not args.force:
            kept.append(dest.relative_to(root).as_posix())
            return
        if src.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
        else:
            shutil.copy(src, dest)
        written.append(dest.relative_to(root).as_posix())

    for src in sorted((ASSETS / "scripts").glob("*.py")):
        place(src, root / INSTALL_SCRIPTS / src.name)
    for src in sorted(d for d in (ASSETS / "skills").iterdir() if d.is_dir()):
        place(src, root / INSTALL_SKILLS / src.name)
    for src in sorted((ASSETS / "templates").iterdir()):
        place(src, root / INSTALL_TEMPLATES / src.name)

    print("")
    print("  Installed into {}".format(root))
    print("")
    for rel in written:
        print("    wrote  " + rel)
    for rel in kept:
        print("    kept   " + rel + "   (already there; --force to replace)")
    print("")
    print("  Nothing above is a completed step. Four of the six are your own")
    print("  files, and the two templates that would look like a head start")
    print("  are written so they cannot pass.")
    print("")
    print("  Next: glitch status")
    print("")
    print("  The same checks are also available to an agent over MCP, read-only,")
    print("  with every answer appended to a local ledger. It gates nothing and")
    print("  makes no network call. This prints the command rather than running")
    print("  it, because writing to your client's configuration is not something")
    print("  an installer should do on your behalf:")
    print("")
    print("    claude mcp add glitch -- uvx --from 'glitch-toolkit[mcp]' glitch-mcp")
    print("")
    print("  uvx rather than pip: the extra pulls a real dependency tree and pip")
    print("  will upgrade what is already installed to satisfy it.")
    print("")
    return 0


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--repo", default=".", help="the repository to check (default: here)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="what is installed and what is not")

    i = sub.add_parser("install", help="copy the artifacts into this repository")
    i.add_argument("--force", action="store_true", help="replace files that are already there")

    c = sub.add_parser("check", help="verify a step")
    c.add_argument("step", nargs="?", help="step id")
    c.add_argument("--all", action="store_true", help="every step")

    args = ap.parse_args()
    if args.cmd == "install":
        return cmd_install(args)
    if args.cmd == "status":
        return cmd_status(args)
    if args.cmd == "check":
        if not args.step and not args.all:
            print("give a step id, or --all")
            return 2
        return cmd_check(args)
    return 2


if __name__ == "__main__":
    sys.exit(main())
