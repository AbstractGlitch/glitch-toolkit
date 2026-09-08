# Listings

Phase 1 step p1f: list the package where the audience is definitionally right.
Everything here is a **draft to approve**. Nothing in this file has been posted,
submitted or sent, and none of it should be posted by anyone but the owner, in
the owner's name.

The step was written down as "mechanical, no writing, no judgement". Two of the
three named surfaces are. The third is not, and the first is not free either:
it needs a release. Both are recorded below rather than discovered at the
submission form.

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

**Blocked on a release, and this is the finding.** Ownership of a PyPI
namespace is proved by an `mcp-name: <server-name>` marker in the package
README. The README is the `long_description`, which is baked into the
distribution at build time. **0.1.1 is on PyPI without the marker, and a PyPI
version cannot be re-uploaded.** So listing requires a new release.

That release is prepared: the marker is at the top of `README.md`, the version
is `0.1.2` in `pyproject.toml`, `src/glitch/__init__.py` and `server.json`, and
a CI step now refuses a tree where those disagree or the marker is missing.
Confirmed present in the built wheel's metadata, not merely in the source file.

The distribution is `glitch-toolkit` and the server entry point is `glitch-mcp`,
so the runtime line is `uvx --from 'glitch-toolkit[mcp]' glitch-mcp` rather than
the usual bare package name. That divergence is deliberate and `RELEASING.md`
says why; the cost of it is this one extra argument.

**Steps, once 0.1.2 is on PyPI:**

```
mcp-publisher login github          # as AbstractGlitch, for io.github.AbstractGlitch/*
mcp-publisher publish               # from glitch/registry/
```

**What to check first:** that the PyPI project page for 0.1.2 shows the marker
in its rendered description. If it does not, the publish will be rejected and
the fix is another release, not a retry.

---

## 2. `mcpservers.org` — the submission route for wong2/awesome-mcp-servers

That list does not take pull requests; it takes submissions at
<https://mcpservers.org/submit>. Use the one-line blurb above.

Nothing blocks this one. It needs no release and no code change.

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

| Surface | State | Blocked on |
|---|---|---|
| Official MCP registry | entry written and schema-validated | 0.1.2 uploaded to PyPI |
| mcpservers.org | blurb written | nothing — owner submits |
| appcypher/awesome-mcp-servers | entry written | nothing — owner opens the PR |
| Claude Code plugin directory | not started | a plugin that does not exist yet |

Two of four can go today. One needs the release that is prepared here. One was
mis-scoped and should come out of p1f rather than sit in it failing.
