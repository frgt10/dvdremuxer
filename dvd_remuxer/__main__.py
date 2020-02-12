#!/usr/bin/env python3

import sys

if __package__ is None and not hasattr(sys, "frozen"):
    # direct call of __main__.py
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import dvd_remuxer

if __name__ == "__main__":
    dvd_remuxer.main()
