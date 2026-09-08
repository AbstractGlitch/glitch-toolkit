# CLAUDE.md

A rules file for a store: something is bought, something is shipped, and money
moves before anyone reads the code.

Read this once before you edit it. Every rule below carries the edit that would
break it, on the line under it, because a rule with no failing case is a mood.
`rules_check.py` reads only what is between the two markers and refuses any rule
that cannot be violated, so keep the shape and delete freely. **A shorter file
that holds beats a long one that nobody follows.**

The order is not decorative. The money path is first and the customer's data is
second, because that is the order in which a mistake stops being recoverable.

Replace every `<...>` with the real thing in your repository. A rule pointing at
a path that does not exist is the first rule anybody learns to ignore.

<!-- rules:start -->
- Never change the price, the currency, or the amount charged anywhere except `<lib/pricing>`.
  Why: a price that is computed in two places is a price that disagrees with itself on a Friday.
  Violated by: writing an amount in cents into a checkout route, a component, or a test fixture

- The browser chooses what is being bought. The server chooses what it costs.
  Why: an amount that arrives in a request body is an amount a stranger can edit.
  Violated by: reading a price, a total, or a discount out of the request body

- Never write, log, or commit a live API key, a webhook signing secret, or a session token.
  Why: a secret in the history is a secret forever, and rotating it is the cheap half.
  Violated by: pasting a key into a file, a print statement, or a commit message

- Grant what somebody bought only from the payment provider's own verified event.
  Why: the success page is a URL. Anybody can visit it, twice, without paying.
  Violated by: granting access on the thanks page, or from a query parameter

- Every order write goes through `<the one order module>` and nothing else touches the store.
  Why: two writers and one file is the bug this toolkit's chapter four is about.
  Violated by: opening the order store directly from a route, a script, or a job

- Never delete customer or order data. Mark it and leave it.
  Why: a refund is reversible, a delete is not, and support will ask you next week.
  Violated by: a hard delete, a truncate, or a destructive migration on order data

- Never claim a result, a review, a rating, or a count that is not measured.
  Why: this is the one that gets the shop closed rather than merely broken.
  Violated by: writing a number of customers, a star rating, or a testimonial nobody sent

- Shipping times, returns windows, and stock come from the supplier record, never from the copy.
  Why: a page that promises three days because it reads well is a chargeback with a delay.
  Violated by: typing a delivery time into a product page

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
<where the money path lives>
<where the order store lives>
<where the customer-facing copy lives>
```
