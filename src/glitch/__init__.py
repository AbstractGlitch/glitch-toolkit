"""Bounded autonomy for agents working in a repository.

Six practices from *Building Your Store Or Your SaaS With Claude*, installed
into your own project and checked there. The checker's contract is that an
artifact counts as installed only when it is present, runs, AND still refuses a
deliberately broken case; anything that merely passes is treated as not wired up.

The command line is the product. Import it if you want to, but nothing in here
is a stable API yet.
"""

__version__ = "0.1.0.dev0"
