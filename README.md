<!-- mcp-name: io.github.abstractglitch/glitch-toolkit -->
<!-- The line above is how the official MCP registry proves this PyPI
     package belongs to the namespace it claims. It is read out of the
     project description, which is this file baked into the distribution
     at build time, so it cannot be added to a release after the fact. -->

# glitch

**A check that has stopped refusing things still passes.** That is the failure
this looks for.

On 8 September 2026, in the repository this package was extracted from, a test
guarded the one chapter of a paid book that is given away free — asserting the
sample stops at its cut and does not leak the rest. It was green. It was
searching a page that had no book on it, for passages it therefore could never
find, and passing. Nothing was broken; the redaction worked fine. The alarm had
been disconnected and was still showing a green light.

Every guardrail decays that way eventually, and the decay is silent, because a
guardrail that has stopped refusing looks exactly like one with nothing to
refuse.

`glitch` installs six guardrails into your repository and then, whenever you
ask, runs each one against a case it is *supposed* to refuse. One that no longer
refuses anything fails here, loudly, instead of passing quietly.

```bash
pip install glitch-toolkit

glitch install     # put the artifacts in this repository
glitch status      # what is installed, what is not
glitch check --all # verify every step
```

No dependencies, no network calls, no telemetry. It writes nothing outside the
directory you point it at.

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

Apache License 2.0 — see [LICENSE](https://github.com/AbstractGlitch/glitch-toolkit/blob/main/LICENSE)
and [NOTICE](https://github.com/AbstractGlitch/glitch-toolkit/blob/main/NOTICE). Chosen over MIT for
the patent grant.

Everything in this repository is under it. Use it commercially, change it,
redistribute it.

The links above are absolute on purpose: this README is also the package's
description on PyPI, where a relative link resolves against `pypi.org` and
returns a 404.

## Where this comes from

This repository is a published mirror. The package is developed inside a private
monorepo alongside the book *Building Your Store Or Your SaaS With Claude*, whose
practices it installs and checks, and it is pushed here as a subtree. The book,
the shop that sells it and the rest of that repository are **not** open source
and are not here. Nothing is being withheld from this repository that belongs to
the package.

Issues and pull requests belong here rather than there, because here is the part
anyone can read.

## Status

Version 0.1.1. It installs, and the practices it checks are the six the book
argues for. 0.1.0 was the first release; 0.1.1 changes this description and adds
continuous integration, and nothing about what the code does.

What it is not yet: it gates nothing. `glitch-mcp` reports and records and
cannot block an agent from doing anything. That is deliberate and the reasoning
is in `mcp_server.py` — a server that stands between an agent and a production
database should earn its evidence before it earns the power to refuse.
