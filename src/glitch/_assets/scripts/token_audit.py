"""Token audit for Claude Code sessions.

Reads the local session transcripts for a project and reports where tokens actually
go, so token decisions are measured instead of guessed.

    python token_audit.py                     # this project, summary table
    python token_audit.py --floor             # what is in the startup floor
    python token_audit.py --top 3             # 3 heaviest sessions, detailed
    python token_audit.py --session ee842ca5  # one session, detailed
    python token_audit.py --project C:/Users/<you>/Desktop/other-repo
    python token_audit.py --transcripts D:/backups/jsonl  # read them from elsewhere
    python token_audit.py --record FLOOR.md   # check the record, measure nothing
    python token_audit.py --table-only        # the table alone, safe to show someone
    python token_audit.py --full-path         # unredacted directory, for a wrong scan

Almost nobody has measured their own floor. They have an impression of it, formed
by watching a bar move, and the impression is usually wrong by a factor. The floor
is the one number where being wrong costs you on every single turn for the life of
the session, which is why it is the number worth having.

Metrics and why each one matters:

  floor        Context tokens on the very first turn: system prompt, tool schemas,
               CLAUDE.md, memory, skills, hook output. Re-read on every later turn,
               so it is a per-turn tax for the life of the session.
  floor share  floor * turns / cache_read. How much of the session's total read
               volume is the immutable floor. A high share means shrink the floor.
  round trips  API responses that used tools. Each one re-reads the whole context,
               so the round trip is the real unit of cost, not the tool call.
  batching     Tool calls per round trip. Independent calls issued together share
               one context read; issued separately they pay for two.
  re-reads     The same file Read more than once. Each re-read appends another full
               copy to the context, which every later turn then re-reads again.

WHAT THIS CANNOT DO:

  * It reads transcripts, so it can only report sessions that have already run.
    A brand new project has nothing to measure yet. Do some work, then measure.
  * Token counts come from what the API reported. The character-based estimates
    for tool results and floor items are estimates, and they are labelled as
    such. Do not quote them to two significant figures.
  * It cannot tell you whether an item in your floor is worth its cost. It can
    only tell you what it costs.
  * If it finds nothing, it says so and exits non-zero. A measuring tool that
    prints a confident zero when it read no data is the false green in
    measurement form.

--record reads a FLOOR.md you already wrote and checks it against what the
transcripts say now. It wants at least two entries, because one measurement is
a reading rather than a record, and it exits non-zero when the record and the
transcripts disagree. It measures nothing new and writes nothing.

--transcripts points at a directory of .jsonl transcripts somewhere other than
the default ~/.claude/projects location, for a machine that keeps them
elsewhere or for reading a copy taken off another machine.

Standard library only. Reads transcripts and writes nothing.
"""

import argparse
import collections
import glob
import json
import os
import re
import sys

CHARS_PER_TOKEN = 3.8  # rough mixed prose+code estimate, used only for tool-result sizing


def project_dir(project_path):
    """Map a working directory to its ~/.claude/projects transcript folder."""
    # Spaces flatten to hyphens too. Leaving that out is the defect Appendix A
    # walks through: every project whose folder name contains a space was told
    # its transcripts did not exist, and the fallback below missed for the same
    # reason, because it compared a spaced tail against a hyphenated folder.
    slug = (project_path.replace(":", "-").replace("\\", "-")
            .replace("/", "-").replace(" ", "-"))
    base = os.path.expanduser("~/.claude/projects")
    exact = os.path.join(base, slug)
    if os.path.isdir(exact):
        return exact
    tail = os.path.basename(project_path.rstrip("/\\")).lower().replace(" ", "-")
    for cand in sorted(glob.glob(os.path.join(base, "*"))):
        if os.path.isdir(cand) and cand.lower().endswith(tail):
            return cand
    # Redacted like every other path this tool prints. This one is easy to miss
    # because it is the failure path, but it is the likeliest of all of them to
    # end up in a screenshot: it fires when someone runs the tool from the wrong
    # directory, which is exactly the moment they go and ask somebody why.
    sys.exit("No transcript directory found for %s" % redact_path(project_path))


def scan(path):
    """One pass over a transcript. Returns a summary dict."""
    s = {
        "turns": 0, "floor": None, "peak": 0,
        "cache_read": 0, "cache_new": 0, "output": 0,
        "calls": collections.Counter(), "result_chars": collections.Counter(),
        "reads": collections.Counter(), "per_response": collections.Counter(),
        "big_results": [], "started": None,
    }
    uses = {}
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                d = json.loads(line)
            except Exception:
                continue

            typ = d.get("type")
            msg = d.get("message") or {}

            if typ == "assistant" and not d.get("isSidechain"):
                usage = msg.get("usage") or {}
                ctx = (usage.get("input_tokens", 0)
                       + usage.get("cache_read_input_tokens", 0)
                       + usage.get("cache_creation_input_tokens", 0))
                if ctx:
                    s["turns"] += 1
                    s["cache_read"] += usage.get("cache_read_input_tokens", 0)
                    s["cache_new"] += usage.get("cache_creation_input_tokens", 0)
                    s["output"] += usage.get("output_tokens", 0)
                    s["peak"] = max(s["peak"], ctx)
                    if s["floor"] is None:
                        s["floor"] = ctx
                        s["started"] = (d.get("timestamp") or "")[:19]

            content = msg.get("content")
            if not isinstance(content, list):
                continue

            if typ == "assistant":
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "tool_use":
                        name = b.get("name", "?")
                        s["calls"][name] += 1
                        # Parallel calls share one API message id. That id is the round trip;
                        # the transcript stores each call as its own record, so counting
                        # records instead of ids reports every session as unbatched.
                        s["per_response"][msg.get("id")] += 1
                        uses[b.get("id")] = name
                        inp = b.get("input") or {}
                        if name == "Read" and inp.get("file_path"):
                            s["reads"][inp["file_path"]] += 1
            else:
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "tool_result":
                        raw = b.get("content")
                        text = raw if isinstance(raw, str) else json.dumps(raw)
                        name = uses.get(b.get("tool_use_id"), "?")
                        s["result_chars"][name] += len(text)
                        if len(text) > 50000:
                            s["big_results"].append((len(text), name))
    return s


def fmt(n):
    return "{:,}".format(int(n))


def report_one(tag, s):
    if not s["turns"]:
        return
    trips = len(s["per_response"])
    calls = sum(s["calls"].values())
    batched = sum(1 for v in s["per_response"].values() if v > 1)
    share = (s["floor"] * s["turns"]) / s["cache_read"] * 100 if s["cache_read"] else 0

    print("\n" + "=" * 78)
    print("session %s   started %s" % (tag, s["started"]))
    print("=" * 78)
    print("  turns %s | floor %s | peak ctx %s"
          % (fmt(s["turns"]), fmt(s["floor"]), fmt(s["peak"])))
    print("  cache_read %s | cache_new %s | output %s"
          % (fmt(s["cache_read"]), fmt(s["cache_new"]), fmt(s["output"])))
    print("  floor share of all reads: %.0f%%   <- shrinking the floor saves this fraction" % share)
    if trips:
        print("  round trips %s for %s tool calls (%.2f per trip); batched %.0f%%"
              % (fmt(trips), fmt(calls), calls / trips, batched / trips * 100))
        print("  each avoided round trip saves ~%s tokens (avg context)"
              % fmt(s["cache_read"] / max(s["turns"], 1)))

    if s["result_chars"]:
        print("\n  heaviest tool results (fed in once, then re-read every later turn):")
        for name, ch in s["result_chars"].most_common(5):
            n = s["calls"][name] or 1
            print("    %-26s %5s calls %9s chars (~%s tok, avg %s)"
                  % (name[:26], fmt(n), fmt(ch), fmt(ch / CHARS_PER_TOKEN), fmt(ch / n)))

    if s["big_results"]:
        print("\n  oversized single results (>50k chars) — these tax every later turn:")
        for size, name in sorted(s["big_results"], reverse=True)[:5]:
            print("    %9s chars (~%s tok)  %s" % (fmt(size), fmt(size / CHARS_PER_TOKEN), name[:40]))

    dupes = [(p, n) for p, n in s["reads"].most_common() if n > 1]
    if dupes:
        wasted = sum((n - 1) for _, n in dupes)
        print("\n  re-read files: %s redundant Read calls across %s files"
              % (fmt(wasted), fmt(len(dupes))))
        for p, n in dupes[:5]:
            print("    %3dx  %s" % (n, p[-64:]))


def _native(path):
    """Translate a git-bash style /c/Users/... path to C:/Users/... so stat works."""
    if len(path) > 2 and path[0] == "/" and path[2] == "/":
        return path[1].upper() + ":" + path[2:]
    return path


def _size(path):
    try:
        return os.path.getsize(_native(path))
    except OSError:
        return 0


def _description_chars(skill_md):
    """Characters of one skill's description, which is what gets injected per session."""
    try:
        text = open(skill_md, encoding="utf-8", errors="replace").read(8000)
    except OSError:
        return 0
    parts = text.split("---")
    front = parts[1] if len(parts) > 2 else text
    start = front.find("description:")
    if start == -1:
        return 0
    chunk = front[start + len("description:"):]
    for stop in ("\nmetadata:", "\nallowed-tools:", "\nname:", "\nmodel:", "\nlicense:"):
        cut = chunk.find(stop)
        if cut != -1:
            chunk = chunk[:cut]
    return len(chunk.strip())


def _skill_descriptions(root, recursive=False):
    """Total characters of skill descriptions under a root, plus a per-skill breakdown."""
    pattern = os.path.join(root, "**", "SKILL.md") if recursive else os.path.join(root, "*", "SKILL.md")
    total, names = 0, []
    for skill in sorted(glob.glob(pattern, recursive=recursive)):
        n = _description_chars(skill)
        if n:
            total += n
            names.append((n, os.path.basename(os.path.dirname(skill))))
    return total, names


def _hook_payloads(settings_path):
    """Hook commands, plus the size of any file a hook cats into the session."""
    out = []
    try:
        cfg = json.load(open(settings_path, encoding="utf-8"))
    except Exception:
        return out
    for event, groups in (cfg.get("hooks") or {}).items():
        for group in groups:
            for hook in group.get("hooks", []):
                cmd = hook.get("command", "")
                payload = 0
                for token in cmd.replace("'", " ").replace('"', " ").split():
                    if ("/" in token or "\\" in token) and os.path.splitext(token)[1]:
                        payload += _size(token)
                out.append((event, cmd, payload, os.path.basename(settings_path)))
    return out


def report_floor(project, latest_floor):
    """Itemise the controllable parts of the startup floor."""
    home = os.path.expanduser("~/.claude")
    slug_dir = project_dir(project)
    print("\n" + "=" * 78)
    print("STARTUP FLOOR INVENTORY")
    print("=" * 78)
    print("The floor is re-read on every turn, so each item below costs its size times")
    print("the session's turn count. Sizes are bytes on disk; tokens are estimated at")
    print("%.1f chars per token.\n" % CHARS_PER_TOKEN)

    items = []
    for label, path in [
        ("project CLAUDE.md", os.path.join(project, "CLAUDE.md")),
        ("user CLAUDE.md", os.path.join(home, "CLAUDE.md")),
        ("MEMORY.md index", os.path.join(slug_dir, "memory", "MEMORY.md")),
    ]:
        n = _size(path)
        if n:
            items.append((n, label, path))

    skill_chars, skill_names = _skill_descriptions(os.path.join(home, "skills"))
    if skill_chars:
        items.append((skill_chars, "global skill descriptions (%d skills)" % len(skill_names),
                      os.path.join(home, "skills")))

    # The marketplace cache under ~/.claude/plugins is only in context if a plugin is
    # actually enabled. Counting it unconditionally overstates the floor by thousands of
    # tokens, so it is reported separately and left out of the attributed total.
    plugin_chars, plugin_names = _skill_descriptions(os.path.join(home, "plugins"), recursive=True)
    enabled = {}
    try:
        cfg = json.load(open(os.path.expanduser("~/.claude.json"), encoding="utf-8"))
        enabled = cfg.get("enabledPlugins") or {}
        for proj, pcfg in (cfg.get("projects") or {}).items():
            if os.path.normcase(proj.rstrip("/\\")) == os.path.normcase(project.rstrip("/\\")):
                enabled.update(pcfg.get("enabledPlugins") or {})
    except Exception:
        pass
    if plugin_chars and enabled:
        items.append((plugin_chars, "plugin skill descriptions (%d skills)" % len(plugin_names),
                      os.path.join(home, "plugins")))
        plugin_chars = 0

    hooks = []
    for settings in [os.path.join(home, "settings.json"),
                     os.path.join(project, ".claude", "settings.json"),
                     os.path.join(project, ".claude", "settings.local.json")]:
        hooks.extend(_hook_payloads(settings))
    for event, cmd, payload, src in hooks:
        if payload:
            items.append((payload, "%s hook payload (%s)" % (event, src), cmd[:60]))

    items.sort(reverse=True)
    attributed = 0
    print("%-52s %10s %10s" % ("item", "bytes", "~tokens"))
    for n, label, _ in items:
        attributed += n
        print("%-52s %10s %10s" % (label[:52], fmt(n), fmt(n / CHARS_PER_TOKEN)))

    if plugin_chars:
        print("\n%-52s %10s %10s" % ("(marketplace cache, no plugin enabled: not loaded)",
                                     fmt(plugin_chars), fmt(plugin_chars / CHARS_PER_TOKEN)))

    print("\n%-52s %10s %10s" % ("attributed (yours to control)", fmt(attributed),
                                 fmt(attributed / CHARS_PER_TOKEN)))
    if latest_floor:
        est = attributed / CHARS_PER_TOKEN
        print("%-52s %10s %10s" % ("measured floor, most recent session", "", fmt(latest_floor)))
        print("%-52s %10s %10s" % ("remainder: system prompt + tool schemas + MCP", "",
                                   fmt(max(latest_floor - est, 0))))
        print("\nControllable share of the floor: %.0f%%" % (est / latest_floor * 100))

    if skill_names:
        print("\nGlobal skills load in EVERY project, relevant or not:")
        for n, name in sorted(skill_names, reverse=True):
            print("   %6s ch  %s" % (fmt(n), name))
        print("   Move project-specific skills into that project's .claude/skills/ to drop them here.")

    if hooks:
        print("\nHooks firing in this project:")
        for event, cmd, payload, src in hooks:
            note = ("  <- injects %s bytes" % fmt(payload)) if payload else ""
            print("   %-18s %s%s" % (event, cmd[:52], note))


RECORD = re.compile(r"floor[^0-9\n]{0,40}([0-9][0-9,_ ]*)", re.I)
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def check_record(path):
    """Read a floor record and refuse it if it is not a record of two measurements.

    Measuring once tells you a number. The work is measuring, cutting, and
    measuring again, and a record with one entry is the half of that which
    nobody skips. So one entry is not enough, and neither is a number with no
    date on it: a floor from an unknown week describes a project that has since
    changed.
    """
    if not os.path.isfile(path):
        print("no floor record at %s" % path)
        print("A number you measured and did not write down is a number you will")
        print("measure again next month. Keep it where you will see it.")
        return 1

    entries = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for i, line in enumerate(fh, 1):
            m = RECORD.search(line)
            if not m:
                continue
            d = DATE.search(line)
            if not d:
                print("line %d has a floor with no date: %s" % (i, line.strip()[:70]))
                return 1
            value = int(m.group(1).replace(",", "").replace("_", "").replace(" ", ""))
            if value < 1:
                print("line %d records a floor of zero. Nothing has a floor of zero." % i)
                return 1
            entries.append((d.group(0), value, i))

    if len(entries) < 2:
        print("%s holds %d measurement(s)." % (path, len(entries)))
        print("A floor record needs at least two: what it was, and what it is after")
        print("you cut something. One measurement is an observation, not a change.")
        print("Each line needs a number and a date, like:")
        print("    2026-01-14  floor 31,400 tokens  (before)")
        return 1

    print("")
    print("%s: %d measurements" % (path, len(entries)))
    for when, value, _ in entries:
        print("   %s  %s tokens" % (when, fmt(value)))
    first, last = entries[0][1], entries[-1][1]
    delta = first - last
    if delta > 0:
        print("   cut %s tokens off every turn since the first measurement." % fmt(delta))
    elif delta == 0:
        print("   unchanged since the first measurement.")
    else:
        print("   the floor has grown by %s tokens since the first measurement." % fmt(-delta))
    print("")
    return 0


def redact_path(p):
    """Make a transcript directory printable in front of other people.

    The directory Claude Code keeps transcripts in is named after the absolute
    path of the project, so on this machine it reads
    C--Users-<you>-Desktop-Abstract-Glitch. That is a username, a project name
    and the fact it sits on the Desktop, and the whole point of this tool is
    that its output gets pasted into threads and screenshots. Redacting by
    default costs a user nothing, because they already know where their own
    projects live, and --full-path gives it back when the question is why the
    scan pointed somewhere unexpected.
    """
    home = os.path.expanduser("~")
    base, name = os.path.split(p.rstrip("/\\"))
    if base.replace("\\", "/").rstrip("/").endswith(".claude/projects"):
        name = "<project>"
    shown = os.path.join(base, name)
    if shown.startswith(home):
        shown = "~" + shown[len(home):]
    return shown.replace("\\", "/")


def main():
    ap = argparse.ArgumentParser(description="Measure where a project's Claude Code tokens go.")
    ap.add_argument("--project", default=os.getcwd())
    ap.add_argument("--transcripts", help="scan this directory of .jsonl transcripts directly")
    ap.add_argument("--record", help="check a floor record file and exit, measuring nothing")
    ap.add_argument("--session", help="session id prefix for a detailed single report")
    ap.add_argument("--top", type=int, default=0, help="detail the N heaviest sessions")
    ap.add_argument("--limit", type=int, default=40, help="how many recent sessions to scan")
    ap.add_argument("--floor", action="store_true",
                    help="itemise the startup floor: what is in it and what you control")
    ap.add_argument("--table-only", action="store_true", dest="table_only",
                    help="print the session table and stop, with no totals underneath it")
    ap.add_argument("--full-path", action="store_true", dest="full_path",
                    help="print the transcript directory unredacted, for debugging a wrong scan")
    args = ap.parse_args()

    if args.record:
        return check_record(args.record)

    d = args.transcripts if args.transcripts else project_dir(args.project)
    shown = d if args.full_path else redact_path(d)
    if not os.path.isdir(d):
        print("no transcript directory at %s" % shown)
        return 1
    files = sorted(glob.glob(os.path.join(d, "*.jsonl")), key=os.path.getmtime, reverse=True)

    if args.session:
        match = [f for f in files if os.path.basename(f).startswith(args.session)]
        if not match:
            print("no session starting with %s" % args.session)
            return 1
        s = scan(match[0])
        if not s["turns"]:
            print("session %s has no turns to measure." % args.session)
            return 1
        report_one(args.session, s)
        return 0

    files = files[:args.limit]
    print("scanning %d sessions in %s\n" % (len(files), shown))
    print("%-10s %7s %9s %9s %14s %7s %7s"
          % ("session", "turns", "floor", "peak", "cache_read", "trips", "batch%"))
    rows = []
    for f in files:
        s = scan(f)
        if not s["turns"]:
            continue
        tag = os.path.basename(f)[:8]
        trips = len(s["per_response"])
        batched = sum(1 for v in s["per_response"].values() if v > 1)
        rows.append((tag, s))
        print("%-10s %7s %9s %9s %14s %7s %7s" % (
            tag, fmt(s["turns"]), fmt(s["floor"]), fmt(s["peak"]), fmt(s["cache_read"]),
            fmt(trips), ("%.0f%%" % (batched / trips * 100)) if trips else "-"))

    if not rows:
        # The refusal. Printing an empty table and exiting 0 would look exactly
        # like a project whose floor is nothing, which is the one answer that is
        # never true. A measuring tool that reports success on no data is the
        # false green wearing a different hat.
        print("")
        print("nothing measured. %d transcript file(s) in %s, none with a usable turn."
              % (len(files), shown))
        print("Either this project has no sessions yet, or --project points somewhere")
        print("that is not it. Do some work in it, then measure.")
        return 1

    if args.table_only:
        # The table is billed figures and nothing else. Everything below this
        # point either projects a saving that did not happen or prints a share
        # that reads like "the percentage" to someone seeing one for the first
        # time, and there are already several of those in circulation. This flag
        # exists so output can be shown to someone without either.
        return 0

    if rows:
        tot_read = sum(s["cache_read"] for _, s in rows)
        tot_turns = sum(s["turns"] for _, s in rows)
        floors = [s["floor"] for _, s in rows]
        floor_cost = sum(s["floor"] * s["turns"] for _, s in rows)
        print("\ntotals across %d sessions: %s cache-read tokens, %s turns"
              % (len(rows), fmt(tot_read), fmt(tot_turns)))
        print("floor range %s to %s tokens; floor accounts for %s tokens = %.0f%% of all reads"
              % (fmt(min(floors)), fmt(max(floors)), fmt(floor_cost),
                 floor_cost / tot_read * 100 if tot_read else 0))
        print("cutting 10k from the floor would have saved ~%s tokens across these sessions"
              % fmt(10000 * tot_turns))

    if args.floor:
        # rows are in most-recent-first order, so rows[0] is the newest real session
        report_floor(args.project, rows[0][1]["floor"] if rows else None)

    for tag, s in sorted(rows, key=lambda r: -r[1]["cache_read"])[:args.top]:
        report_one(tag, s)

    return 0


if __name__ == "__main__":
    sys.exit(main())
