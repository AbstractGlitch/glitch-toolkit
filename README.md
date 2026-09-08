# glitch

Install the practices from *Building Your Store Or Your SaaS With Claude* into
your own repository, and check that they still refuse things.

```bash
glitch install     # put the artifacts in this repository
glitch status      # what is installed, what is not
glitch check --all # verify every step
```

## What it actually checks

A step is not complete because a file is present. Every check does three things
and reports which of them failed:

1. finds the artifact
2. runs it, and expects it to work
3. runs it against a deliberately broken case, and expects it to **refuse**

Without the third, a check passes the moment you copy a file in, whether or not
that file has any teeth left, and it would be green for every reader forever.
`tests/test_cli.py` exists to prove the checker fails that case; its `SABOTAGE`
test installs artifacts that run, exit 0 and refuse nothing.

## What `install` will not do

It will not write your `CLAUDE.md`, `FLEET.md`, `FLOOR.md` or `PLAN.md`. Four of
the six steps are checked against your own file, because for those four the file
*is* the work: a rules file that holds, a desk table with one committer, a floor
measured twice, a plan someone else approved. A command that wrote them would
turn the path into "you ran an installer". The `FLOOR.md` and `PLAN.md` templates
ship deliberately unpassable for the same reason.

It will not overwrite. An artifact already in your repo is left alone and
reported as kept; `--force` is how you say otherwise.

It writes nothing outside the directory you point it at, makes no network calls,
and has no dependencies outside the standard library.

## Running it without installing it

`cli.py` is one file and stays one file. Copy it into a repository and `status`
and `check` work with nothing on the path and no install step — that property is
deliberate and there is a test for the search paths it uses. Only `install`
needs the rest of the package, and it says so plainly rather than failing oddly.

## Tests

```bash
python tests/test_cli.py     # 18 tests, no dependencies
```

## Status

Pre-release, and **no licence is declared yet** — see the note at the top of
`pyproject.toml`. Until that decision is made the package carries the
`Private :: Do Not Upload` classifier, which PyPI honours by rejecting it.
