"""Bounded autonomy for agents working in a repository.

Six practices from *Building Your Store Or Your SaaS With Claude*, installed
into your own project and checked there. The checker's contract is that an
artifact counts as installed only when it is present, runs, AND still refuses a
deliberately broken case; anything that merely passes is treated as not wired up.

The command line is the product. Import it if you want to, but nothing in here
is a stable API yet.
"""

# Kept in step with `version` in pyproject.toml by hand, and by a check in
# .github/workflows/tests.yml because by hand is how they drift. This one is
# what `glitch-mcp` reports over the protocol, so a stale value here misidentifies
# the running server rather than merely being untidy.
__version__ = "0.1.3"
