"""Lane claims for a repo that several Claude sessions share.

The failure this exists for: two sessions edit the same file, the second write
wins, there is no conflict and no error, and the lost work reads to you as a
completed task. You find out days later, or never.

Claims live one-file-per-lane under .claude/lanes/ so two sessions writing
claims at the same moment never touch the same file. A shared claims file would
race, which is the bug we are here to avoid.

    python check_lanes.py claim backend app/main.py app/routes/*.py
    python check_lanes.py check app/main.py      # before you edit
    python check_lanes.py status
    python check_lanes.py release backend

Honest limits, stated up front:
  * This cannot see other sessions. It sees claims they wrote and mtimes on
    disk. A session that never claims anything is invisible to it.
  * mtime evidence is advisory. A recent mtime means someone touched the file,
    not necessarily that they are still in it.
  * It does not lock anything. It tells you; you decide.
"""
# Lazy annotations, so this file imports on Python 3.9.
#
# The signatures below use `X | None`, which is PEP 604 and needs 3.10. A def's
# annotations are evaluated when the def runs, so without this line the module
# raises TypeError at IMPORT on 3.9 — not at call, which is why it looked fine
# to anyone reading it. CI caught it on the floor version the first time it ran.
#
# This is a shipped artifact: it gets copied into a reader's repository and run
# with THEIR interpreter, which `requires-python` does not govern. So it should
# import as far back as it can rather than as far back as the installer allows.
from __future__ import annotations

import argparse
import fnmatch
import glob
import json
import os
import pathlib
import socket
import sys
import time

LANES_DIR = pathlib.Path(".claude/lanes")
STALE_HOURS = 4.0        # a claim older than this is suspect, see status output
RECENT_EDIT_MINUTES = 30  # mtime inside this window is worth warning about


def _now() -> float:
    return time.time()


def _lane_files() -> list[pathlib.Path]:
    return sorted(LANES_DIR.glob("*.json")) if LANES_DIR.exists() else []


def _load(p: pathlib.Path) -> dict | None:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _expand(patterns: list[str]) -> list[str]:
    """Globs are resolved at claim time so a claim names real files."""
    out = []
    for pat in patterns:
        hits = glob.glob(pat, recursive=True)
        out.extend(hits if hits else [pat])
    return sorted({os.path.normpath(p).replace("\\", "/") for p in out})


def _matches(claimed: str, target: str) -> bool:
    t = os.path.normpath(target).replace("\\", "/")
    return t == claimed or fnmatch.fnmatch(t, claimed) or t.startswith(claimed.rstrip("/") + "/")


def _age(ts: float) -> str:
    m = (_now() - ts) / 60
    if m < 60:
        return f"{m:.0f}m ago"
    return f"{m / 60:.1f}h ago"


def cmd_claim(args) -> int:
    LANES_DIR.mkdir(parents=True, exist_ok=True)
    paths = _expand(args.paths)

    conflicts = _conflicts(paths, skip_lane=args.lane)
    if conflicts and not args.force:
        print("REFUSED. Another lane already claims these:")
        for path, lane, ts in conflicts:
            print(f"  {path}  ->  lane '{lane}' (claimed {_age(ts)})")
        print("\nTalk to that lane, or re-run with --force if you know it is stale.")
        return 1

    dest = LANES_DIR / f"{args.lane}.json"
    dest.write_text(json.dumps({
        "lane": args.lane,
        "paths": paths,
        "claimed_at": _now(),
        "host": socket.gethostname(),
        "pid": os.getpid(),
        "note": args.note or "",
    }, indent=2), encoding="utf-8")

    print(f"claimed {len(paths)} path(s) for lane '{args.lane}'")
    for p in paths:
        print(f"  {p}")
    if conflicts:
        print("\nforced past these conflicts:")
        for path, lane, _ in conflicts:
            print(f"  {path} (lane '{lane}')")
    return 0


def _conflicts(paths: list[str], skip_lane: str | None) -> list[tuple[str, str, float]]:
    found = []
    for lf in _lane_files():
        data = _load(lf)
        if not data or data.get("lane") == skip_lane:
            continue
        for claimed in data.get("paths", []):
            for target in paths:
                if _matches(claimed, target) or _matches(target, claimed):
                    found.append((target, data["lane"], data.get("claimed_at", 0)))
    return found


def cmd_check(args) -> int:
    paths = _expand(args.paths)
    problems = 0

    conflicts = _conflicts(paths, skip_lane=args.lane)
    if conflicts:
        problems += len(conflicts)
        print("CLAIMED BY ANOTHER LANE:")
        for path, lane, ts in conflicts:
            stale = " [STALE]" if (_now() - ts) / 3600 > STALE_HOURS else ""
            print(f"  {path}  ->  lane '{lane}' (claimed {_age(ts)}){stale}")

    # mtime evidence catches the session that never claimed anything.
    cutoff = _now() - RECENT_EDIT_MINUTES * 60
    recent = []
    for p in paths:
        fp = pathlib.Path(p)
        if fp.is_file() and fp.stat().st_mtime > cutoff:
            recent.append((p, fp.stat().st_mtime))
    if recent:
        problems += len(recent)
        print("\nRECENTLY MODIFIED (someone may be in these right now):")
        for p, ts in sorted(recent, key=lambda x: -x[1]):
            print(f"  {p}  modified {_age(ts)}")

    if not problems:
        print(f"clear: {len(paths)} path(s), no claims and no recent edits")
        return 0

    print(f"\n{problems} warning(s). Confirm before editing.")
    return 1


def cmd_status(args) -> int:
    lanes = _lane_files()
    if not lanes:
        print("no lanes claimed")
        return 0

    print(f"{len(lanes)} lane(s):\n")
    for lf in lanes:
        data = _load(lf)
        if not data:
            print(f"  {lf.name}: UNREADABLE")
            continue
        ts = data.get("claimed_at", 0)
        hrs = (_now() - ts) / 3600
        flag = "  <- STALE, release it or refresh it" if hrs > STALE_HOURS else ""
        print(f"  {data['lane']}  ({_age(ts)}, {len(data.get('paths', []))} paths){flag}")
        if data.get("note"):
            print(f"      note: {data['note']}")
        for p in data.get("paths", [])[:8]:
            print(f"      {p}")
        if len(data.get("paths", [])) > 8:
            print(f"      ... and {len(data['paths']) - 8} more")
        print()

    print("A stale claim is not harmlessly cautious. It makes other lanes route")
    print("around files that are actually free.")
    return 0


def cmd_release(args) -> int:
    dest = LANES_DIR / f"{args.lane}.json"
    if not dest.exists():
        print(f"no claim for lane '{args.lane}'")
        return 1
    dest.unlink()
    print(f"released lane '{args.lane}'")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("claim", help="claim paths for a lane")
    c.add_argument("lane")
    c.add_argument("paths", nargs="+")
    c.add_argument("--note", default="")
    c.add_argument("--force", action="store_true")
    c.set_defaults(fn=cmd_claim)

    k = sub.add_parser("check", help="check paths before editing")
    k.add_argument("paths", nargs="+")
    k.add_argument("--lane", default=None, help="your own lane, excluded from conflicts")
    k.set_defaults(fn=cmd_check)

    s = sub.add_parser("status", help="show all claims")
    s.set_defaults(fn=cmd_status)

    r = sub.add_parser("release", help="release a lane")
    r.add_argument("lane")
    r.set_defaults(fn=cmd_release)

    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
