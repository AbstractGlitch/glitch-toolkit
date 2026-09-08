# Corpus

Every check in this package came from something that actually went wrong. This
file is the list, so that a check can be read against the failure it exists for
rather than as a rule somebody thought sounded prudent.

It is also the honest half. Several entries below are caught by nothing here,
and they say so. A corpus that only recorded the failures it had already solved
would be doing the thing this package is about.

All of these are from **8 September 2026** unless dated otherwise. One day, one
repository, seventeen entries. That is not unusual; it is what happens the first
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

## Why there is no seventh step

Every `Step` in `cli.py` cites a chapter of the book this came from, and the six
steps are that book's path. Several failures above have no chapter, so they have
no step. Bolting one on would break the correspondence the path rests on, and a
list of good ideas with no through-line is a toolbox rather than a product.

So the division is: a failure the path already names gets a sharper check inside
the step that names it. A failure the path does not name goes here, and waits
for a reason to exist beyond having happened once.
