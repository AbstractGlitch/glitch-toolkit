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
`punkpeye` pull request is **open as #14062** — `appcypher`, the list this
step originally targeted, turned out to have been archived since August. The
plugin directory is out of
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
That provision is moot for this surface now that the pull request is open, but
it stands for the plugin directory and for whatever surface comes next. What
fails Gate A is drift: not doing something and not deciding, then reading a
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

## 3. An awesome-list pull request — and which list

**`appcypher/awesome-mcp-servers` is dead.** Archived by its owner on
2026-08-01, read-only, pull requests disabled. This was discovered at the edit
page, after the entry for it had been drafted, the category chosen and the
contributing rules read. Every one of those checks was made against files
fetched from `raw.githubusercontent.com`, which serve perfectly well from an
archived repository. **Nothing had checked whether the repository was alive.**
Recorded in `CORPUS.md`; it is the same shape as the rest of that file.

Two other lists were then looked at properly:

- **`wong2/awesome-mcp-servers`** — alive, but its README says *"We do not
  accept PRs. Please submit your MCP on the website"*. That website is
  mcpservers.org, which is surface 2 above and already submitted.
- **`punkpeye/awesome-mcp-servers`** — alive, and roughly twenty times the
  size. This is the target.

**The entry, in that list's own format.** It uses a legend of emoji markers
rather than the icons the dead list used: 🐍 Python codebase, 🏠 local service,
🍎 🪟 🐧 for operating systems. No 🎖️, which means official protocol
implementation and is not us. The category is **Developer Tools**, appended at
the bottom, because that section is in insertion order rather than alphabetical.

```
- [AbstractGlitch/glitch-toolkit](https://github.com/AbstractGlitch/glitch-toolkit) 🐍 🏠 🍎 🪟 🐧 - Read-only checks over a repository's own guardrails, failing any that are present but have stopped refusing anything. Every answer is appended to a local append-only ledger. No network calls and no writes to the repository being checked. `uvx --from 'glitch-toolkit[mcp]' glitch-mcp`
```

**The 🍎 was earned rather than assumed.** The marker asks which operating
systems the server runs on. CI covered Linux and Windows; nothing had ever run
on macOS. The package is standard library only with no OS-specific code, so it
almost certainly worked and omitting the marker would have been misleading in
the other direction — but claiming it would have been an unverified assertion in
somebody else's README, which is the exact thing this package exists to object
to. A `macos-latest` job was added to the test matrix instead, so the marker is
a checked fact.

**Their contributing file asks agents to say so.** *"If you are an automated
agent, we have a streamlined process for merging agent PRs. Just add `🤖🤖🤖` to
the end of the PR title to opt-in."* This entry was drafted by one, so the title
carries it. Suggested title:

```
Add glitch-toolkit to Developer Tools 🤖🤖🤖
```

**OPENED 2026-09-09** as
<https://github.com/punkpeye/awesome-mcp-servers/pull/14062>, one line added and
nothing else touched, no conflicts with the base branch. Their own submission
check runs on it; merging is a separate matter, and with roughly 2,200 pull
requests open on that repository it should not be expected quickly.

**BLOCKED, within the hour, on a third party.** `github-actions[bot]` commented
on the pull request with a listing requirement that is not in the contributing
guide: the server must be listed on **Glama** (`glama.ai/mcp/servers`) and pass
its checks, and the pull request must then carry a Glama **score badge**. Glama
builds and runs the server in a sandbox and performs the standard introspection
exchange; what it builds from is configured on **Glama's admin page**, not
committed here. ~~The Dockerfile is configured there.~~ It is not a Dockerfile,
though this paragraph said so for a day; the build spec below carries the
correction and the failure that produced it.

**Where the badge goes was settled by reading the list, not the instruction.**
The bot said "after the server description", which puts it at the end of the
line. All 269 badged entries in this category put it immediately after the
repository link, before the emoji markers. Following the instruction literally
would have produced the only entry in 269 formatted differently — passing the
stated check and failing the list it was checking for. When a stated
requirement and the corpus it governs disagree, read the corpus.

So merging is not the maintainer's decision alone. It is gated on a commercial
directory's build system. That was invisible when the surface was chosen, and it
is a fact about the surface rather than about this package.

*Do not read the list itself as evidence the badge was always required.* 269 of
the 483 entries in that category carry one and 214 do not; the requirement is
new and the older entries are grandfathered.

**The introspection bar is met, and this was run rather than reasoned.** In a
clean virtualenv with `glitch-toolkit[mcp]` from PyPI, launched from an entirely
empty directory, the server answered `initialize` reporting `glitch 0.1.3` and
returned all three tools to `tools/list`, with nothing on stderr. Reading the
code says the same — `on_list_tools` returns a static list and startup only
calls `.resolve()`, which does not require the path to exist — but reading the
code is what `CORPUS.md` is about, so it was executed.

**The build spec, as it actually built.** Glama does not take a Dockerfile. It
generates its own Debian image with Python installed through `uv` — and `pip`
not on the path — then accepts an array of build steps and a startup command,
which it wraps in `mcp-proxy`:

```
build steps:
  python -m venv /opt/glitch
  ln -s /opt/glitch/bin/pip /usr/local/bin/pip
  pip install --no-cache-dir 'glitch-toolkit[mcp]'
  ln -s /opt/glitch/bin/glitch-mcp /usr/local/bin/glitch-mcp

startup command:
  ["glitch-mcp", "--repo", "."]
```

~~This section previously carried a four-line Dockerfile — `FROM
python:3.12-slim`, `RUN pip install ...`, `WORKDIR /repo`, `ENTRYPOINT
["glitch-mcp", "--repo", "."]` — and instructed the reader to paste it on
Glama's admin page.~~ **That is the block that failed**, and the file said to use
it. Superseded 2026-09-09 rather than deleted, because the obvious-looking answer
being the broken one is the useful part:

```
/bin/sh: 1: pip: not found
process "/bin/sh -c (pip install --no-cache-dir 'glitch-toolkit[mcp]')" did not
complete successfully: exit code: 127
```

It was written from Glama's published methodology rather than from Glama, and
committed before anything tried it. It never reached the public mirror: the last
subtree push predated the commit that introduced it, which was established by
reading the mirror rather than by assuming — an earlier draft of this sentence
said it had been mirrored and was wrong. `CORPUS.md` carries both halves.

**3.12 remains correct, and now for a second reason.** Glama's image is Python
3.12, and 3.12 is the version the `full` CI job installs the `[mcp]` extra on and
exercises the server with. The empty-directory handshake above ran on 3.11. The
core matrix covers 3.13, but it covers the *package* — no extra, no server
started — so 3.13 would still be an unverified claim.

**Checked 2026-09-09: not findable on Glama by search.** That reading was wrong,
and the way it was wrong is worth keeping. The submission had in fact succeeded;
the public search index simply had not caught up, and the account dashboard —
which is authoritative and was not checked before concluding — would have shown
it. A directory's search results are a view of its state, not its state.

**LISTED, as reported by a handoff run on 2026-09-09 and NOT verified here.**
`glama.ai` is blocked by the egress proxy on the machine this file is written
from, so every claim in this paragraph is on that report's word rather than
checked, exactly as an mcpservers.org submission is not a listing until it
appears:

- profile at <https://glama.ai/mcp/servers/AbstractGlitch/glitch-toolkit>,
  claimed and verified as belonging to AbstractGlitch
- a Glama release published as 0.1.3; the successful build reported
  `glitch 0.1.3` and returned all three read-only tools
- **tier B**, which is what the awesome-list requirement needs

**One of those three is no longer on the report's word.** The badge endpoint
under that profile was opened in a browser on 2026-09-09 and served a real
score image — seen rather than relayed. That establishes two things and no
more: the profile resolves at that path, and Glama serves a grade for it. It
confirms neither the release, nor the build output, nor the tool count; those
stay on the handoff's word. Letting one checked fact stand in for an unchecked
set is the substitution this package exists to catch, and the flag on the
paragraph above stays where it is.

One loose end, stated rather than smoothed: the individual tool-quality
evaluations are still marked `pending`, so there is no numeric score. A tier is
normally derived from a score, so a tier without one is worth re-reading when the
evaluations finish rather than treated as settled. If it moves, the three gaps in
`RELEASING.md` are the likely reason and the likely fix.

The badge sharpens that end rather than closing it: a grade is being served
while the evaluations that should produce it still read `pending`. Either the
grade has an input this file has not identified, or it is a placeholder awaiting
one. Both readings point the same way — re-read it when the evaluations finish.

**Submitting with 0.1.3 as it stands is a decision, not an oversight.** Glama's
score is 70% tool definition quality and 30% server coherence, and it re-scores
on every introspection sweep. So a later release lifts the grade automatically,
and making a fourth release in two days *for the grade* would be the proxy
driving the product. The three real gaps that check exposed are written into
`RELEASING.md` instead, to be picked up by whatever release happens next for its
own reasons.

**BADGE ADDED 2026-09-09**, committed directly to `patch-1` as a second commit
rather than a second pull request. Verified by fetching the branch and diffing
it against the fork's `main`, not by reading the pull request header: one
occurrence of `glitch-toolkit`, byte-identical to the drafted line, at the end
of Developer Tools directly above `### Delivery`, and a whole-file diff of
`1708a1709` — one line added, nothing removed, nothing else touched. The
heading had no blank line before it in the base either, so that shape is
unchanged. Nothing further is owed on this surface; merging is a maintainer's
decision in a queue roughly 2,200 deep.

*Three things went wrong on the way and are worth keeping.* The entry was first
pasted one line too low, below the `### Delivery` heading rather than above it,
which would have filed a guardrail checker under courier logistics. The cause is
worth naming: the last entry in the section wraps across six display rows and is
one logical line, so "put the cursor at the end of the line" is ambiguous in a
web editor. It was caught by looking at the result before committing rather than
by any rule. The absence of a duplicate, and which entry is currently last, were
both re-checked against the live README immediately before the paste, because
both had moved since the first draft.

Third, the expected shape of the badge commit was stated as "1 addition, 1
deletion" — which is that commit's own diff, and not the pull request's. The
pull request is diffed against `punkpeye:main`, which never held the line, so
its correct reading is one addition and no deletion. A number was carried from
the wrong baseline, and a confirmation step that had been given a wrong success
criterion would have raised a false alarm on a clean result. It was caught by
computing the diff instead of accepting the prediction.

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
| appcypher/awesome-mcp-servers | **archived 1 Aug 2026, dead** | nothing; PRs are disabled |
| punkpeye/awesome-mcp-servers | **PR #14062 open, badge added 9 Sep, gate cleared** | nothing; a maintainer's queue of ~2,200 |
| Glama directory | **listed 9 Sep, tier B** (reported, unverified here) | re-read the score when the evaluations finish |
| Claude Code plugin directory | not started, **out of scope** | a separate piece of work with its own decision |
| Hacker News, Show HN | **refused 10 Sep: new accounts restricted** | not a listing surface; recorded here because it was attempted. See `CORPUS.md` |

**Hacker News is in that table without belonging in it.** Show HN is a launch channel rather
than a listing, and it is recorded because it was tried on 2026-09-10 and refused: the
account was new, and Show HN is currently restricted for new accounts. The refusal is
not about this package. `research/CHANNEL_MAP_2026-08-26.md` had read `showhn.html` at
source and was right about every rule on it; the restriction is not on that page. The
launch post moved to r/ClaudeAI, which satisfies Gate A on its own wording, and the Show
HN waits until there is standing to post one. `CORPUS.md` carries the entry.

Everything p1f can finish on this side is finished. The registry listing is
live and checked here. Glama is listed on a handoff's report, of which one
part — the profile and its served grade — has now been seen first-hand.
mcpservers.org is lodged, and a submission is not a listing until it appears.
punkpeye is complete and waiting on a maintainer. Of the two that are not
shipped, one was archived before it was tried and one was mis-scoped, and it
came out of p1f rather than sitting inside it failing.
