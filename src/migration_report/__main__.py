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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Compare DIA analysis",
        description="""
        looks at a collection of pre-and post dia-analyze results
        and returns any ARP entries that have not reappeared in the target CSW,
        as well as any light levels out of spec post-migration.
        """
    )

    parser.add_argument("prefolder", help="Path to pre-migration analyze-dia JSON files")
    parser.add_argument("postfolder", help="Path to post-migration files")
    parser.add_argument("--debug",action="store_true",help="enable debug output")
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    pre_dir = args.prefolder
    post_dir = args.postfolder
    generate_report(pre_dir,post_dir)
    # test_dict = test()
    # test_df = pd.DataFrame.from_dict(test_dict,orient='index')
    # test_df.reset_index(drop=True)
    # test_df.rename(
    #     columns={
    #     "ont_light_alert": "ONT Rx Level",
    #     "olt_light_alert": "OLT Rx Level",
    #     }
    # )
    # test_df.to_csv("test.csv")

    # for svc, info in services_affected.items():
    #     print(f"{svc}:")
    #     for k,v in info.items():
    #         print(f"{k}: {v}")