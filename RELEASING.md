# Releasing

**0.1.0 was released on 2026-09-08** to
<https://pypi.org/project/glitch-toolkit/0.1.0/>. This file is the checklist it
went through and the record of what was decided before it.

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

**One thing is still outstanding.** The token used for the first upload is
account-scoped, because a project-scoped one cannot exist before the project
does. Replace it with a token scoped to `glitch-toolkit` and update `.pypirc`,
or delete `.pypirc` until the next release. An account-scoped token in a plain
text file can publish anything on the account.

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
was not written to be read by strangers. A mirror is only as private as the least
careful push into it, and a public commit cannot be recalled.

## The steps

```bash
rm -rf build dist src/*.egg-info
python -m build                      # sdist AND wheel, both are published
python tests/run_all.py              # 38 tests, three suites
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
