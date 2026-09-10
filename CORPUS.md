# Corpus

Every check in this package came from something that actually went wrong. This
file is the list, so that a check can be read against the failure it exists for
rather than as a rule somebody thought sounded prudent.

It is also the honest half. Several entries below are caught by nothing here,
and they say so. A corpus that only recorded the failures it had already solved
would be doing the thing this package is about.

**The repositories are named on purpose.** Several entries below name a real, private
repository of the author's and say exactly what went wrong in it. That was put to the
owner directly on 8 September 2026 and kept: a corpus that says which repository each
failure came from is harder to dismiss than the same list anonymised, and there is
nobody to protect here but the author. Nothing in this file is a credential, a key,
customer data, revenue or campaign detail, and that boundary does not move.

All of these are from **8 September 2026** unless dated otherwise. One day, one
repository, nineteen entries. That is not unusual; it is what happens the first
time anything looks.

---

## Caught: a guardrail that is present, green, and refusing nothing

**The sample chapter's leak check.** A paid twenty-chapter book has one free
chapter on the one route search engines are invited to index. A test asserted
the sample stops at its cut and does not leak the rest. It was green. The book
was not built in that environment, so the page had no chapter on it, and the
test was searching an empty page for passages it could therefore never find. Its
neighbour noticed and failed; this one passed. Nothing was broken — the
redaction worked. The alarm had been disconnected and was still showing green.

*What catches it:* this is the rule the whole package is built on. Every step's
check runs its artifact and then runs it against a deliberately broken case, so
an artifact that has stopped refusing fails rather than passes. `FLOOR.md` and
`PLAN.md` ship deliberately unpassable for the same reason.

**A gate that certified a run with a hole in it.** `gate_check.py`, pointed at
this package's own test runner, answered *trustworthy green*. The runner's own
output said `1 suite(s) skipped. That is not a pass.` and exited 0, because a
skipped suite leaves the exit code alone. The gate reported `18`, which was the
first suite's count, not the total. Ten tests unrun, certified.

*What catches it:* `gate_check.py` now detects skips and returns WARN — green,
unproven, non-zero unless the caller passes `--warn-ok` to accept it
deliberately. `glitch check gates` sabotages that ability and fails an
installation where it is missing.

**A runner that exits 0 on a skipped suite.** `tests/run_all.py` exits
`1 if failed else 0`. A SKIPPED suite leaves it at 0, so a workflow checking only
the exit code goes green with the server tests unrun.

*What catches it:* the `full` CI job greps for `SKIPPED` and fails on it.
Removing that grep re-creates a false green inside the package written to catch
false greens.

**The same shape, one repository over.** `floor-audit-mcp/scripts/agreement-tests.mjs`
calls `skipped()` and then `process.exit(fail > 0 ? 1 : 0)`. It currently runs
because a fallback path happens to exist; the day that path moves, it goes green
having tested nothing.

*What catches it:* nothing yet. Recorded rather than fixed.

---

## Caught: a claim nobody had checked

**A step that stated its own price.** A distribution plan tagged a step
*"mechanical, no writing, no judgement, the only step with no downside if the
rest is abandoned"*. Doing it cost two releases. The word "mechanical" was an
estimate wearing the clothes of a fact, and nothing in the document could
contradict it.

*What catches it:* `plan_check.py` now refuses a step that states a cost nothing
in the plan measured, alongside the existing list of verifications written so
they cannot fail. Same idea, one step earlier: that list is about a check that
cannot come back false, this one is about a price that cannot come back higher.

**A kill criterion resting on a premise nobody had verified.** A strategy
document blocked publication of an incident writeup on two questions about a
third party. There was no third party; the account destroyed was the author's
own. A false premise had been holding a dated step for no reason.

*What catches it:* nothing automatic. `plan_check.py` reaches the shape of a
plan, never the truth of it, and says so in its own docstring. Asking the person
who knows is still the only method.

**A test count maintained by hand.** Four files claimed 38 tests while the
suites ran 39.

*What catches it:* a CI step comparing the README's stated count against the
number the runner actually reports, in the one job where nothing skips.

**A safety rule that had been wrong for forty days.** `client-acquisition-saas`
carried a hard rule stating that every `user_id` column cascades from
`auth.users`. True when written; false since 2026-07-30, when 19 constraints
were switched to `restrict`. It was then wrong the other way too — three tables
created after the fix reintroduced the cascade. Acting on the rule as written
would have meant writing a migration for a risk that could not fire, because
every foreign key in the chain is `not null` and terminates at a table that is
restrict-guarded.

*What catches it:* nothing here. `rules_check.py` checks that a rules file is
enforceable, not that its statements are still true of the schema. A rule that
was accurate when written and decayed silently is a real gap and is named as one.

---

## Caught: what you shipped is not what you checked

These are packaging failures. They are listed because they are the same family —
a thing verified in one place and shipped from another — not because this
package checks them for you.

**Annotations that crashed at import on the declared floor.** Two shipped
scripts used `X | None`, which is PEP 604 and needs 3.10, while the package
declared `>=3.9`. A def's annotations are evaluated when the def runs, so the
module raised at IMPORT, not at call — which is why reading the file told nobody
anything. Found by CI on the floor version, the first time CI ever ran.

**A floor that no build backend could honour.** `requires-python = ">=3.8"` with
a build backend of `setuptools>=77`, and no such setuptools runs on 3.8. Shipped
in 0.1.0; nothing had ever checked it.

**A description that shipped a lie permanently.** The README is the PyPI
`long_description`, baked into the distribution at build time. 0.1.0's still said
the package was "not published anywhere". Caught before upload; a version cannot
be re-uploaded, so it would have been permanent.

**Line endings from the builder's machine.** 0.1.0 shipped CRLF in all 21 text
files of the wheel, because it was built on a Windows clone with
`core.autocrlf=true`. One commit produced different bytes depending on who built
it, and the receipt digest hashes file bytes, so the receipt moved with the
builder.

**An ownership marker that could not be added afterwards.** The MCP registry
proves PyPI namespace ownership with an `mcp-name:` line in the package README —
which is, again, baked in at build time. 0.1.1 went up without it. Cost: 0.1.2.

**A namespace spelled with the wrong capital letter.** The grant is
`io.github.AbstractGlitch/*`, following the GitHub login exactly. The entry said
`io.github.abstractglitch/...`, lowercased off a documentation example rather
than off the account holding the grant. Cost: 0.1.3, because the marker proving
ownership is baked into a distribution that cannot be re-uploaded.

*The guard that missed it is the interesting part.* A CI step already checked
that `server.json` and the README agreed. They did — **both were wrong in the
same direction.** A check comparing two things you control cannot notice that
both are out of step with the world. It now derives the expected namespace from
the repository URL's owner segment, which is the same login the grant is issued
against.

**A guard that fired on a healthy repository.** The dependency-free check listed
everything pip could see after installing and failed on anything that was not
this package. That is a census, not a delta. It passed on Linux and failed on
the Windows runner, whose image ships pipx and seven of its dependencies. A check
that fires on a healthy tree is as broken as one that never fires. It now
records `pip freeze` before the install and compares.

**A test that compared an unresolved path.** It passed on every machine it had
ever run on, and failed on Windows CI, where `tempfile` returns a short 8.3 path
(`C:\Users\RUNNER~1\`) that `.resolve()` expands.

---

## Caught: text that changed on the way through

**A BOM written by a shell pipeline.** `Set-Content -Encoding utf8` on Windows
PowerShell 5.1 writes a byte-order mark. Applied to a JSON file, the parser
refused it: `invalid character 'ï' looking for beginning of value`.

**The same class, at scale, in another repository.** `roadmap-studio` took 98
corrupt sequences into its seeded course data through a single
`Get-Content | Out-File` round trip — `Get-Content` decodes with the ANSI
codepage and `Out-File` re-encodes as UTF-8, double-encoding every non-ASCII
character. They survived from the first commit until 2026-08-25.

*What catches it:* nothing in this package. Both repositories now carry the rule
in prose and `roadmap-studio` has a test that fails if its seeded data is
double-encoded again. A general check — no BOM, no mojibake, no CRLF where the
repository says LF — is the strongest candidate for the next artifact here, and
it does not exist yet.

---

## Caught: verifying the documentation instead of the system

**An entry drafted for a repository that had been read-only since August.**
`appcypher/awesome-mcp-servers` was chosen as a listing target. Its
`CONTRIBUTING.md` was read and quoted, its entry format was derived from its
`README.md`, its categories were compared and one was chosen, and the list was
searched for duplicates. All four checks passed. All four were made against
files fetched from `raw.githubusercontent.com`, which serves them exactly the
same whether a repository is alive or archived.

The repository was archived by its owner on 2026-08-01. Pull requests are
disabled. The banner saying so is on the repository page, which nothing had
opened, and the state is one field in the API, which nothing had asked for.

*What this is.* Every check confirmed what the repository **says**. None
confirmed what it **does**. A contributing guide describing how to open a pull
request is not evidence that pull requests can be opened, any more than a green
test is evidence that a check still refuses — it is the same substitution of the
description for the thing, and it survived four separate verifications because
all four were of the description.

*What catches it:* nothing automatic. The habit that would have: before
trusting a repository's rules, ask the repository whether it is accepting
anything — one field, `archived`, on the API, or the banner at the top of the
page. Recorded here because the next list will look exactly as alive from
`raw.githubusercontent.com` as this one did.

**And the same shape one turn further on, on the list that replaced it.** The
pull request was opened against a live repository whose contributing guide
describes exactly how to contribute, and that guide is accurate. Within the hour
a bot commented with the requirement that actually governs merging: the server
must first be listed on a commercial third-party directory, which builds and
runs it, and the pull request must then carry that directory's score badge. None
of that is in the contributing guide, because the guide describes how to *open* a
pull request and the bot enforces what it takes to *merge* one.

Checking the stated process is not checking the operative one. There is often no
document that contains the operative one, and no amount of reading finds it —
the only thing that surfaced it was opening the pull request and being told.

**And a third time, which is the worst of the three, because it published a wrong
instruction.** Satisfying that bot's requirement meant configuring a build on a
directory platform. Its published methodology describes adding a Dockerfile, so a
four-line Dockerfile was written, committed, and mirrored publicly — with the
file telling the reader to paste it.

The platform does not take a Dockerfile. It generates its own Debian image with
Python installed through `uv`, does not put `pip` on the path, and accepts an
array of build steps plus a startup command that it wraps in a proxy. The first
build failed on the second line:

```
/bin/sh: 1: pip: not found
```

Nothing had run it. It went into a committed file on the strength of a
description, and the description was a fair summary of the platform that happened
not to be the platform's interface.

*And then the entry you are reading got its own reach wrong.* As first written,
this paragraph said the block had been **mirrored** — published where a stranger
would follow it. The pre-push inspection found otherwise: the mirror's head was
the subtree split of a commit that predated the block, and the live file carried
no such line. It had never left the private monorepo. That claim was made by
reasoning about what had been committed rather than by reading the mirror, which
is this entry's own subject, committed inside this entry. What settled it was
`git ls-remote`, a computed `git subtree split`, and fetching the published file
— asking the system instead of the record of the system.

**The same mistake also went the other way, an hour earlier.** Searching the
directory for the package returned nothing, and that was read as "the submission
failed". It had succeeded; the public search index had not caught up, and the
account dashboard — authoritative, and not checked before concluding — would have
said so. Absence from a search result is not absence from a system.

**The rules were read at source, and the platform still said no.** 2026-09-10.
`research/CHANNEL_MAP_2026-08-26.md` is the only document in this repository graded
**A**, and it earned that grade for exactly the right reason: its Show HN rules were
quoted from `news.ycombinator.com/showhn.html` rather than from a summary. It
settled what qualifies, what is off topic, and which of two assets to submit. Every
word of it was correct.

The submission was refused anyway. Not on the content, and not on the title. Hacker
News currently restricts Show HN from accounts that are new, and says so on a page
you only reach by pressing submit: *"We are temporarily restricting Show HNs because
of a massive influx, mostly by users who aren't yet familiar with the site or its
culture."* That restriction is not in `showhn.html`. Reading the published rules at
source, which is the strongest form of the habit this file keeps recommending, did
not surface it, because it is a property of the account and the moment rather than
of the rules.

This is the third in a week and they are the same shape. `appcypher` was archived and
read-only while four checks passed against files that serve identically either way.
punkpeye's merge turned out to be gated on a Glama badge that appears in no
contributing guide. Now this. Three rented distribution surfaces, three requirements
that could not be read in advance from anything the surface publishes.

The correction is not "read harder". It is that a channel you do not own has terms
you cannot fully know until you try, and the only honest plan treats the first
attempt as the test rather than as the launch.

**The rule that stopped it was not in the rules.** 2026-09-10, hours after the
one above. Hacker News having closed, the launch post moved to r/ClaudeAI, and
this time the room's rules were read properly first: all twelve, from the
sidebar, before a word was drafted. `content/STANDING_RULES.md` section 6 has
demanded exactly that since 26 August and its table had said `not yet` ever
since. Rule 7 permits showcase posts on condition that they educate, so the
answer was yes, and the reading even caught a second problem nobody had
suspected: the draft was a PostgreSQL postmortem in a subreddit about Claude,
and would have failed rule 2 on relevance.

Then the post was written, the fields filled, and a notice appeared under the
body box: *"We now require total reddit karma >=50 to submit a post on the feed."*
Not in the twelve rules. Visible only in the composer, only for showcase posts,
and only once there is a post to submit. The account was under 50.

So the sidebar was read in full, correctly, at source, and the binding condition
was somewhere the sidebar does not go. Reading the published rules is necessary
and it is not sufficient, because a platform's terms live in three places at
once: what it publishes, what it enforces, and what it only mentions at the
moment you act.

The fourth and the fifth are the same shape and it is worth naming: both are
gates on **who is asking** rather than on **what is being submitted**. No amount
of reading finds those, because they are not facts about the rules. They are
facts about the account.

*What catches all five:* nothing automatic, and probably nothing automatic can.
The habit is the whole of it. A repository's rules are not its state; a
contributing guide is not the merge requirement; a methodology page is not the
API; a search result is not the database. The only thing that establishes what a
system does is making it do it, and where that is impossible from here — the
platform is blocked by this machine's egress proxy — the honest move is to record
the claim as reported rather than as checked, which is what `registry/LISTINGS.md`
now does.

---

## Caught: a promise that stopped at the package boundary

**The extra ate an unrelated application.** The checker has no runtime
dependencies, and a CI job asserts it by diffing `pip freeze` either side of the
install. That guard covers `pip install glitch-toolkit`. It does not cover
`pip install 'glitch-toolkit[mcp]'`, which is a different thing entirely:
`mcp>=2.0` pulls pydantic, starlette, cryptography, pywin32, opentelemetry and
more, and pip upgrades whatever is already installed to satisfy them.

Run against a global interpreter, it replaced pydantic 1.10.22 with 2.13.5 and
starlette 0.46.2 with 1.6.0, and a FastAPI application on the same machine that
pins `starlette<0.47` stopped satisfying its own requirements. Nothing about the
package was broken. The README simply said `pip install 'glitch-toolkit[mcp]'`
with no word about where, and the reader had one Python.

The registry entry had it right the whole time — it launches through `uvx`,
which builds a throwaway environment — and the README's own instructions did
not match it. Two descriptions of how to run one program, and only one of them
was safe.

*What catches it:* nothing automatic yet. The README now leads with the isolated
form and says what the extra costs. A check comparing the README's documented
launch against the one `registry/server.json` publishes is the obvious next
guard and does not exist.

---

## Why there is no seventh step

Every `Step` in `cli.py` cites a chapter of the book this came from, and the six
steps are that book's path. Several failures above have no chapter, so they have
no step. Bolting one on would break the correspondence the path rests on, and a
list of good ideas with no through-line is a toolbox rather than a product.

So the division is: a failure the path already names gets a sharper check inside
the step that names it. A failure the path does not name goes here, and waits
for a reason to exist beyond having happened once.
