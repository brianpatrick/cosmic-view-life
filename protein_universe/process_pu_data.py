'''

process_pu_data.py

This script is derived from Emma Broman's Jupyter notebook that processes data from the
Protein Universe (https://zenodo.org/records/8121336),associated with the publication:

Durairaj, J., Waterhouse, A.M., Mets, T. et al. Uncovering new families and folds in the
natural protein universe. Nature 622, 646–653 (2023). https://doi.org/10.1038/

The script assumes data has been downloaded and extracted to a supplied path, and relies
on the following files:

 - communities_edge_list-coordinates.csv
 - communities_summary.csv
 - communities_edge_list_no_duplicates.csv

'''

import argparse
from pathlib import Path
import pandas as pd
import shutil

def load_collate_and_center_pu_coordinates(data_path):
    print("Loading Protein Universe data...", end='', flush=True)
    inpath = Path(data_path) / Path('communities_edge_list-coordinates.csv')
    print(inpath)
    communities_coordinates = pd.read_csv(data_path / 'communities_edge_list-coordinates.csv', sep=';')
    communities_summary = pd.read_csv(data_path / 'communities_summary.csv')

    pu_data = pd.merge(communities_coordinates, communities_summary, left_on='id', right_on='Community')

    print("centering...", end='', flush=True)
    # Center the data.
    pu_data['x_centered'] = pu_data['x'] - pu_data['x'].mean()
    pu_data['y_centered'] = pu_data['y'] - pu_data['y'].mean()
    pu_data['z'] = 0
    print("done.")

    return pu_data

def make_pu_points_asset_file(pu_data_filename, asset_filename, asset_path):
    print("Writing points asset file...", end='', flush=True)
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

    print("done.")
    
def make_pu_speck_file(pu_data, data_path, speck_filename, speck_path):
    # Load in the connection data. This might take a while.
    print("Loading connection data...", end='', flush=True)
    communities_connections = pd.read_csv(data_path / 'communities_edge_list_no_duplicates.csv')
    print(f"done. {len(communities_connections)} connections.")

    print("Writing speck file...")

    # Open the speck file for writing.
    with open(speck_path / speck_filename, 'w') as speck_file:
        # For each connection, write out the coordinates. 
        for i, connection in communities_connections.iterrows():
            innode = connection['innode']
            outnode = connection['outnode']

            innode_data = pu_data[pu_data['id'] == innode]
            outnode_data = pu_data[pu_data['id'] == outnode]

            if innode_data.empty or outnode_data.empty:
                print(f"Warning: connection {i} has no data.")
                continue

            innode_data = innode_data.iloc[0]
            outnode_data = outnode_data.iloc[0]

            print("mesh -c 2 {", file=speck_file)
            print(f"  id con{i}", file=speck_file)
            print("  2", file=speck_file)
            speck_file.write(f"  {innode_data['x_centered']} {innode_data['y_centered']} {innode_data['z']}\n")
            speck_file.write(f"  {outnode_data['x_centered']} {outnode_data['y_centered']} {outnode_data['z']}\n")
            print("}", file=speck_file)

            # Every 100 connections, print a status message. Skip 0, the first one.
            if (i % 100 == 0) and (i != 0):
                print(f"\b{i}...", end='', flush=True)
            # Every 1000 connections, start a new line.
            if (i % 1000 == 0) and (i != 0):
                print()

            # Print a spinning baton to indicate progress.
            baton = ['|', '/', '-', '\\']
            print(f"\b{baton[i % 4]}", end='', flush=True)

            # Testing - let's exit after 1000 connections.
            if i > 1000:
                break

    print("\bdone.")

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

    # Do we want to skdoidop the connection lines? Processing these can take a while.
    parser.add_argument('--do_connections', action='store_true', help='Process connection data.',
                        default=False)

    return parser.parse_args()

def main():
    args = parse_args()

    pu_data = load_collate_and_center_pu_coordinates(Path(args.data_path))

    pu_data_filename = 'pu_data.csv'

    print("Writing processed PU coordinate data...", end='', flush=True)
    # Make sure the output path exists, and write the data.
    Path(args.asset_path).mkdir(parents=True, exist_ok=True)
    pu_data.to_csv(Path(args.asset_path) / pu_data_filename)
    print("done.")

    # Now make asset file.
    make_pu_points_asset_file(pu_data_filename=pu_data_filename, 
                       asset_filename='pu_points.asset',
                       asset_path=Path(args.asset_path))
    
    if args.do_connections:
        # Now make speck file.
        make_pu_speck_file(pu_data=pu_data,
                        data_path=Path(args.data_path),
                        speck_filename='pu_connections.speck',
                        speck_path=Path(args.asset_path))

if __name__ == '__main__':
    main()
