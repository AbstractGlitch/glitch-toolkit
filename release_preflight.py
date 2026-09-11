"""Check that a release is ready to be uploaded, from wherever you are standing.

    python release_preflight.py
    python release_preflight.py --dist ~/Downloads   # artefacts not in ./dist

This exists because the handover for 0.1.4 failed on all three of its commands,
run from C:\\WINDOWS\\System32:

    twine upload dist/*   -> Cannot find file (or expand pattern): 'dist/*'
    git subtree push ...  -> fatal: not a git repository
    mcp-publisher publish -> The term 'mcp-publisher' is not recognized

One cause. The commands assumed a working directory and assumed installed
tooling, and nothing checked either. RELEASING.md has always had that shape and
it worked for three releases because the same person ran it from the same folder
each time. That is a habit, not a guarantee, and the first time it was written
down for somebody else it broke immediately.

So this answers the questions the command list assumed: where am I, do the four
version numbers agree, are the artefacts here and are they the ones that were
checked, is the tooling installed, and is this version already on the index. It
prints the commands afterwards with every path resolved.

WHAT THIS DOES NOT DO:

  * It does not upload, push, or publish anything. Publishing is a deliberate
    act and RELEASING.md is right to keep it one. This tells you that you are
    ready; you decide to go.
  * It does not check that the artefacts are GOOD. `twine check` does that, and
    the test suite does the rest. This checks they are PRESENT and that they are
    the version the tree says they are.
  * It cannot tell you where to download mcp-publisher. The machine this was
    written on cannot reach that host, and an unverified URL inside a release
    script would be exactly the substitution of description for thing that the
    rest of this package is about.
  * Its index check needs the network. Blocked or offline is reported as
    unknown, never as a pass.

Standard library only, like everything else that ships here.
"""
import argparse
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys

DIST = "glitch-toolkit"
INDEX = "https://pypi.org/pypi/{}/json".format(DIST)

# The four places a version lives. RELEASING.md named three of them for three
# releases; src/glitch/__init__.py was found by reading the workflow that
# asserts it, not the checklist that is supposed to list it.
VERSION_FILES = ("pyproject.toml", "src/glitch/__init__.py", "registry/server.json", "README.md")


class Report:
    def __init__(self):
        self.problems = []
        self.unknown = []

    def ok(self, line):
        print("  ok       " + line)

    def fail(self, line):
        self.problems.append(line)
        print("  MISSING  " + line)

    def unsure(self, line):
        self.unknown.append(line)
        print("  ?        " + line)


def repo_root(start):
    """Where the checkout is, asked of git rather than guessed from the path."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(start), capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return pathlib.Path(out.stdout.strip())


def read_versions(pkg):
    """Every version in the tree, by file. Missing reads as None, never as agreement."""
    found = {}

    proj = pkg / "pyproject.toml"
    m = re.search(r'^version\s*=\s*"([^"]+)"', proj.read_text(encoding="utf-8"), re.M) if proj.is_file() else None
    found["pyproject.toml"] = m.group(1) if m else None

    init = pkg / "src" / "glitch" / "__init__.py"
    m = re.search(r'^__version__\s*=\s*"([^"]+)"', init.read_text(encoding="utf-8"), re.M) if init.is_file() else None
    found["src/glitch/__init__.py"] = m.group(1) if m else None

    entry = pkg / "registry" / "server.json"
    if entry.is_file():
        data = json.loads(entry.read_text(encoding="utf-8"))
        found["registry/server.json"] = data.get("version")
        found["_server_name"] = data.get("name")
        found["_package_versions"] = [p.get("version") for p in data.get("packages", [])]
    else:
        found["registry/server.json"] = None
        found["_server_name"] = None
        found["_package_versions"] = []

    return found


def check_versions(pkg, r):
    """Agreement, and the marker. Returns the version if everything agrees."""
    found = read_versions(pkg)
    named = [(f, found.get(f)) for f in VERSION_FILES if f != "README.md"]

    for label, value in named:
        if value is None:
            r.fail("{} has no version in it".format(label))

    values = {v for _, v in named if v is not None}
    if len(values) > 1:
        r.fail("the version disagrees: " + ", ".join(
            "{} says {}".format(l, v) for l, v in named))
        return None
    if not values:
        return None
    version = values.pop()

    for pv in found["_package_versions"]:
        if pv != version:
            r.fail("a package entry in registry/server.json says {} and the tree says {}".format(pv, version))
            return None

    # The marker. A one-character casing error here cost two releases, so it is
    # compared against server.json's own name rather than against a constant
    # written here, which would be a third place to get it wrong.
    name = found["_server_name"]
    readme = pkg / "README.md"
    if not name:
        r.fail("registry/server.json has no name, so the marker cannot be checked")
        return None
    if not readme.is_file():
        r.fail("README.md is not there, and it is the marker's only home")
        return None
    if ("mcp-name: " + name) not in readme.read_text(encoding="utf-8"):
        r.fail("README.md carries no 'mcp-name: {}' marker, so the registry cannot verify the namespace".format(name))
        return None

    r.ok("all four version numbers say {}, and the mcp-name marker matches {}".format(version, name))
    return version


def find_dist(pkg, given):
    """Where the artefacts are. Named directory first, then the usual place."""
    if given:
        d = pathlib.Path(given).expanduser()
        return d if d.is_dir() else None
    d = pkg / "dist"
    return d if d.is_dir() else None


def recorded_hashes(pkg, version):
    """The hashes RELEASING.md wrote down for this version, or None.

    The file records them as:  - `name` -- N bytes, sha256 `hex`
    under a '### The artefacts' heading, written from an actual build. Parsing
    them here means the artefacts are compared against something in the
    repository rather than against a number somebody reads off the screen and
    eyeballs, which is the whole difference between a check and a habit.

    Returns None when the block is missing or names a different version. That is
    deliberately not the same answer as "they match": a release whose artefacts
    nobody recorded is a release nobody checked, and the caller reports it as
    unknown rather than passing it.
    """
    path = pkg / "RELEASING.md"
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    found = {}
    for m in re.finditer(
        r"^-\s+`([^`]+)`\s+[^`\n]*?sha256\s+`([0-9a-f]{64})`\s*$", text, re.M
    ):
        name, digest = m.group(1), m.group(2)
        if version in name:
            found[name] = digest
    return found or None


def describe(directory):
    """What is in a directory, without reciting it.

    The first version of this printed every filename so the reader was not left
    guessing. Against glitch/dist/ that is two lines. Run against a real
    downloads folder on 2026-09-11 it was seventy-odd names, printed four times,
    and it put the names of unrelated personal files into a terminal and from
    there into a transcript. Unreadable, and a diagnostic that recites its
    surroundings is worse than one that says less.

    So: only files that look like this distribution, at most five, and a count
    for the rest. Nothing else is named.
    """
    try:
        files = [p.name for p in directory.iterdir() if p.is_file()]
    except OSError as error:
        return "could not be read ({})".format(type(error).__name__)
    if not files:
        return "it is empty"
    ours = sorted(f for f in files if f.startswith(DIST.replace("-", "_")))
    if not ours:
        return "it holds {} file(s), none of them a {} build".format(len(files), DIST)
    shown = ours[:5]
    tail = "" if len(ours) <= 5 else ", and {} more".format(len(ours) - 5)
    return "it holds: {}{}".format(", ".join(shown), tail)


def check_artefacts(pkg, directory, version, r):
    if directory is None:
        r.fail("no artefacts directory. Build with 'python -m build', or pass --dist <path> "
               "if you downloaded them somewhere else")
        return []

    wheel = "{}-{}-py3-none-any.whl".format(DIST.replace("-", "_"), version)
    sdist = "{}-{}.tar.gz".format(DIST.replace("-", "_"), version)

    # Computed once, not once per missing artefact.
    inventory = describe(directory)
    expected = recorded_hashes(pkg, version)

    out = []
    for name in (wheel, sdist):
        path = directory / name
        if not path.is_file():
            r.fail("{} is not in {} -- {}".format(name, directory, inventory))
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if expected is None:
            r.unsure("{} is here, but RELEASING.md records no sha256 for {}, so there is "
                     "nothing to compare it with".format(name, version))
        elif name not in expected:
            r.unsure("{} is here, but RELEASING.md records no sha256 for this file".format(name))
        elif expected[name] == digest:
            r.ok("{} matches the build RELEASING.md recorded".format(name))
        else:
            # Not a failure. A local 'python -m build' on another machine
            # legitimately differs: setuptools writes generated metadata in the
            # platform's line endings and gzip stamps the tarball with a time.
            # So this means "not the build that was checked", which the reader
            # has to decide about, rather than "corrupt", which they do not.
            r.unsure("{} is NOT the build RELEASING.md recorded.\n"
                     "           recorded {}\n"
                     "           this one {}\n"
                     "           A build you made yourself will differ, which is fine if you ran\n"
                     "           'twine check' and the test suite against it. A download should\n"
                     "           match; if it does not, fetch it again."
                     .format(name, expected[name], digest))
        out.append(path)
    return out


def check_tool(name, r, extra_dirs=()):
    """On PATH, or beside the thing that needs it."""
    where = shutil.which(name)
    if where:
        r.ok("{} found at {}".format(name, where))
        return True
    for d in extra_dirs:
        for candidate in (d / name, d / (name + ".exe")):
            if candidate.is_file():
                r.ok("{} found at {} (not on PATH, so run it by full path)".format(name, candidate))
                return True
    r.fail("{} is not on PATH and is not beside the tree".format(name))
    return False


def check_index(version, r):
    """Is this version already released? A version cannot be re-uploaded."""
    try:
        import urllib.request
        with urllib.request.urlopen(INDEX, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception as error:
        r.unsure("could not read the index ({}). Check by hand before uploading: {}".format(
            type(error).__name__, INDEX))
        return
    released = sorted(data.get("releases", {}))
    if version in released:
        r.fail("{} {} is ALREADY on the index. A version cannot be re-uploaded; the next one is a "
               "new number. Released: {}".format(DIST, version, ", ".join(released)))
        return
    r.ok("{} is not on the index yet. Latest released is {}".format(
        version, data.get("info", {}).get("version", "unknown")))


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dist", help="where the built artefacts are, if not ./dist")
    ap.add_argument("--no-index", action="store_true",
                    help="skip the index check (it needs the network)")
    args = ap.parse_args()

    r = Report()
    here = pathlib.Path.cwd()

    print("\nRelease preflight, from {}\n".format(here))

    root = repo_root(here)
    if root is None:
        print("  MISSING  this is not a git checkout, so nothing below can be resolved.")
        print("\n  cd to your AbstractGlitch clone and run this again. The three commands in")
        print("  RELEASING.md all need a checkout; running them from a shell's default")
        print("  directory is what failed on 2026-09-11.\n")
        return 2
    r.ok("repository root {}".format(root))

    pkg = root / "glitch"
    if not (pkg / "pyproject.toml").is_file():
        print("  MISSING  no glitch/pyproject.toml under {}. Wrong repository?".format(root))
        return 2

    version = check_versions(pkg, r)
    directory = find_dist(pkg, args.dist)
    artefacts = check_artefacts(pkg, directory, version, r) if version else []

    check_tool("twine", r)
    has_publisher = check_tool("mcp-publisher", r, extra_dirs=(pkg / "registry",))

    if version and not args.no_index:
        check_index(version, r)

    print("")
    if r.problems:
        print("{} thing(s) are not ready:".format(len(r.problems)))
        for p in r.problems:
            print("  - " + p)
        print("\nNothing was uploaded, pushed or published. Fix the above and run this again.")
        return 1

    # Unknown is not ready. The steps still print, because the reader may have a
    # good answer -- they built the artefacts themselves, or the index was
    # unreachable -- but the word "Ready" is reserved for a run where nothing
    # was left open. A green verdict over an unchecked thing is the failure this
    # whole package is about, and it would be absurd to ship it here.
    if r.unknown:
        print("{} thing(s) could not be checked, so this is NOT a clean run:".format(len(r.unknown)))
        for u in r.unknown:
            print("  - " + u)
        print("")
        print("Read each one and decide. The steps are below; nothing has been done for you.\n")
    else:
        print("Ready. Nothing below has been done for you; run them in this order.\n")
    dist_dir = artefacts[0].parent if artefacts else (pkg / "dist")
    print("  1. Upload. From the machine holding the token in $HOME/.pypirc:")
    print("       cd {}".format(dist_dir))
    print("       twine check *")
    print("       twine upload *")
    print("")
    print("  2. STOP. Open https://pypi.org/project/{}/ and confirm the".format(DIST))
    print("     mcp-name marker rendered in the description, with that exact capitalisation.")
    print("     The registry reads that page, not the file. 0.1.2 skipped this and cost a release.")
    print("")
    print("  3. Publish the mirror:")
    print("       cd {}".format(root))
    print("       git subtree push --prefix=glitch https://github.com/AbstractGlitch/glitch-toolkit.git main")
    print("")
    print("  4. The registry entry. The login token expires quickly, so run both without a gap:")
    print("       cd {}".format(pkg / "registry"))
    if not has_publisher:
        print("       (mcp-publisher is not installed here -- see registry/LISTINGS.md)")
    print("       mcp-publisher login github")
    print("       mcp-publisher publish")
    print("")
    print("  5. Then prove what a stranger does, from a clean virtualenv:")
    print("       pip install {}".format(DIST))
    print("       glitch install")
    print("       glitch status")
    print("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
