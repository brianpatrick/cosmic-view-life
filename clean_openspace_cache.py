#!/bin/env python

#
# clean_openspace_cache.py
#
# Files present in the OpenSpace cache will sometimes be loaded instead of updated
# asset files. Some asset files can be tagged with UseCache = false, but not everything.
# For example, updated color map files are not re-read.
#
# This script takes all the filenames in a given asset dir and removes them from
# the cache. This will force OpenSpace to re-read the files from the asset dir.

import argparse
import shutil
import os
from pathlib import Path
import sys

parser = argparse.ArgumentParser(description="Clean Openspace cache dir of all "
                                 "files present in the given asset dir.")
parser.add_argument("-a", "--asset_dir", help="Dir with assets to be cleaned from cache.",
                    required=True)
parser.add_argument("-c", "--cache_dir", help="OpenSpace cache directory.",
                    required=True)
parser.add_argument("-v", "--verbose", help="Verbose output.", action="store_true")
args = parser.parse_args()


# Get a list of all the files in the asset dir. Do not traverse subdirs.
asset_dir = Path(args.asset_dir)
# If the asset dir doesn't exist, just exit.
if not asset_dir.exists():
    print(f"Asset dir {asset_dir} does not exist.")
    sys.exit(0)
asset_files = [f for f in asset_dir.iterdir() if f.is_file()]

# For each file in the asset dir, remove the directory with the same name from the cache
# dir.
cache_dir = Path(args.cache_dir)
for asset_file in asset_files:
    cache_file = cache_dir / asset_file.name
    if cache_file.exists():
        if args.verbose:
            print(f"Removing {cache_file}")
            # Remove the directory with the name of the cache file
            shutil.rmtree(cache_file)
    else:
        if args.verbose:
            print(f"Cache file {cache_file} does not exist.")

sys.exit(0)
