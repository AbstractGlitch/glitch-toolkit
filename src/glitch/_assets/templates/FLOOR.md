# FLOOR.md

The startup floor of this project: what a session costs before it has done any
work at all. It is paid again on every turn, so a number here that is ten
thousand too high is ten thousand per turn, all day, for the life of every
session.

Almost nobody has measured theirs. Most people have an impression formed by
watching a bar move, and the impression is usually wrong by a factor.

## The record

Two lines minimum, and each one needs a number and a date. One measurement is an
observation. Two is the only evidence that anything you did to the floor worked.

`token_audit.py --record FLOOR.md` refuses this file until you have replaced the
placeholders below with numbers you actually measured. That refusal is the
point: a template that passed unedited would certify nothing.

<!-- Replace both lines. Keep the shape: a date, the word floor, and the number. -->

    <YYYY-MM-DD>  floor <your number> tokens  (before)
    <YYYY-MM-DD>  floor <your number> tokens  (after cutting <what you cut>)

## How to measure

```
python token_audit.py --floor
```

The first number in the report is the measured floor of your most recent
session. The inventory under it is what you control, item by item, with the
part you do not control named separately rather than folded in.

## What is worth cutting, in the order it is worth cutting

1. **A project rules file that grew.** It is read on every turn of every
   session in this project. Length here is the most expensive length you own.
2. **Skills you never use.** Every skill's description loads whether or not it
   is invoked. `skillOverrides` set to `name-only` in `.claude/settings.json`
   keeps the name and drops the rest.
3. **Hook payloads.** A hook that prints a file into the session pays for that
   file on every turn afterwards. Check what yours actually emit.
4. **Global rules and global skills.** These load in every project you open,
   relevant or not. Move the project-specific ones into the project.

Measure, cut one thing, measure again, and write both numbers down here. Cutting
without the second measurement is how people spend an afternoon removing
something that cost four hundred tokens.

## What this record is not

It is not a budget and it is not a target. It is the number, and the date you
knew it. A floor from an unknown week describes a project that has since
changed, which is why the date is required and not decoration.
