import pandas as pd
import json 
import os
from typing import Union
import re
from pprint import pprint
import logging
import argparse
from .migration_report import *
logger = logging.getLogger(__name__)

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="Compare DIA analysis",
        description="""
        looks at a collection of pre-and post dia-analyze results
        and returns any ARP entries that have not reappeared in the target CSW,
        as well as any light levels out of spec post-migration.
        """
    )

    parser.add_argument("folder", help="Path to pre-migration analyze-dia JSON files")
    parser.add_argument("-p","--postfolder", help="Path to post-migration files")
    parser.add_argument("--debug",action="store_true",help="enable debug output")
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
    pre_dir = args.folder
    if args.postfolder:
        post_dir = args.postfolder
        generate_report(pre_dir,post_dir)
    else:
        print(get_arp_table(pre_dir).to_markdown(tablefmt="rounded_outline"))


if __name__ == "__main__":
    main()