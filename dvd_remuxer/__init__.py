import sys

from .options import parse_args
from .dvdremux import DVDRemuxer
from .lsdvd import lsdvd
from .remux_service import RemuxService


def main():
    try:
        RemuxService(lsdvd, DVDRemuxer, parse_args()).run()
    except KeyboardInterrupt:
        sys.exit("\nERROR: Interrupted by user")
    except Exception as error:
        sys.exit("\nERROR: %s" % (error))
