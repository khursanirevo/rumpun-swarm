"""Resolution probe for the s49 w1 grafted-suite run (temp; removable)."""

import logging
import sys

import rumpun

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("s49w1-probe")

logger.info("python: %s", sys.executable)
logger.info("sys.path[0]: %s", sys.path[0])
logger.info("rumpun binds to: %s", rumpun.__file__)
