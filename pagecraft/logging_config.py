"""Logging configuration for pagecraft.

Provides a module-level logger and a setup function that respects
--quiet and --verbose flags. All modules should use this logger
instead of bare print() so that output is filterable by level.

Exit codes (semantic, for shell scripting):
    0  success
    1  no valid input files found
    2  some files failed, but at least one succeeded (partial)
    3  all files failed, or output could not be written (total)
    4  unexpected error (bug)
"""

import logging
import sys

# Semantic exit codes
EXIT_SUCCESS = 0
EXIT_NO_INPUT = 1
EXIT_PARTIAL = 2
EXIT_TOTAL_FAIL = 3
EXIT_BUG = 4

logger = logging.getLogger("pagecraft")


def setup_logging(quiet: bool = False, verbose: bool = False) -> None:
    """Configure the pagecraft logger.

    - quiet:  WARNING+ only (errors and warnings, no info/progress)
    - verbose: DEBUG+ (everything, including per-file debug)
    - default: INFO+ (progress + warnings)
    """
    if quiet:
        level = logging.WARNING
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logger.setLevel(level)

    # Avoid duplicate handlers if called twice (e.g. tests).
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(
            logging.Formatter("%(levelname)s: %(message)s")
        )
        logger.addHandler(handler)
