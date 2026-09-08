"""Allow `python -m glitch` alongside the `glitch` console script."""
import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
