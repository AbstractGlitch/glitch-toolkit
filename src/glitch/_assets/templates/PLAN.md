# PLAN.md

What we are doing, what we are deliberately not doing, and how anyone will know
it worked. Written before the work. Approved as a separate act.

This file exists for one reason. When the result is wrong, you need to be able
to tell "it did the wrong thing" apart from "I asked for the wrong thing", and
your memory of what you meant cannot do that. It moves, and it moves toward the
version where you were clear.

Copy this into the repository the work happens in. Not into a chat window, and
not into a document nobody opens. The test is whether a session that was never
in the conversation could read this file and start.

---

## Plan: <one line, what this round is>

**Written** <date> by <who>
**Approved** <date> by <who, and it should not be the same person on both lines>
**Stages** <n>

### What we are NOT doing

This section is first on purpose. It is the half that gets skipped, it is the
half a session cannot infer, and it is the only part you can write with real
confidence on a bad day.

- <thing we are not touching this round>
- <thing that is parked rather than cancelled, and say which>
- <thing somebody will ask about, answered here so it is not reopened>

**Exceptions.** Name every one, with its reason attached. A scope list with no
exceptions is usually a scope list that has not met reality yet.

- <exception> because <reason>

### What we ARE doing

The goal in one sentence a stranger could hold:

> <goal>

- <the work, in the order it happens>

**Anything outside this repository gets asked before it gets planned around.** A
step that opens a pull request somewhere, lists on a registry, or submits to a
directory is a step about a thing you do not control, and what that thing
publishes about itself is not evidence it is open. A contributing guide reads
exactly the same from a repository that was archived in August.

So ask it one question only a live target can answer, and write the answer here
with the date you got it. One line per target.

- **Checked** <date> <target> <what was asked, and what it answered>

Bad: "their CONTRIBUTING.md says pull requests are welcome", which is the
description, not the thing. Better: "the API's `archived` field is false", or
"the banner at the top of the page", or "their last merged pull request is from
this month".

### How we will know it worked

One line per claim, specific enough that it can fail. Write this now, while you
still want it to be hard, rather than at the end when you want to be finished.

Bad: "tests pass". Better: "the checker is installed, runs, AND fails a
deliberately broken case", because installed and running is satisfied by a
copied file.

- <check> proves <claim>
- <check> proves <claim>

**Not checked by any of the above:** <say it here rather than leaving it to be
discovered>

### Stages

Each stage names itself in the work that comes out of it, so a commit message or
a status note can say `Stage 2 of 5 from the plan approved on <date>` and a
reader can find this file.

| # | stage | done when |
| --- | --- | --- |
| 1 | <stage> | <check from above> |
| 2 | <stage> | <check from above> |

---

## Deviations

Appended to, never edited. The plan above stays as it was approved.

A deviation said at the time costs one sentence. Found afterwards in a diff, it
costs the reader's confidence in every other line of this file, because they now
know the plan and the work can disagree without anybody saying so.

Same format as a findings log entry: what, when, why, and who decided.

<!-- deviations:start -->
- **<date>** The plan said <X>. Doing <Y> instead, because <reason>. Decided by
  <who>.
<!-- deviations:end -->

---

## What this file cannot do

Say this to yourself once, so the file does not get trusted past its reach.

**A plan approved by somebody who did not understand it is worse than no plan.**
No plan leaves you uncertain, and uncertain is a safe state. An approved plan you
skimmed launders a guess into a decision, and everything downstream now cites it.

**It does not stop a confident false claim.** A plan governs scope. It has
nothing to say about whether a fact somebody reported is true. That is the
findings log's job.

**A stale plan still gets followed.** It is a written thing that looks
authoritative and carries no expiry. That is why the date is at the top. Treat a
plan older than the work in front of it as a claim, not an instruction.

**It costs the thing you were doing instead.** On a small task it is not worth
paying. Use it where being wrong is expensive and skip it where it is not, or
you will stop writing plans at all.
