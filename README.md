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

## The MCP server (read-only)

```bash
pip install 'glitch-toolkit[mcp]'
glitch-mcp --repo .
```

It offers the checks to an agent as three tools — `glitch_status`, `glitch_check`,
`glitch_ledger_tail` — and appends every question and answer to
`.claude/toolkit/ledger/ledger.jsonl`.

**It gates nothing.** It cannot pause, block, refuse or intercept any action. It
has no database connection, no credential and no network call. That is the whole
first version, on purpose: a server that stands between an agent and a
production database is serious software, and the honest order is to run
read-only first, read the ledger, and find out what it *would* have refused
before giving it the power to refuse. A gate built before that record exists is
a guess with permissions.

The checks write nothing into your repository. The server breaks that in exactly
one place — it appends to the ledger — and `--no-ledger` turns off even that, at
the cost of the only thing worth keeping.

In Claude Code, `.mcp.json`:

```json
{
  "mcpServers": {
    "glitch": { "command": "glitch-mcp", "args": ["--repo", "."] }
  }
}
```

### The ledger

Append-only JSONL. Nothing rewrites a line it did not just write; a record that
is overtaken is superseded by a new one and both stay; a field nobody measured
is `null` rather than `0`; a half-written last line is skipped and counted, never
repaired, because repairing it means rewriting the file.

## Tests

```bash
python tests/run_all.py      # all three suites, 38 tests
```

The server suite skips cleanly without the `[mcp]` extra and the runner reports
that as SKIPPED rather than passing, because a green line meaning "we did not
look" is the exact failure the gate-check practice exists to catch.

## Licence

Apache License 2.0 — see [LICENSE](LICENSE) and [NOTICE](NOTICE). Chosen over MIT
for the patent grant.

The licence covers **this directory only**. It was extracted from a repository
that also holds a commercial book, its shop, and unreleased application code,
none of which are open source; the `LICENSE` at that repository's root is a
reservation that grants nothing outside `glitch/`.

## Status

Pre-release. Licensed, but **not published anywhere** — no PyPI release exists
and the distribution name above is a placeholder that has not been claimed.
`pip install` from a checkout works today; a package index does not have it.
