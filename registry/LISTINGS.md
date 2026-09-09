# Listings

Phase 1 step p1f: list the package where the audience is definitionally right.
Everything here is a **draft to approve**. Nothing in this file has been posted,
submitted or sent, and none of it should be posted by anyone but the owner, in
the owner's name.

The step was written down as "mechanical, no writing, no judgement". Two of the
three named surfaces are. The third is not, and the first was not free either:
it needed two releases. Both are recorded below rather than discovered at the
submission form.

**State, 9 September 2026.** The official registry is **listed and active**. The
mcpservers.org submission is **in**, made by the owner on 9 September; a
submission is not a listing, so it proves nothing until it appears. The
`appcypher` pull request is **drafted and open**. The plugin directory is out of
scope and says why below.

**And the ranking, which was not written down and should have been.** These four
surfaces are not equal and calling the remaining two "the cheapest" made
cheapness sound like a reason. The registry is the one that mattered: clients
query it machine-readably and arrive at the point of need. The aggregator lists
are browsed by people, hundreds of entries deep, and their real argument is
being scraped and indexed rather than read — worth a quarter of an hour, not
worth a fortnight. The step with actual reach is the incident writeup, which is
a different step and a harder one.

Gate A allows a step to pass by being **explicitly withdrawn** as well as done.
So deciding not to open the `appcypher` pull request, and saying so here, is a
pass. What fails Gate A is drift: not doing it and not deciding, then reading a
false negative on 22 September.

---

## The blurbs

Three lengths, because three surfaces cap it differently. Same claim in all
three, so the package does not describe itself differently depending on who is
reading.

**89 characters** — the official registry caps `description` at 100.

> Read-only checks that fail a guardrail which is present but has stopped refusing anything

**84 characters** — already live as the PyPI summary, unchanged.

> Install and verify bounded-autonomy practices in a repository worked on by AI agents

**One line, for the awesome-lists**, which run long and want the shape of the
thing:

> Read-only checks over a repository's own guardrails, run over MCP or from the
> command line, that fail a check which is present and has stopped refusing
> anything. Every answer is appended to a local, append-only ledger. No network
> calls, no telemetry, no writes to the repository being checked.

---

## 1. The official MCP registry — `registry.modelcontextprotocol.io`

**Entry:** [`server.json`](server.json), in this directory. Validated against the
published `2025-12-11` schema, and the validation was proved to refuse six
broken variants rather than only ever printing VALID.

**LISTED 2026-09-08.** `io.github.AbstractGlitch/glitch-toolkit`, version
`0.1.3`, status active. Read back from the registry's own API rather than
believed from the publish command, which is worth doing here: the run that
succeeded was followed by one that returned `duplicate version`, and taking that
error at face value would have read as a failure when it was the registry saying
the work was already done.

*What this cost, kept because it is the reason the entry has the shape it does.*
Ownership of a PyPI namespace is proved by an `mcp-name: <server-name>` marker
in the package README. The README is the `long_description`, baked into the
distribution at build time, and a PyPI version cannot be re-uploaded. 0.1.1 went
up without the marker, which cost 0.1.2. Then 0.1.2 carried the marker spelled
`io.github.abstractglitch`, lowercased off a documentation example rather than
off the account holding the grant, which is `io.github.AbstractGlitch/*` and is
case sensitive. That cost 0.1.3.

The guard that missed the second one is the part worth remembering: a CI step
already checked that `server.json` and the README agreed, and they did — both
were wrong in the same direction. It now derives the expected namespace from the
repository URL's owner segment, so it compares against something outside itself.

The distribution is `glitch-toolkit` and the server entry point is `glitch-mcp`,
so the runtime line is `uvx --from 'glitch-toolkit[mcp]' glitch-mcp` rather than
the usual bare package name. That divergence is deliberate and `RELEASING.md`
says why; the cost of it is this one extra argument.

**For the next release, since the entry names a version:**

```
mcp-publisher login github          # as AbstractGlitch, for io.github.AbstractGlitch/*
mcp-publisher publish               # from glitch/registry/, immediately after login
```

The JWT expires quickly; a gap between the two lines is what produced a 401 the
first time. Check before publishing that the PyPI page for the version in
`server.json` renders the `mcp-name` marker with the exact capitalisation, since
a mismatch is refused and the fix is another release rather than a retry. And do
not commit `mcp-publisher.exe` if it was downloaded into this directory.

---

## 2. `mcpservers.org` — the submission route for wong2/awesome-mcp-servers

That list does not take pull requests; it takes submissions at
<https://mcpservers.org/submit>. Use the one-line blurb above.

**SUBMITTED 2026-09-09** by the owner. A submission is not a listing: nothing
here is evidence until the entry appears, and if it never does, that is a fact
about the queue rather than about the package.

---

## 3. `appcypher/awesome-mcp-servers` — a pull request

Takes PRs. Its contributing guidelines ask for: no duplicates, alphabetical
order, and the entry added to the bottom of the relevant category. The literal
format in the README is:

```
- [name](url) - Description.
```

Draft entry, for **Development Tools** (the closest category; there is no
category for guardrails, and inventing one in the same PR that adds an entry is
how a list PR gets closed):

```
- [glitch](https://github.com/AbstractGlitch/glitch-toolkit) - Read-only checks over a repository's own guardrails that fail a check which is present and has stopped refusing anything. Appends every answer to a local append-only ledger. No network calls and no writes to the repository being checked.
```

Alphabetical position and the absence of a duplicate must be checked against the
list at the moment of the PR, not against this file.

---

## 4. The Claude Code plugin directory — **not a listing, a build**

This one was written down as mechanical and it is not. The directory takes
plugins with a `.claude-plugin/` manifest, `skills/`, optional `agents/`,
`hooks/hooks.json` and `.mcp.json`, submitted through an in-app form and
screened; `claude plugin validate` is the check the pipeline runs, and it can be
run locally first.

`glitch` has four skills, but they are **assets it installs into somebody
else's repository**, not a plugin it presents to a client. Shipping to that
surface means building a plugin wrapper, deciding whether it duplicates or
replaces `glitch install`, and keeping the two from drifting — which is the
failure mode this package exists to catch.

So it is out of scope for p1f as written. It is a real opportunity and it is a
separate piece of work with its own decision in it.

---

## What is actually ready

| Surface | State | Next |
|---|---|---|
| Official MCP registry | **listed 8 Sep, 0.1.3, active** | nothing; re-publish only on a release |
| mcpservers.org | **submitted 9 Sep** | wait; a submission is not a listing |
| appcypher/awesome-mcp-servers | entry drafted, **open** | the owner opens it, or withdraws it on the record |
| Claude Code plugin directory | not started, **out of scope** | a separate piece of work with its own decision |

Two of four are done. One is a quarter of an hour whenever it is wanted, or an
explicit withdrawal, and either passes. One was mis-scoped and came out of p1f
rather than sitting in it failing.
