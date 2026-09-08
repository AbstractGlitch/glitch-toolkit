"""Check that a plan of record was actually written, not just started.

    python plan_check.py check                  # PLAN.md here
    python plan_check.py check path/to/FILE
    python plan_check.py check --show           # print what it parsed

Every other guard in this toolkit catches work that went wrong. None of them
catches work that was wrong from the moment it was asked for, because there is
nothing to catch: it passes every test, every lane check and every gate, and you
find out weeks later that you built the wrong thing correctly.

A plan is the only thing that catches that, and only if it says three things
before the work starts:

  * what you are NOT doing, which is the half nobody writes
  * who approved it and when, which is what makes it a decision rather than a note
  * how you will know it worked, written while you still want it to be hard

So this reads a plan and refuses the four ways one gets written without being
written. A plan with no not-doing list has not been scoped. A plan approved by
nobody, or approved by the same person who wrote it, records agreement with
yourself. A verification line that cannot fail is the false green from Chapter
18 arriving a week earlier. And a template still full of angle brackets is a
file, not a plan.

WHAT THIS CANNOT DO:

  * It cannot tell you the plan is any good. It checks that the questions were
    answered, never that the answers were right. A confidently wrong plan that
    fills in every section passes this cleanly.
  * It cannot tell whether the person on the Approved line read it. That failure
    is named in the template itself and no script reaches it.
  * It does not know whether the work matches the plan. Nothing here reads your
    diff. That disagreement is what the deviation log is for, and a deviation
    nobody writes down is invisible to this too.
  * The weak-verification list is a list of phrases, not comprehension. It
    catches the common ways a check is written so it can never fail. It will
    miss a new one.

Standard library only. Reads the file you name and writes nothing.
"""
import argparse
import pathlib
import re
import sys

# The sections a plan has to have. Matched on the heading text rather than the
# exact level, because people renumber headings and that is not a defect.
NOT_DOING = "what we are not doing"
ARE_DOING = "what we are doing"
HOW_WE_KNOW = "how we will know it worked"

DEV_START = "<!-- deviations:start -->"
DEV_END = "<!-- deviations:end -->"

HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.*\S)\s*$")
BULLET = re.compile(r"^\s*[-*]\s+(.*\S)\s*$")
WRITTEN = re.compile(r"^\s*\*\*Written\*\*\s*(.*\S)\s*$", re.I)
APPROVED = re.compile(r"^\s*\*\*Approved\*\*\s*(.*\S)\s*$", re.I)
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")

# An unfilled slot from the template. Two characters minimum so a stray "<" in
# prose, or a comparison like "a < b", is not read as a placeholder.
PLACEHOLDER = re.compile(r"<[^<>]{2,}>")

# " 2026-08-27 by Someone " -> the name half. The template puts a parenthetical
# after the name on the Approved line, so anything from the first comma on is
# dropped before the two names are compared.
BY = re.compile(r"\bby\b\s*(.+)$", re.I)

# Ways of writing a check so that it cannot fail. Chapter 18's argument, moved
# a week earlier: "tests pass" is satisfied by a suite that covered nothing,
# and every phrase here is satisfied by doing nothing carefully.
WEAK = [
    "tests pass",
    "test pass",
    "it works",
    "everything works",
    "works as expected",
    "works correctly",
    "no errors",
    "no bugs",
    "nothing breaks",
    "looks right",
    "looks good",
    "seems fine",
    "is done",
    "is complete",
    "is finished",
    "code review",
    "manual check",
    "we are happy with it",
]

# Softeners. Same argument as the hedge list in rules_check.py: a hedged check
# is satisfied by whatever happened, because that was one of the times the
# hedge covered.
HEDGES = [
    "where possible",
    "if possible",
    "as appropriate",
    "if needed",
    "as needed",
    "generally",
    "usually",
    "ideally",
    "mostly",
    "roughly",
    "should be fine",
    "etc.",
]


class Plan:
    def __init__(self):
        self.written = None      # (line_no, text)
        self.approved = None     # (line_no, text)
        self.not_doing = []      # [(line_no, text)]
        self.are_doing = []
        self.checks = []
        self.deviations = []     # raw lines inside the markers
        self.has_dev_block = False


def _name(text):
    """The who half of 'DATE by WHO', lowercased, first clause only."""
    m = BY.search(text or "")
    if not m:
        return None
    who = m.group(1).strip().strip(".")
    who = who.split(",")[0].strip()
    return who.lower() or None


def parse(text):
    """Return (plan, error). Sections are found by heading, not by position."""
    lines = text.splitlines()
    plan = Plan()
    section = None
    in_dev = False

    for i, line in enumerate(lines):
        line_no = i + 1

        if DEV_START in line:
            in_dev = True
            plan.has_dev_block = True
            continue
        if DEV_END in line:
            in_dev = False
            continue
        if in_dev:
            if line.strip():
                plan.deviations.append(line.rstrip())
            continue

        h = HEADING.match(line)
        if h:
            title = h.group(1).strip().lower().rstrip(":")
            if title.startswith(NOT_DOING):
                section = "not"
            elif title.startswith(ARE_DOING):
                section = "are"
            elif title.startswith(HOW_WE_KNOW):
                section = "how"
            else:
                section = None
            continue

        w = WRITTEN.match(line)
        if w and plan.written is None:
            plan.written = (line_no, w.group(1))
            continue
        a = APPROVED.match(line)
        if a and plan.approved is None:
            plan.approved = (line_no, a.group(1))
            continue

        b = BULLET.match(line)
        if b and section:
            entry = (line_no, b.group(1))
            if section == "not":
                plan.not_doing.append(entry)
            elif section == "are":
                plan.are_doing.append(entry)
            else:
                plan.checks.append(entry)

    if plan.written is None and plan.approved is None and not plan.not_doing:
        return None, (
            "this does not look like a plan. Expected a **Written** line, an\n"
            "**Approved** line, and a 'What we are NOT doing' section. Start from\n"
            "the PLAN.md template rather than from a blank file."
        )
    return plan, None


def judge(plan):
    """Return a list of (line_no, subject, why). Empty means the plan holds."""
    out = []

    # 1. Approval. A plan approved by nobody is a note, and a plan approved by
    #    its own author is a note with a second date on it.
    for label, entry in (("Written", plan.written), ("Approved", plan.approved)):
        if entry is None:
            out.append((0, label, "there is no **{}** line. A plan with no {} date and no\n"
                                  "            name is a draft that will be followed anyway."
                        .format(label, label.lower())))
            continue
        line_no, text = entry
        if not DATE.search(text):
            out.append((line_no, label, "no date in YYYY-MM-DD. An undated plan is a claim, not\n"
                                        "            an instruction, and it never expires on its own."))
        if not _name(text):
            out.append((line_no, label, "no name after 'by'. Somebody has to be the person who\n"
                                        "            said yes."))

    if plan.written and plan.approved:
        one, two = _name(plan.written[1]), _name(plan.approved[1])
        if one and two and one == two:
            out.append((plan.approved[0], "Approved",
                        "the same person wrote and approved this. Approval by the\n"
                        "            author is agreement with yourself, which is the state you\n"
                        "            were already in."))

    # 2. The not-doing list. First in the template on purpose, and the half a
    #    session cannot infer from anything else in the repository.
    real_not = [e for e in plan.not_doing if not PLACEHOLDER.search(e[1])]
    if not plan.not_doing:
        out.append((0, "What we are NOT doing",
                    "the section is empty. Scope is the half of a plan that gets\n"
                    "            skipped, and it is the only part you can write with real\n"
                    "            confidence on a bad day."))
    elif not real_not:
        out.append((plan.not_doing[0][0], "What we are NOT doing",
                    "every entry is still the template's angle brackets."))
    elif len(real_not) < 2:
        out.append((real_not[0][0], "What we are NOT doing",
                    "one entry. A scope list with one line has not met reality yet;\n"
                    "            name the thing somebody will ask about."))

    # 3. The work.
    real_doing = [e for e in plan.are_doing if not PLACEHOLDER.search(e[1])]
    if not real_doing:
        out.append((plan.are_doing[0][0] if plan.are_doing else 0, "What we ARE doing",
                    "nothing here that is not a placeholder."))

    # 4. Verification. The reason this file is checked at all: these are written
    #    before the work, while you still want them to be hard.
    real_checks = [e for e in plan.checks if not PLACEHOLDER.search(e[1])]
    if not plan.checks:
        out.append((0, "How we will know it worked",
                    "the section is empty. A plan with no verification is a wish\n"
                    "            with stages."))
    elif not real_checks:
        out.append((plan.checks[0][0], "How we will know it worked",
                    "every check is still the template's angle brackets."))
    else:
        for line_no, text in real_checks:
            low = text.lower()
            weak = [w for w in WEAK if w in low]
            if weak:
                out.append((line_no, text,
                            "'{}' cannot fail in a way you would notice. Name what\n"
                            "            runs and what it would say when it is wrong."
                            .format(weak[0])))
                continue
            hedge = [h for h in HEDGES if h in low]
            if hedge:
                out.append((line_no, text,
                            "hedged with '{}', so whatever happened satisfies it."
                            .format(hedge[0])))

    # 5. The deviation log. Optional to have entries, not optional to have been
    #    emptied of the example.
    if plan.has_dev_block:
        left = [ln for ln in plan.deviations if PLACEHOLDER.search(ln)]
        if left:
            out.append((0, "Deviations",
                        "the template's example deviation is still in the log. Clear\n"
                        "            the block, or the first real deviation lands underneath a\n"
                        "            fake one."))

    return out


def cmd_check(args):
    path = pathlib.Path(args.path)
    if not path.is_file():
        print("no plan at {}".format(path))
        print("Point at one: python plan_check.py check path/to/PLAN.md")
        return 2

    plan, error = parse(path.read_text(encoding="utf-8", errors="replace"))
    if error:
        print("{}: {}".format(path, error))
        return 1

    if args.show:
        for label, entry in (("written", plan.written), ("approved", plan.approved)):
            print("  {:>9}  {}".format(label, entry[1] if entry else "-- missing --"))
        for label, items in (("not doing", plan.not_doing),
                             ("doing", plan.are_doing),
                             ("checks", plan.checks)):
            print("  {:>9}  {} entr{}".format(label, len(items), "y" if len(items) == 1 else "ies"))
            for line_no, text in items:
                print("             {:>4}  {}".format(line_no, text[:66]))

    complaints = judge(plan)
    print("")
    print("{}: {} not-doing, {} doing, {} check(s)".format(
        path, len(plan.not_doing), len(plan.are_doing), len(plan.checks)))

    if not complaints:
        print("this plan says what it is not doing, who approved it, and how it can fail.")
        return 0

    print("")
    for line_no, subject, why in complaints:
        where = "line {:<5}".format(line_no) if line_no else "          "
        print("  {} {}".format(where, str(subject)[:66]))
        print("            {}".format(why))
    print("")
    print("{} thing(s) a plan has to answer are not answered here.".format(len(complaints)))
    print("A plan you filled in halfway still gets cited later as though you had not.")
    return 1


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="check a plan of record")
    c.add_argument("path", nargs="?", default="PLAN.md")
    c.add_argument("--show", action="store_true", help="print what was parsed")
    args = ap.parse_args()
    return cmd_check(args)


if __name__ == "__main__":
    sys.exit(main())
