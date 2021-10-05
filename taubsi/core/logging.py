import sys
import logging
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--debug", action='store_true', help="Run the script in debug mode")
args = parser.parse_args()

success_level = 25
if args.debug:
    log_level = logging.DEBUG
else:
    log_level = logging.INFO

logging.basicConfig(format="[%(asctime)s] [%(name)s] [%(levelname)-1.1s]  %(message)s", level=log_level,
                    datefmt="%H:%M:%S", stream=sys.stdout)
log = logging.getLogger("Taubsi")
