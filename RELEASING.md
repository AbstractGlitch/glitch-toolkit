# Releasing

**0.1.4 was released on 2026-09-11 at 12:11 UTC.** Read from the index, not from this file:
`glitch-toolkit` latest is 0.1.4, five releases, `>=3.9`, Apache-2.0. What is in it is below.

**This line said "0.1.4 is prepared and NOT released" until the upload, and that is the second time
in one day this file has been wrong about release state in exactly that way.** The first was about
0.1.3, corrected this morning, with a sentence added saying the version had been determined by
asking the index and that the next one should be too. Hours later the sentence about the next one was
false.

**A correction is not a mechanism.** What got fixed in the morning was one sentence. What produced it
— release state written into prose by hand, with nothing able to contradict it — was not touched, so
it produced the same defect at the first opportunity. Anybody reading this before an upload should
assume the line above is stale and check the index, which `release_preflight.py` now does on every
run. The durable answer is further down: publish from CI, and let the run that uploads be the thing
that writes this.

**0.1.3 was released on 2026-09-08**, and the line that stood here until
2026-09-11 said it was not. It read, in bold, at the top of the release
checklist, *"0.1.3 is prepared and NOT released"*. The index disagrees and the
index is the authority: `0.1.0`, `0.1.1`, `0.1.2`, `0.1.3`, latest `0.1.3`, read
from `https://pypi.org/pypi/glitch-toolkit/json` on 2026-09-11.

That is worth more than a correction. It is this package's own corpus class —
verifying the documentation instead of the system — sitting in the file somebody
reads in the minutes before they upload something that can never be re-uploaded.
It went stale the moment 0.1.3 shipped and nothing could contradict it, because
nothing asked. The version below was determined by asking the index, not by
reading this file, and the next one should be too.

**0.1.3 exists because of a mistake.**
The registry namespace is CASE SENSITIVE and follows the GitHub login exactly:
the grant is `io.github.AbstractGlitch/*`. The entry was written
`io.github.abstractglitch/...`, lowercased off a documentation example rather
than off the account holding the grant. Publishing returned 403.

Correcting the entry was not enough. The ownership marker must match the server
name character for character, and the marker is in the README, which is the
`long_description` baked into the distribution. 0.1.2 carries the lowercase
spelling, cannot be re-uploaded, and the registry refused it with:

> the server name 'io.github.AbstractGlitch/glitch-toolkit' must appear as
> 'mcp-name: io.github.AbstractGlitch/glitch-toolkit' in the package README

So a one-character casing error cost a release. The `dist` job now derives the
expected namespace from the repository URL's owner segment and fails on a
mismatch; the version before it only checked that `server.json` and the README
agreed with each other, and they did — both were wrong in the same direction.

**0.1.2 was released on 2026-09-08.** It carries the marker, spelled wrongly,
and is superseded rather than withdrawn. It is otherwise identical to 0.1.3.

**Why 0.1.2 existed.** It exists for one reason: listing on the
official MCP registry requires an `mcp-name: io.github.AbstractGlitch/glitch-toolkit`
marker in the package README, the README is the `long_description` baked into
the distribution at build time, and 0.1.1 went up without it. A PyPI version
cannot be re-uploaded, so the marker cannot be added to 0.1.1 and a release is
the only way to carry it. The marker is confirmed present in the built wheel's
metadata, not only in the source file.

The registry entry itself is `registry/server.json`, validated against the
published `2025-12-11` schema and proved to refuse six broken variants. A CI
step in the `dist` job now fails a tree where `server.json`, `pyproject.toml`
and the README marker disagree, because the entry names a PyPI version and an
entry pointing at a version that is not on the index is a dangling listing.
`registry/LISTINGS.md` carries the rest of the surfaces and what each one is
blocked on.

Before uploading 0.1.2, check what 0.1.1 taught: the description on the PyPI
project page is what the registry reads, so confirm the marker renders there
after the upload and before running `mcp-publisher publish`.

**0.1.1 was released on 2026-09-08**, the same day as 0.1.0, to
<https://pypi.org/project/glitch-toolkit/>. Verified from the index's own JSON
rather than the local build: `requires_python >=3.9`, `License-Expression:
Apache-2.0`, all three project URLs, `mcp>=2.0` only under the extra, and a
description that opens with the failure the package detects. Then installed from
the real index into a clean virtualenv: both previously-crashing scripts import,
and `glitch check gates` returns a receipt.

**One thing the release proved about this file's own guard.** The wheel is LF
throughout — 0 of 23 text files carry CRLF, against 21 of 21 in 0.1.0, so
`.gitattributes` did its job. The **sdist** still carries three: `PKG-INFO`,
`setup.cfg`, and the egg-info `PKG-INFO`. All three are generated by setuptools
at build time, in text mode, on the Windows machine doing the building. No
attribute in the repository can reach them, because they are not in the
repository.

That matters less for what it breaks — nothing; PyPI parses them fine — than for
what it reveals. **The CI CRLF guard runs on `ubuntu-latest`, so it can only ever
check a Linux build, while releases are uploaded from Windows.** It is a check
pointed at an artifact nobody ships. It would also have missed these three
anyway, since it only inspects `.py`, `.md`, `.json` and `.txt`, and two of the
three files have no extension at all. The real fix is to publish from CI so the
checked artifact and the shipped artifact are the same file; until then this
paragraph is the honest statement of what the guard does and does not cover.

This file is the checklist 0.1.0 went through and the record of what was decided
before it.

## 0.1.4 — the handover, and what was already verified

Prepared on 2026-09-11 in a Linux container that deliberately holds no PyPI token.

**Steps 1 and 2 are now done.** The owner rebuilt on their own machine, ran all three suites against
that build (40 passed, 0 failed, none skipped, with the `[mcp]` extra installed), `twine check`
passed both files, and the upload went through at 12:11 UTC. Step 2 was then verified against the
live project page rather than eyeballed: the description carries
`mcp-name: io.github.AbstractGlitch/glitch-toolkit` with exact capitalisation, exactly one such
line, so the registry will accept it. That is the step 0.1.2 skipped.

**Step 5 is done too**, from the real index in a clean virtualenv: `pip install glitch-toolkit`
resolves 0.1.4, adds exactly one distribution and no dependencies, and `glitch check plan` from the
published wheel refuses a plan whose step opens a pull request against a list with no dated
`**Checked**` line, then passes the same plan once the line is added. The headline change of this
release, proved from what a stranger downloads rather than from the source tree.

**Steps 3 and 4 have NOT been performed.** The mirror push and the registry entry are still
outstanding, for reasons named beside them below. Do not read this section as a record that they
were done.

### Already done and verified here

- Merged to `main` (fast-forward, `6f3395d`), so nothing unmerged becomes permanent.
- The four places a version lives all say `0.1.4`: `pyproject.toml`, `src/glitch/__init__.py`,
  `registry/server.json` (top level and the package entry), and the README's `mcp-name:` marker
  matches `server.json`'s `name` character for character. The `dist` job's own consistency check
  was run locally and reports no problems. **`src/glitch/__init__.py` is the one this file never
  mentioned**; it was found by reading the workflow rather than this checklist.
- `python -m build` produced both distributions. `twine check` PASSED on both.
- The sdist carries `tests/run_all.py`, `LICENSE` and `NOTICE`.
- The wheel says `License-Expression: Apache-2.0`, carries `LICENSE` and `NOTICE`, has no
  `Private :: Do Not Upload`, and **carries the `mcp-name:` marker in the built METADATA**, not
  only in the source README. That last one is what cost 0.1.2.
- **Neither distribution contains CRLF, the sdist included.** That is new. 0.1.0 shipped CRLF in
  all 21 wheel files and all 26 sdist files; 0.1.1 fixed the wheel and left three in the sdist
  (`PKG-INFO`, `setup.cfg`, egg-info `PKG-INFO`) because setuptools generates them in text mode on
  the Windows machine doing the building. Building on Linux removes all three. This file says the
  real fix is to publish from CI so the checked artifact and the shipped artifact are the same
  file; building here is not that, but it is the first build where the sdist is clean.
- Dependency-free promise, as a delta rather than a census: `pip freeze` before and after
  installing the wheel into an empty virtualenv differs by exactly one line, `glitch-toolkit`.
- All three suites, run against the **built wheel** with the `[mcp]` extra installed:
  **40 passed, 0 failed, 0 SKIPPED**, counted from the runner. This file's pre-upload list asks for
  exactly that.
- The headline change proved from the installed wheel in a fresh git repository, not from the
  source tree: a plan whose step opens a pull request against a list, with no `**Checked**` line,
  is refused and names the line it wants; the same plan with a dated `**Checked**` line passes and
  issues a receipt.
- `site/toolkit/` still byte-identical to `src/glitch/_assets/` and `src/glitch/cli.py`. The
  version bump touched no shipped artifact, so the buyer's download did not move.
- **Mirror pre-push inspection, done.** Every commit message the subtree push would carry public
  was read for credentials, keys, customer data, revenue and campaign detail. Five keyword hits,
  all benign: this file quoting its own prohibition list, a pull-request title token, and the word
  "price" inside the cost-claim rule. `CORPUS.md` naming `client-acquisition-saas` and the rest is
  a decision the owner confirmed on 2026-09-08 and is not to be undone.

### Two builds of one commit produce four different hashes

Observed 2026-09-11 on the owner's machine. They ran `python -m build` twice, minutes apart, from
the same commit, and the preflight reported:

| build | wheel | sdist |
|---|---|---|
| first  | `e57c132c…` | `f7554997…` |
| second | `8739c0bb…` | `adddacc8…` |

Both a wheel and an sdist are archives that stamp their entries with a time, so every build differs.
Nothing is wrong; it is what setuptools does without `SOURCE_DATE_EPOCH`.

**What it means for the hashes recorded below.** They identify one specific build and nothing more.
A match proves the file is that build. A mismatch proves only that it is a different build, which is
the normal case for anybody who ran `python -m build` themselves. That is why the preflight reports a
mismatch as unknown and leaves the decision to the reader, rather than refusing: a check that refused
here would fire on every healthy local build and would be ignored within a week.

**And it sharpens the case for publishing from CI**, which this file already calls the real fix. The
earlier argument was about platform: the CRLF guard runs on Linux while releases are uploaded from
Windows. The sharper argument is that *the artefact that was checked is never the artefact that is
uploaded*, on any platform, unless one build does both. Running the tests, then building, then
uploading means the thing tested and the thing shipped are two different files that merely came from
the same source.

### The artefacts

**What shipped**, read back from PyPI's own digests on 2026-09-11, not from the terminal that
uploaded it:

- `glitch_toolkit-0.1.4-py3-none-any.whl` — 80233 bytes, sha256 `8739c0bbe959d2a253e7a8659ae3661c9a272983c7bc70aeccec4bc36f30a47b`
- `glitch_toolkit-0.1.4.tar.gz` — 95175 bytes, sha256 `adddacc8de6a15f78a2237b5f48079cbfb43ffbb00c92db424b01f9db52b2021`

That is a **Windows** build, so the three generated files carry CRLF (`PKG-INFO`, `setup.cfg`, the
egg-info `PKG-INFO`), as in 0.1.1 through 0.1.3. Nothing breaks; the entry above on reproducibility
says why it is still worth removing, and how.

**Retired, and named so nobody compares against it.** This block previously held
`737652f5…` (80166 bytes) and `a57e3012…` (94598 bytes), a Linux build made in a container while
preparing the release. It was verified there and **never uploaded**. Its hashes are bytes nobody can
obtain: worse than no hash, because a future comparison against them would refuse a legitimate file
and an audit of what shipped would be misled.

## Publishing from CI, which is where this should happen from 0.1.5

Added 2026-09-11, after 0.1.4 shipped, because that release produced the two
arguments this file had been making abstractly since 0.1.1.

**The artefact that was checked was never the artefact that shipped.** One build was made and
verified in a container; a second was made on the owner's machine; the second went to PyPI. Both
were fine and nobody could have said so from the evidence. Rebuilding and comparing cannot close
that: two runs of `python -m build` minutes apart on one machine produce four different hashes,
because wheels and sdists stamp their entries with a time. Building once and uploading that exact
file can.

**Release state written by hand went stale twice in a day** — 0.1.3 for three days, then 0.1.4
within hours of the correction. A run that uploads is the only thing that can truthfully say a
version is published.

`.github/workflows/release.yml` does it: dispatch it by hand with the version you expect, and it
refuses if the tree disagrees or if that version is already on the index, builds **once**, runs
every suite and every metadata check against that built wheel rather than against the source, then
waits for a human to approve the `pypi` environment before uploading the file it tested.

### The one-time setup, in a browser, before the first dispatch

Neither of these can be done from a session, and until both exist the workflow will fail at the
upload step:

1. **On PyPI**: the project, Settings, Publishing, add a trusted publisher — owner
   `AbstractGlitch`, repository `glitch-toolkit`, workflow `release.yml`, environment `pypi`. All
   four must match the workflow exactly or the token exchange is refused.
2. **On the mirror**: create an environment named `pypi` with required reviewers. Trusted publishing
   grants upload rights to any run of that workflow in that repository; the environment is what puts
   a person back in front of it.

Once a publish has worked this way, **delete the API token on PyPI**. Its whole purpose was to live
on a laptop, and the point of the change is that nothing has to.

### The order changes, and this is the part to actually read

The mirror push moves from third to **first**. CI cannot run on code that is not there yet.

1. `python glitch/release_preflight.py` from the repository root. Everything it checks still applies.
2. `git subtree push --prefix=glitch https://github.com/AbstractGlitch/glitch-toolkit.git main`
3. On the mirror, Actions, **release**, Run workflow, and type the version. It refuses a version the
   tree does not carry and one the index already has, so at a tree that has not been bumped it will
   refuse both the current version and the next one, which is correct.
4. Approve the `pypi` environment when it asks.
5. Confirm the marker rendered at <https://pypi.org/project/glitch-toolkit/>. Still worth doing by
   eye even though the workflow asserts it in the built metadata, because what the registry reads is
   the rendered page.
6. `mcp-publisher login github` then `mcp-publisher publish`, from `glitch/registry/`.
7. From a clean virtualenv: `pip install glitch-toolkit`, `glitch install`, `glitch status`.

### What was verified about this workflow, and what was not

**Not run.** No GitHub Actions runner was available, so the workflow itself has never executed. That
is stated rather than glossed: the first dispatch is the first time it runs, and it may fail on
something only a runner shows.

**Every inline Python block in it was extracted and executed** against this tree on 2026-09-11, with
its refusals watched to fail: the version-agreement check passes at the tree's own version and
refuses both a higher and a lower one; the index check refuses a released version and accepts an
unreleased one; the built-wheel metadata check passes on the real wheel and refuses a wheel whose
marker has been miscased; the sdist check passes and refuses one with `tests/run_all.py` removed.
Eight green, two sabotage cases caught. The YAML parses and the permissions are as intended:
`{}` at the top, `id-token: write` on the publish job alone.

**The publish action is pinned to `release/v1`, not to a commit SHA.** The machine this was written
on could not reach that repository to resolve one, and an unverified SHA would be worse than an
honest branch pin. Pinning it is a real improvement and is left as a deliberate decision for
somebody who can check the value, because that job holds `id-token: write`.

---

### Yours, in this order

**Run the preflight first. It exists because the block that used to be here failed.**

```
cd <your AbstractGlitch clone>
python glitch/release_preflight.py
```

The `cd` is not decoration and this file already got it wrong once today: the first draft of this
paragraph said "from anywhere inside your clone", which is true of the preflight's own checks and
false of the path you type to reach it. The script finds the repository root itself, so the working
directory does not matter to what it checks — only to whether the shell can find the file. From
inside `glitch/` it is `python release_preflight.py` instead.

Add `--dist <path>` if the artefacts are somewhere other than `glitch/dist/` — a downloads folder,
for instance. It checks where you are standing, that
all four version numbers and the `mcp-name` marker agree, that the artefacts are present and are the
version the tree says, that `twine` and `mcp-publisher` are actually installed, and that the version
is not already on the index. Then it prints these same steps with every path resolved to an absolute
one. **It uploads nothing and pushes nothing**; publishing stays a deliberate act.

The steps it prints, in summary, so this file still says them:

1. `twine check *` then `twine upload *`, from the directory holding the artefacts, on the machine
   with the token in `$HOME/.pypirc`.
2. **Stop.** Open <https://pypi.org/project/glitch-toolkit/> and confirm the `mcp-name` marker
   rendered in the description with that exact capitalisation. The registry reads that page rather
   than the file, and 0.1.2 skipped this.
3. `git subtree push --prefix=glitch https://github.com/AbstractGlitch/glitch-toolkit.git main`,
   from the repository root.
4. `mcp-publisher login github` then `mcp-publisher publish`, from `glitch/registry/`, with no gap
   between them because the login token expires quickly.
5. From a clean virtualenv: `pip install glitch-toolkit`, `glitch install`, `glitch status`.

**What was here before, and what it cost.** Until 2026-09-11 this section was five bare commands
with no directories:

```
twine upload dist/*
git subtree push --prefix=glitch <url> main
mcp-publisher publish
```

Run from a fresh PowerShell prompt, which opens in `C:\WINDOWS\System32`, all three failed:
`Cannot find file (or expand pattern): 'dist/*'`, `fatal: not a git repository`, and
`The term 'mcp-publisher' is not recognized`. Every one of them is a true answer to the question
actually asked and a useless answer to the question meant, which is this repository's whole subject.

The commands were not wrong. They carried their working directory in the reader's head, and that
worked for three releases because the same person ran them from the same folder each time. A habit
is not a guarantee, and the first time this was written down for somebody else it broke on the first
line. The preflight is the habit written out.

## 0.1.4 — what is in it

Sixteen commits touched `glitch/` after 0.1.3. Six of them changed files that
land in the distribution, so this is a release rather than a tidy-up.

**A third refusal in `plan_check.py`, and the reason it exists.** A step in a
plan that reaches for something outside the repository — opens a pull request
against it, lists on it, submits to it — and carries no dated `**Checked**` line
saying what was asked of the target and what it answered, is refused. An
undated `**Checked**` line is refused separately, because whether a repository
accepts anything is true on a day rather than in general.

It comes from 9 September: a repository was chosen as a listing target, its
contributing guide read and quoted, its entry format derived, its categories
compared, the list searched for duplicates. Four checks, four passes, every one
against files from a CDN that serves them the same whether a repository is alive
or archived. It had been archived since 1 August.

**No network call, and that is the design rather than a limit of it.** The
liveness check itself stays out of the package: `dependencies = []` is a promise
and a call to a repository host would spend it. What ships is the refusal to
plan around an unasked target, not the asking. The `PLAN.md` template carries
the line and the example that matters: *their CONTRIBUTING.md says pull requests
are welcome* is the description, *the API's `archived` field is false* is the
thing.

**A skip-detecting refusal in `gate_check.py`**, and the cost-claim refusal in
`plan_check.py`, both from 8 September and both already described above under
their own incidents.

**`cli.py` gained the canaries for all of it** — every new refusal is exercised
against a deliberately broken fixture on every `glitch check`, so an artifact
that has stopped refusing fails rather than passes quietly.

**One thing found by the suite rather than by review, worth carrying.** The new
refusal also fired on the fixture that exists to prove the cost-claim refusal,
because that fixture lists on a registry. Two defects in one fixture cannot
prove which refusal is still working: gutting the cost list left the fixture
rejected anyway, and the sabotage went unnoticed. `tests/test_cli.py` caught it.
A red result for the wrong reason is indistinguishable from a red result for the
right one, which is the same shape as the incident the release is about.

**Carried forward, not fixed here.** The three underspecified MCP tool
definitions below. They are listed as items for the next release and they are
also, in the same breath, "not a reason to make a release". Fixing them in this
one would falsify two texts that currently state the gaps exist — the published
`/toolkit` page and `content/SHOW_HN_GLITCH_TOOLKIT.md` — and a release is the
wrong vehicle for a change that needs two other files moved with it.

## 0.1.1 — why there is a second release so soon

Four corrections, none of which could reach a reader without a release. Three
are metadata; the fourth is a real bug in two shipped scripts that CI found
before the upload.

**The description.** The README is the PyPI project description and it is baked
into the uploaded distribution, so editing it on GitHub changes nothing on
`pypi.org`. 0.1.0 opened with "Install the practices from *Building Your Store
Or Your SaaS With Claude*" — which told a stranger who had never heard of the
book nothing about why they would want this. It now opens with the failure the
package detects. Since 0.1.0 cannot be re-uploaded, that fix is a version.

**A metadata claim that was never true.** 0.1.0 declared
`requires-python = ">=3.8"` while its build backend requires `setuptools>=77`,
and no setuptools at or above 77 runs on 3.8. The wheel would install there; the
sdist could not build. Corrected to `>=3.9`.

**Line endings.** 0.1.0 shipped CRLF in **all 21 text files of the wheel and all
26 of the sdist**, verified by downloading the published artifacts rather than
inferred: it was built on a Windows clone with `core.autocrlf=true`. Nothing
breaks — Python reads either — but one commit produced different bytes depending
on the machine, `glitch install` wrote CRLF into repositories that may lint
against it, and the `GLITCH-RECEIPT` digest hashes file bytes, so the receipt
moved with the builder instead of with the installation. `.gitattributes` now
pins the working tree to LF on every platform, and the `dist` job fails on any
CRLF in a built distribution.

Each was wrong from the first commit and stayed wrong through a release, because
nothing ran that could contradict it. That is the argument for the change below
— and the next two entries are what happened the first time something did.

**The floor was wrong a second time, and CI found it within a minute.** `>=3.9`
was still not right. Two of the six shipped scripts — `check_lanes.py` and
`gate_check.py` — annotate with `X | None`, which is PEP 604 and needs 3.10. A
def's annotations are evaluated when the def runs, so those files raised
`TypeError` at IMPORT on 3.9, not at call, which is why reading them told nobody
anything. `core · ubuntu · py3.9` went red on the first CI run that ever
existed, before 0.1.1 was uploaded.

Fixed with `from __future__ import annotations` in both, rather than by raising
`requires-python` to 3.10. The floor governs `pip install`; it does not govern
the artifacts, which are copied into a reader's repository and run with THEIR
interpreter. Dropping 3.9 to avoid a two-line fix would have inverted the
package's own argument. The same edit went into `site/toolkit/scripts/`, which
is byte-identical by contract.

**And the guard beside it was broken in the other direction.** The
dependency-free check listed everything pip could see after installing and
failed on anything that was not `glitch-toolkit`. That is a census, not a delta.
It passed on Linux and failed on the Windows runner, whose image ships pipx and
seven of its dependencies in the same interpreter — none of them from this
package. A check that fires on a healthy repository is as broken as one that
never fires. It now records `pip freeze` before the install and compares.

## CI, and the five checks it takes off this list

`.github/workflows/tests.yml` runs on the public mirror. It lives at
`glitch/.github/` in the monorepo, which is not a repository root, so GitHub
ignores it there and runs it after the subtree push — one file, CI on the
repository a stranger can actually open a pull request against.

It automates five things that were previously "remember to do it":

- the three suites, on Linux 3.9, 3.12 and 3.13, plus **Windows on 3.13** — the
  28 dependency-free tests had only ever run on Linux until they were run by hand
  on Windows on 2026-09-08 and passed, against a CRLF working tree. 3.13 because
  that is what the owner's own Windows machine runs;
- **the sdist carries `tests/run_all.py`, `LICENSE` and `NOTICE`**;
- **the wheel says `License-Expression: Apache-2.0`, carries no
  `Private :: Do Not Upload` classifier, and no longer describes itself as
  unpublished** — the exact three failures that nearly shipped on release day;
- **neither distribution contains CRLF**, so a Windows build and a Linux build of
  one commit are byte-identical;
- **the base install pulls in no dependencies**, which the README states as a
  promise and which was until now only ever true by inspection.

One guard is worth understanding before anyone edits it. `tests/run_all.py`
exits `1 if failed else 0`, so a SKIPPED suite leaves the exit code at **0**.
A workflow that only checked the exit code would go green with the ten server
tests unrun. Verified, not assumed: without the `[mcp]` extra the runner prints
`test_mcp_server.py SKIPPED` and still exits 0. So the job greps for `SKIPPED`
and fails on it. Removing that grep re-creates a false green inside the package
written to catch false greens.

Because the MCP SDK requires Python >= 3.10, the extra cannot be installed on
the floor version, which is why there are two jobs rather than one matrix: the
dependency-free promise is tested where it matters and the server where its SDK
can install.

## Before anything

Publishing is not reversible in the ways that matter. A distribution name on PyPI
cannot be taken back and given to someone else, and a version number cannot be
re-used even after a release is deleted. Both of those are decisions, not steps,
and they belong to the owner rather than to whoever happens to be running the
commands.

- [x] **The distribution name.** Decided 2026-09-08: **`glitch-toolkit`**,
      checked available on PyPI that day. It was `abstractglitch-toolkit`, a
      placeholder chosen for a package nobody intended to upload. `glitch`
      itself is taken by an unrelated 2016 library for glitching JPEGs.
      Availability was true on the day it was checked and was confirmed again
      immediately before uploading. It is now taken, by us.
- [x] **The version.** Moved off `.dev0` to **`0.1.0`** on 2026-09-08, once the
      name was decided. `.dev0` was honest while the name was open, but it is a
      pre-release that `pip install` skips without `--pre`, and shipping the
      first release as something pip ignores by default is a footgun rather
      than a caution.

Both were settled before the upload, which is the point of listing them as
decisions rather than steps. 0.1.0 is on PyPI and cannot be replaced; a
correction is 0.1.1.

**The token is now scoped to this project. Settled 2026-09-08.** The first
upload used an account-scoped token, because a project-scoped one cannot exist
before the project does. It was replaced afterwards and the old one was
**deleted on PyPI**, not merely stopped being used — a token that still works can
be found later in a file nobody remembered.

Two things to keep doing. The token lives in `$HOME/.pypirc` and is written there
with an editor, never with `$env:TWINE_PASSWORD` or an inline `Set-Content`,
both of which put the value into PSReadLine's on-disk history. And nothing
verifies a PyPI token except an upload, so the current one is untested until the
next release; if it fails at `twine upload`, generate another rather than
reaching for an account-scoped one to get unstuck.

## The console script is not the distribution name

They are independent, and only one of them is a promise to strangers. The command
is `glitch`, and it should stay `glitch` whatever the package ends up being
called: it is what the book says, what every SKILL.md says, and what the
`GLITCH-RECEIPT` lines say.

The one thing worth knowing about the collision: the unrelated `glitch` package
on PyPI is an sdist-only release from 2016. If it also installs a `glitch`
command, anyone who has both in one environment gets whichever was installed
last. The audiences do not overlap and this is not worth renaming the command
for, but it is worth knowing rather than discovering.

## Keeping the public mirror in sync

The package is developed in the private monorepo and published to
<https://github.com/AbstractGlitch/glitch-toolkit>, which is a MIRROR rather than
the home of the code. That direction matters: `site/scripts/build-tests.mjs`
resolves `../glitch/src/glitch/_assets` to prove `site/toolkit/` has not drifted
from the package, and `site/toolkit/` is a buyer's download path. Moving the tree
out of the monorepo would break that check, so it stays where it is.

To publish new commits, from the monorepo root:

```bash
git subtree push --prefix=glitch \
  https://github.com/AbstractGlitch/glitch-toolkit.git main
```

The first push was done differently, and it is worth knowing why in case the
history ever looks odd: `git subtree split --prefix=glitch -b _public_preview`
produced a branch that was INSPECTED before anything went public — 32 files, 6
commits, checked for content from `book-studio/`, `site/`, `codex/` and
`diagnostic-copilot/`, and checked again for Stripe, revenue, campaign or
infrastructure detail in the commit MESSAGES, which a subtree split carries over
verbatim. Then `git push <url> _public_preview:main`.

Do that inspection again if the monorepo ever gains a file under `glitch/` that
was not written to be read by strangers.

**`CORPUS.md` is not such a file, and this is the note that stops it being read as
one.** It names `client-acquisition-saas`, `roadmap-studio` and `floor-audit-mcp`,
describes what went wrong in each, and says the account destroyed on 30 July was the
author's own. All of that is deliberate and was confirmed by the owner on 2026-09-08,
after it was already public: the naming is the value of the file, because a failure
attributed to a real repository is harder to dismiss than the same failure anonymised.
Anonymising it would undo a decision rather than tidy an oversight, so do not. What the
inspection above is actually for is unchanged: credentials, keys, customer data,
revenue, campaign detail, and anything about the book's paid content. A mirror is only as private as the least
careful push into it, and a public commit cannot be recalled.

## The steps

```bash
rm -rf build dist src/*.egg-info
python -m build                      # sdist AND wheel, both are published
python tests/run_all.py              # 40 tests, three suites, none skipped
twine check dist/*
twine upload dist/*
```

PowerShell, because that is the shell this actually gets run in. Exactly one
line differs: `rm` is an alias for `Remove-Item`, which has no `-rf` and errors
on paths that do not exist.

```powershell
Remove-Item -Recurse -Force build, dist, src\*.egg-info -ErrorAction SilentlyContinue
python -m build
python tests\run_all.py
twine check dist/*
twine upload dist/*
```

`twine check dist/*` and `twine upload dist/*` need no change. PowerShell does
not expand globs for native commands, so twine receives the literal `dist/*` and
expands it itself — verified by passing it as a single literal argument. Wrapping
it in `Get-ChildItem` is unnecessary.

**Run these from a clone of the PUBLIC repo, not from the monorepo**, or at
least from a monorepo checkout you have confirmed is current. On release day the
monorepo's `main` still carried a README saying the package was "not published
anywhere" — that README is the PyPI description, and building from `main` would
have published that sentence permanently.

If twine's hidden token prompt will not accept a paste (it often will not on
Windows), put the token in `$HOME\.pypirc` with Notepad rather than setting
`$env:TWINE_PASSWORD`, which writes it into PSReadLine's on-disk history:

```ini
[pypi]
username = __token__
password = pypi-...
```

Then, from a clean machine and a clean virtualenv, prove the thing a user will
actually do rather than the thing you just built:

```bash
pip install glitch-toolkit
glitch install
glitch status
```

## Carry these into the next release, whenever it happens

Not blockers, and not a reason to make a release. They are here because this is
the file that gets read before an upload, and they are otherwise the kind of item
that waits forever.

**Three tool definitions do not tell an agent enough.** Found on 2026-09-09 while
working out what a directory's quality score measures, which turned out to be a
useful question independently of the score: does each tool describe itself well
enough for an agent to use it correctly? Reading `describe_tools()` in
`src/glitch/mcp_server.py` against that, three gaps, none cosmetic:

- [ ] `glitch_ledger_tail`'s `limit` carries `minimum`, `maximum` and `default`
      and **no `description`**. An agent is told the bounds and not the meaning.
- [ ] `glitch_check`'s `step` describes itself as `"one of: rules, lanes, ..."`,
      which restates the enum rather than explaining it, and never says that
      **omitting it runs all six** — behaviour the tool description mentions and
      the parameter does not.
- [ ] None of the three says *when* an agent should reach for it. Purpose is
      clear; usage guidance is absent.

What is already good and should not be disturbed while fixing those: the
behavioural transparency in `glitch_status` (a failing step usually means the
reader has not written their own file yet, which is work rather than a bug), the
consistent `glitch_*` naming, and three tools being a coherent count for a
read-only checker.

The score itself is a proxy. Fix these because an agent needs them, and let the
grade follow.

## What must be true before uploading

All five held for 0.1.0. They are a checklist for the NEXT release, not a record
of this one.

- [ ] `python tests/run_all.py` reports three suites ok, none SKIPPED. A skipped
      MCP suite means the `[mcp]` extra is not installed locally and the server
      went untested; that is not a release-blocker but it must be a decision.
- [ ] The sdist carries `tests/run_all.py`. `MANIFEST.in` exists because
      setuptools' defaults missed it, and an sdist whose documented test command
      does not work is one a packager cannot check.
- [ ] The wheel metadata says `License-Expression: Apache-2.0` and carries both
      `LICENSE` and `NOTICE`.
- [ ] No `Private :: Do Not Upload` classifier survives anywhere. Its removal
      was the deliberate act described in `pyproject.toml`; if it has come back,
      something has been reverted and the licence decision needs re-checking
      before anything is uploaded.
- [ ] `site/toolkit/` still matches `src/glitch/_assets/` and `src/glitch/cli.py`
      byte for byte. `site/scripts/build-tests.mjs` is the check. Those files are
      a buyer's download and they must not drift because a release touched them.

## Measuring adoption WITHOUT putting telemetry in the package

The build sequence asks for an install count. It must not be obtained by making
the package phone home, and this is not a preference.

`cli.py` says, in its own module docstring, "Nothing leaves your machine. There
are no network calls in this file." `token_audit.py` redacts the paths it prints
precisely because its output gets pasted into threads. The whole product is an
argument that an agent should not take actions its operator did not authorise.
A package that quietly reported installs would be doing exactly that, to the
people most likely to notice, in the one tool they installed to stop it
happening. It would be the fastest way to lose the only audience this has.

So the number comes from outside the package:

- **PyPI download counts.** PyPI publishes them; `pypistats.org` and the public
  BigQuery dataset both expose them, and neither needs a line of code here.
  Mirrors and CI inflate the number, so read the trend rather than the total.
- **The repository.** Stars, forks and clone counts, from the host's own
  insights.
- **What people say.** Issues, questions and pull requests are a worse metric
  and a better signal than any of the above: one person describing a refusal
  that fired on their production database is worth more than a thousand
  downloads by a mirror.

### The threshold, fixed before there was any data

Decided 2026-09-08, before the upload, precisely so it could not be revised in
the light of what happened. Phase 1 passes if, **by 20 October 2026**, ANY of:

- one issue or question from someone who is not the owner;
- ten GitHub stars;
- one person reporting that a check actually refused something in their own
  repository.

Download counts are explicitly NOT the gate. Two hundred downloads can be five
people and several mirrors, and a number you cannot interpret is not a
threshold. Watch them as a trend; do not let them decide this.

If none of the three has happened by that date, the honest reading is that
developers do not want this, and no amount of packaging or pricing changes that.
