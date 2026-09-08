"""Check that a rules file contains rules and not moods.

    python rules_check.py check                 # CLAUDE.md here
    python rules_check.py check path/to/FILE
    python rules_check.py check --show          # print what it parsed

A rules file fails quietly. Nothing errors, nothing goes red, and the model
keeps doing the thing you thought you had forbidden. It fails because most of
what people write in one cannot be violated:

    - Write clean, maintainable code.
    - Follow best practices where possible.
    - Be careful with the database.

None of those has a failing case. There is no edit you could make that they
would forbid, so they forbid nothing, and a rule that forbids nothing is a mood
you have written down.

So this asks one question of every rule, and it is not a question about style:
WHAT WOULD BREAK THIS RULE? If you cannot name the edit, the command, the file
or the request that violates it, the rule is not a rule yet. Write the failing
case next to it:

    <!-- rules:start -->
    - Never write a JSON store through a shell text pipeline.
      Violated by: Get-Content data.json | Out-File data.json
    <!-- rules:end -->

The markers are required. Your rules file has other lists in it, and guessing
which bullets were meant as rules is exactly the kind of quiet assumption this
whole toolkit exists to remove.

WHAT THIS CANNOT DO:

  * It cannot tell you whether the failing case you wrote is the right one, or
    whether it is even a real violation of the rule above it. It can only tell
    you that you were made to think about one.
  * The hedge list is a list of words, not comprehension. It catches the common
    ways a rule is softened into advice. It will miss a new one, and it will
    occasionally object to a word you meant literally. Rewrite or move the rule
    outside the markers; do not add the word to your rules to get past this.
  * It does not read your code. Nothing here knows whether you follow the rules
    you wrote.

Standard library only. Reads the file you name and writes nothing.
"""
import argparse
import pathlib
import re
import sys

START = "<!-- rules:start -->"
END = "<!-- rules:end -->"

BULLET = re.compile(r"^\s*[-*]\s+(.*\S)\s*$")
CASE = re.compile(r"^\s+violated by:\s*(.*\S)\s*$", re.I)

# Words and phrases that turn a rule back into advice. A hedged rule cannot be
# violated: whatever you did, it was one of the times the hedge covers. Kept
# deliberately short, because a long list starts objecting to ordinary English.
HEDGES = [
    "where possible",
    "if possible",
    "when possible",
    "as much as possible",
    "try to",
    "as appropriate",
    "when appropriate",
    "if needed",
    "as needed",
    "generally",
    "usually",
    "ideally",
    "best practice",
    "best practices",
    "where it makes sense",
    "etc.",
]

# A rule that says nothing at all. These are the five that appear in almost
# every CLAUDE.md and mean nothing in any of them.
EMPTY = [
    "clean code",
    "readable code",
    "maintainable",
    "idiomatic",
    "well tested",
    "high quality",
    "be careful",
    "use common sense",
]


class Rule:
    def __init__(self, line_no, text):
        self.line_no = line_no
        self.text = text
        self.case = None


def parse(text):
    """Return (rules, error). Everything outside the markers is ignored."""
    lines = text.splitlines()
    start = end = None
    for i, line in enumerate(lines):
        if START in line and start is None:
            start = i
        elif END in line and start is not None and end is None:
            end = i

    if start is None:
        return [], (
            "no rules block. Add the markers around the rules themselves:\n"
            "    {}\n    - your first rule.\n      Violated by: the thing that breaks it\n    {}"
            .format(START, END)
        )
    if end is None:
        return [], "found {} at line {} with no matching {}".format(START, start + 1, END)

    rules = []
    for offset, line in enumerate(lines[start + 1:end]):
        line_no = start + 2 + offset
        m = BULLET.match(line)
        if m:
            rules.append(Rule(line_no, m.group(1)))
            continue
        c = CASE.match(line)
        if c:
            if not rules:
                return [], "line {}: a failing case before any rule".format(line_no)
            if rules[-1].case is not None:
                return [], "line {}: two failing cases for one rule".format(line_no)
            rules[-1].case = c.group(1)
    return rules, None


def judge(rules):
    """Return a list of complaints. Empty means the file holds."""
    out = []
    for rule in rules:
        low = rule.text.lower()

        if rule.case is None:
            out.append((rule.line_no, rule.text, "no failing case. What edit would break this rule?"))
            continue

        hit = [h for h in HEDGES if h in low]
        if hit:
            out.append((rule.line_no, rule.text,
                        "hedged with '{}', so nothing violates it".format(hit[0])))
            continue

        empty = [e for e in EMPTY if e in low]
        if empty:
            out.append((rule.line_no, rule.text,
                        "'{}' is a judgement, not a rule. Name the thing it forbids"
                        .format(empty[0])))
            continue

        if len(rule.case) < 8:
            out.append((rule.line_no, rule.text,
                        "the failing case is too short to be a case: '{}'".format(rule.case)))
    return out


def cmd_check(args):
    path = pathlib.Path(args.path)
    if not path.is_file():
        print("no rules file at {}".format(path))
        print("Point at one: python rules_check.py check path/to/CLAUDE.md")
        return 2

    rules, error = parse(path.read_text(encoding="utf-8", errors="replace"))
    if error:
        print("{}: {}".format(path, error))
        return 1

    if not rules:
        print("{}: the rules block is empty.".format(path))
        print("An empty rules file is not a passing rules file. It is no rules file.")
        return 1

    if args.show:
        for rule in rules:
            print("  {:>4}  {}".format(rule.line_no, rule.text))
            print("        violated by: {}".format(rule.case or "-- nothing --"))

    complaints = judge(rules)
    print("")
    print("{}: {} rule(s) in the block".format(path, len(rules)))

    if not complaints:
        print("every rule names something that would break it.")
        return 0

    print("")
    for line_no, text, why in complaints:
        print("  line {:<5} {}".format(line_no, text[:70]))
        print("            {}".format(why))
    print("")
    print("{} of {} rule(s) cannot be violated. Rewrite them or delete them;".format(
        len(complaints), len(rules)))
    print("a rule nobody can break is not protecting anything.")
    return 1


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="check a rules file")
    c.add_argument("path", nargs="?", default="CLAUDE.md")
    c.add_argument("--show", action="store_true", help="print each rule as it was parsed")
    args = ap.parse_args()
    if args.cmd == "check":
        return cmd_check(args)
    return 2


if __name__ == "__main__":
    sys.exit(main())
