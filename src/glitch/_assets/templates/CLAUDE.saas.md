# CLAUDE.md

A rules file for a SaaS: people sign in, they see their own data and nobody
else's, and they keep paying for as long as that stays true.

Read this once before you edit it. Every rule below carries the edit that would
break it, on the line under it, because a rule with no failing case is a mood.
`rules_check.py` reads only what is between the two markers and refuses any rule
that cannot be violated, so keep the shape and delete freely. **A shorter file
that holds beats a long one that nobody follows.**

The order is not decorative. Identity is first and billing is second, because a
mistake in identity is a mistake in everybody's data at once.

Replace every `<...>` with the real thing in your repository. A rule pointing at
a path that does not exist is the first rule anybody learns to ignore.

<!-- rules:start -->
- Identity comes from the verified session and from nowhere else.
  Why: a user id in a request body is a request to be somebody else.
  Violated by: reading a user id, an account id, or a role out of a body, a query, or a header

- Every read and every write of tenant data is filtered by the session's tenant.
  Why: the leak is never dramatic. It is one query somebody forgot to scope.
  Violated by: a query against a tenant table with no tenant condition

- The browser never chooses a role, a plan, or a destination after sign-in.
  Why: whatever the browser can choose, the browser can choose wrongly on purpose.
  Violated by: elevating a role, unlocking a plan, or redirecting from a supplied value

- The session cookie carries an opaque token and nothing else.
  Why: anything readable in a cookie is anything editable in a cookie.
  Violated by: putting an email, a role, a plan, or a tenant into the cookie

- Never change what a plan costs or what it unlocks outside `<lib/plans>`.
  Why: entitlement decided in two places is a customer who is upgraded in one of them.
  Violated by: checking a plan name inline in a route, a component, or a job

- Grant and revoke access only from the payment provider's own verified event.
  Why: the success page is a URL, and a cancelled card does not visit it.
  Violated by: granting on the thanks page, or revoking from a client request

- Never write, log, or commit a live API key, a signing secret, or a session token.
  Why: a secret in the history is a secret forever, and rotating it is the cheap half.
  Violated by: pasting a key into a file, a print statement, or a commit message

- Never delete a customer's data on their behalf. Mark it and leave it.
  Why: an export request arrives after the delete, every time.
  Violated by: a hard delete or a destructive migration against customer rows

- A migration that drops or rewrites a column ships on its own, behind its own review.
  Why: bundled with a feature, it gets approved by somebody reading the feature.
  Violated by: a schema change in the same change as product work

- Do not stage files nobody asked for. Never `git add -A`.
  Why: this is how the env file, the export, and the private key get published.
  Violated by: staging with a wildcard, or committing a file you did not open

- Never report a test suite as passing unless you ran it and read the count.
  Why: a runner can exit zero having run nothing, which is what `gate_check.py` is for.
  Violated by: writing "tests pass" without the command and its output
<!-- rules:end -->

## Everything else

Below the markers is ordinary documentation: how to run the thing, where the
directories are, what the stack is. It is not checked, and it should not try to
be. Rules are the part that has to be enforceable. Notes are the part that has
to be true.

### Commands

```
<the command that starts it>
<the command that tests it>
<the command that builds it>
```

### Layout

```
<where the session and identity code lives>
<where the tenant boundary is enforced>
<where plans and entitlements are decided>
```
