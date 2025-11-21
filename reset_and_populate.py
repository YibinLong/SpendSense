#!/usr/bin/env python3
"""
Compatibility entrypoint for Render/start commands.

Delegates to the actual implementation in scripts.reset_and_populate so
`python reset_and_populate.py` works when the working directory is the repo root.
"""

from scripts.reset_and_populate import main


if __name__ == "__main__":
    main()
