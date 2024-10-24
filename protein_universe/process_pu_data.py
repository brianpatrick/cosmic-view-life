'''

process_pu_data.py

This script processes the Protein Universe data from https://zenodo.org/records/8121336,
associated with the publication:

Durairaj, J., Waterhouse, A.M., Mets, T. et al. Uncovering new families and folds in the
natural protein universe. Nature 622, 646–653 (2023). https://doi.org/10.1038/

The script assumes data has been downloaded and extracted to a supplied path, and
relies on the following files:

 - communities_edge_list-coordinates.csv
 - communities_summary.csv

'''

import argparse
from pathlib import Path
import pandas as pd
import shutil

def load_and_center_pu_data(data_path):
    communities_edge_list = pd.read_csv(data_path / 'communities_edge_list-coordinates.csv', sep=';')
    communities_summary = pd.read_csv(data_path / 'communities_summary.csv')

    pu_data = pd.merge(communities_edge_list, communities_summary, left_on='id', right_on='Community')

    # Center the data.
    pu_data['x_centered'] = pu_data['x'] - pu_data['x'].mean()
    pu_data['y_centered'] = pu_data['y'] - pu_data['y'].mean()
    pu_data['z'] = 0

    return pu_data

def make_pu_asset_file(pu_data_filename, asset_filename, asset_path):

    # Make sure the asset path exists.
    asset_path.mkdir(parents=True, exist_ok=True)

    # Load in the asset framework file. This is a template that we will modify.
    with open('pu_points.asset_framework', 'r') as f:
        asset_file = f.read()

    # Replace the placeholder <<ASSET_DATA_FILE>> with the actual data file.
    asset_file = asset_file.replace('<<ASSET_DATA_FILE>>', pu_data_filename)

    # Write the asset file.
    with open(asset_path / asset_filename, 'w') as f:
        f.write(asset_file)
    

# Command line arguments.
def parse_args():

    # Path to protein universe data.
    parser = argparse.ArgumentParser(description='Process Protein Universe data.')
    parser.add_argument('--data_path', type=str, required=True, help='Path to Protein Universe data.')

    # Path to OpenSpace asset directory. This will be created if it does not exist.
    parser.add_argument('--asset_path', type=str, required=True, help='Path to OS asset directory.')

    # Path to OpenSpace cache directory. If provided, this script will clear
    # the cached files so they're not read on startup. This is useful if the
    # data has been updated.
    parser.add_argument('--cache_path', type=str, help='Path to OpenSpace cache directory')

    return parser.parse_args()

def main():
    args = parse_args()

    pu_data = load_and_center_pu_data(Path(args.data_path))

    pu_data_filename = 'pu_data.csv'

    # Make sure the output path exists, and write the data.
    Path(args.asset_path).mkdir(parents=True, exist_ok=True)
    pu_data.to_csv(Path(args.asset_path) / pu_data_filename)

    # Now make asset file.
    make_pu_asset_file(pu_data_filename=pu_data_filename, 
                       asset_filename='pu_points.asset',
                       asset_path=Path(args.asset_path))

if __name__ == '__main__':
    main()
