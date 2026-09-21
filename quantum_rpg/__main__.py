import sys

from .cli import main

if __name__ == "__main__":
    if getattr(sys, "frozen", False) and len(sys.argv) <= 1:
        sys.argv.append("gui")
    main()
