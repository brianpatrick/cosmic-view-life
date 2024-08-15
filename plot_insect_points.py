#!/bin/env python3

"""

plot_insect_points.py

This script plots the points of insect orders and families from Wandrille's
bubble cluster stuff.

Each family needs to be a separate asset so we can turn them on and off and
change colors. It also allows automated creation of actions to turn on and off
certain groups.

The family data is as follows:
,x,y,z,name,r,size
0,-0.28816479961714025,-0.312381271139025,0.9059689707074098,Apystomyiidae,0.0002294433604650468,1
1,-0.29009048506625545,-0.310860722844436,0.905846142597494,Natalimyzidae,0.0002294433604650468,1
2,-0.293725358123676,-0.3063362892046689,0.9061158365610431,Evocoidae,0.0002294433604650468,1
r is the radius of the point that should be displayed (normalized) and size is the actual
species count for the given family.

Each family will be an individual RenderablePointCloud asset that references a CSV file
containing points. For this initial run, each file will contain a single point, however
the file could contain many points. The color of the points is controlled in the asset
file.

"""


import argparse
import pandas as pd
import os
import json

import sys
from src import common

parser = argparse.ArgumentParser(description='Import and plot insect family data.')

# There are two ways to input parameters. The first way is to use a parameter
# file. This is a JSON file that contains all the parameters for the script. The
# second way is to specify them individually. The parameter file is specified with
# the -p flag. If the parameter file is specified, all other parameters are ignored.
# If the parameter file is not specified, the script will look for individual
# parameters. If the parameter file is specified, the script will ignore any
# individual parameters.
parser.add_argument('-p', '--param_file', dest='param_file', type=str,
                    help='The parameter file for the script.')

parser.add_argument('-i', dest='input_filename', type=str,
                    help='The input filename containing the family data.')

parser.add_argument('-o', '--output_path', dest='out_path', type=str,
                     help='Output directory for the CSV and asset files.')

parser.add_argument('--xy_scaling_factor', type=float, default=1000.0)
parser.add_argument('--z_scaling_factor',  type=float, default=1.0)

def main():
    args = parser.parse_args()

    # If a parameter file is specified, read it in and use it to set the arguments.
    if args.param_file:
        print("*** Reading parameter file {} ***".format(args.param_file))
        with open(args.param_file, 'rt') as json_file:
            args = json.load(json_file)
    else:
        # Just use the specified arguments.
        args = vars(args)

    # Passing in the args dictionary is really kinda hacky. I'd rather pass in the
    # individual parameters, but I'm in a hurry.
    load_and_process_family_data(args)


def load_and_process_family_data(args):
    family_data = pd.read_csv(args['input_filename'])

    # Sometimes the data is all placed far away from the origin. To make it easier
    # to view, we can translate the data to the origin. This is done by finding the
    # centroid of the data and then translating all the points to that location.
    # This is done by subtracting the centroid from all the points.
    centroid = family_data[['x', 'y', 'z']].mean()
    family_data['x'] = family_data['x'] - centroid['x']
    family_data['y'] = family_data['y'] - centroid['y']
    family_data['z'] = family_data['z'] - centroid['z']

    # First make sure the output path exists. If it does not, create the dir.
    if not os.path.exists(args['out_path']):
        print(f"Creating output directory: {args['out_path']}")
        os.makedirs(args['out_path'])

    # Let's also make the CSV files dir.
    csv_dirname = "csv"
    csv_path = os.path.join(args['out_path'], csv_dirname)
    if not os.path.exists(csv_path):
        print(f"Creating CSV directory: {csv_path}")
        os.makedirs(csv_path)

    # Now some filenames. Base these off the input filename.
    # The main asset filename is the same as the input filename but with
    # .asset replacing .csv.
    filename_base = os.path.basename(args['input_filename']).replace(".csv", "")
    asset_filename = filename_base + ".asset"

    asset_file = open(os.path.join(args['out_path'], asset_filename), "w")

    # Let's print the "header" info in the asset file. These are variables
    # used by all the assets.
    print(f"local text_size     = {common.TEXT_SIZE}",     file=asset_file)
    print(f"local text_min_size = {common.TEXT_MIN_SIZE}", file=asset_file)
    print(f"local text_max_size = {common.TEXT_MAX_SIZE}", file=asset_file)

    # This is the list of scene graph nodes that are the assets. These
    # need to go into some initialization code that's filled in later.
    asset_scene_graph_nodes = []

    for family_name in family_data['name']:
        # For each family, we need a new asset and a CSV file. The assets can all
        # go in a single file, but the CSV files need to be separate. The CSV files
        # are all x,y,z,name. CSV files all go in a separate dir.
        # Let's first create the CSV file.
        family_csv_filename = f"{filename_base}_{family_name}.csv"
        family_csv_fullpath = os.path.join(csv_path, family_csv_filename)
        family_csv_file = open(family_csv_fullpath, "w")

        # We also need the relative pathname for use inside the asset file.
        family_csv_relpath = os.path.join(csv_dirname, family_csv_filename)

        # Write the header for the CSV file.
        print("x,y,z,name", file=family_csv_file)

        # Now write the data for this family.
        family = family_data[family_data['name'] == family_name]

        # if the scaling factor is set, use it for everything.
        for index, row in family.iterrows():
            x = row['x'] * args['xy_scaling_factor']
            y = row['y'] * args['xy_scaling_factor']
            z = row['z'] * args['z_scaling_factor']
            name = row['name']
            print(f"{x},{y},{z},{name}", file=family_csv_file)

        # Now we need to make the asset for this CSV file. All the assets go in a 
        # single file.
        # The size of the point is relative to its species count. This is a 
        # normailized value, so we need to scale it up. These scaling factors
        # are for a given aesthetic. They can be adjusted as needed.
        scale_factor = 3.0 * row['r'] * 50.0
        scale_exponent = 5.0

        scene_graph_node_name = f"{filename_base}_{family_name}_points"
        print(f"local {scene_graph_node_name} = {{", file=asset_file)
        print(f"    Identifier = \"{scene_graph_node_name}\",", file=asset_file)
        print(f"    Renderable = {{", file=asset_file)
        print(f"        UseCaching = false,", file=asset_file)
        print(f"        Type = \"RenderablePointCloud\",", file=asset_file)
        print(f"        Coloring = {{", file=asset_file)
        print(f"            FixedColor = {{ 0.8, 0.8, 0.8 }}", file=asset_file)
        print(f"        }},", file=asset_file)
        print(f"        Opacity = 1.0,", file=asset_file)
        print(f"        SizeSettings = {{", file=asset_file)
        print(f"            ScaleFactor = {scale_factor},", file=asset_file)
        print(f"            ScaleExponent = {scale_exponent}", file=asset_file)
        print(f"        }},", file=asset_file)
        print(f"        File = asset.resource(\"./{family_csv_relpath}\"),", file=asset_file)
        print(f"        DataMapping = {{ Name=\"name\" }},", file=asset_file)
        print(f"        Labels = {{ Enabled = false, Size = text_size  }},", file=asset_file)
        print(f"        Unit = \"Km\",", file=asset_file)
        print(f"        EnablePixelSizeControl = true,", file=asset_file)
        print(f"        EnableLabelFading = false,", file=asset_file)
        print(f"        Enabled = false", file=asset_file)
        print(f"    }},", file=asset_file)
        print(f"    GUI = {{", file=asset_file)
        print(f"        Name = \"{family_name}\",", file=asset_file)
        print(f"        Path = \"/Insects/{filename_base}\"", file=asset_file)
        print(f"    }}", file=asset_file)
        print(f"}}", file=asset_file)

        asset_scene_graph_nodes.append(scene_graph_node_name)

    #
    # Actions
    #

    action_names = []

    # Now let's make an action that turns all the scene graph nodes on.
    all_on_action_name = f"all_{filename_base}_on"
    print(f"local {all_on_action_name} = {{", file=asset_file)
    print(f"    Identifier = \"{all_on_action_name}\",", file=asset_file)
    print(f"    Name = \"{all_on_action_name}\",", file=asset_file)
    print("    Command = [[", file=asset_file)
    for node in asset_scene_graph_nodes:
        print(f"        openspace.setPropertyValueSingle(\"Scene.{node}.Renderable.Enabled\", true)", file=asset_file)
    print("    ]],", file=asset_file)
    print(f"    Documentation = \"All {filename_base} on\",", file=asset_file)
    print(f"    GuiPath = \"/{filename_base}\",", file=asset_file)
    print(f"    IsLocal = false", file=asset_file)
    print(f"}}", file=asset_file)
    action_names.append(all_on_action_name)

    # ... and off.
    all_off_action_name = f"all_{filename_base}_off"
    print(f"local {all_off_action_name} = {{", file=asset_file)
    print(f"    Identifier = \"{all_off_action_name}\",", file=asset_file)
    print(f"    Name = \"{all_off_action_name}\",", file=asset_file)
    print("    Command = [[", file=asset_file)
    for node in asset_scene_graph_nodes:
        print(f"        openspace.setPropertyValueSingle(\"Scene.{node}.Renderable.Enabled\", false)", file=asset_file)
    print("    ]],", file=asset_file)
    print(f"    Documentation = \"All {filename_base} off\",", file=asset_file)
    print(f"    GuiPath = \"/{filename_base}\",", file=asset_file)
    print(f"    IsLocal = false", file=asset_file)
    print(f"}}", file=asset_file)
    action_names.append(all_off_action_name)

    # Turn all labels on.
    all_labels_on_action_name = f"all_{filename_base}_labels_on"
    print(f"local {all_labels_on_action_name} = {{", file=asset_file)
    print(f"    Identifier = \"{all_labels_on_action_name}\",", file=asset_file)
    print(f"    Name = \"{all_labels_on_action_name}\",", file=asset_file)
    print("    Command = [[", file=asset_file)
    for node in asset_scene_graph_nodes:
        print(f"        openspace.setPropertyValueSingle(\"Scene.{node}.Renderable.Labels.Enabled\", true)", file=asset_file)
    print("    ]],", file=asset_file)
    print(f"    Documentation = \"All {filename_base} labels on\",", file=asset_file)
    print(f"    GuiPath = \"/{filename_base}\",", file=asset_file)
    print(f"    IsLocal = false", file=asset_file)
    print(f"}}", file=asset_file)
    action_names.append(all_labels_on_action_name)

    # Turn all labels off.
    all_labels_off_action_name = f"all_{filename_base}_labels_off"
    print(f"local {all_labels_off_action_name} = {{", file=asset_file)
    print(f"    Identifier = \"{all_labels_off_action_name}\",", file=asset_file)
    print(f"    Name = \"{all_labels_off_action_name}\",", file=asset_file)
    print("    Command = [[", file=asset_file)
    for node in asset_scene_graph_nodes:
        print(f"        openspace.setPropertyValueSingle(\"Scene.{node}.Renderable.Labels.Enabled\", false)", file=asset_file)
    print("    ]],", file=asset_file)
    print(f"    Documentation = \"All {filename_base} labels off\",", file=asset_file)
    print(f"    GuiPath = \"/{filename_base}\",", file=asset_file)
    print(f"    IsLocal = false", file=asset_file)
    print(f"}}", file=asset_file)
    action_names.append(all_labels_off_action_name)



    # Now we need to write the initialization code for the asset file.
    print("asset.onInitialize(function()", file=asset_file)
    for node in asset_scene_graph_nodes:
        print(f"    openspace.addSceneGraphNode({node})", file=asset_file)
    for action_name in action_names:
        print(f"    openspace.action.registerAction({action_name})", file=asset_file)
    print("end)", file=asset_file)

    # And the deinitialization code.
    print("asset.onDeinitialize(function()", file=asset_file)
    for node in asset_scene_graph_nodes:
        print(f"    openspace.removeSceneGraphNode({node})", file=asset_file)
    for action_name in action_names:
        print(f"    openspace.action.removeAction({action_name})", file=asset_file)
    print("end)", file=asset_file)

    for node in asset_scene_graph_nodes:
        print(f"asset.export({node})", file=asset_file)
    for action_name in action_names:
        print(f"asset.export({action_name})", file=asset_file)

if __name__ == "__main__":
    main()

