#!/bin/env python

"""

# CSV to OpenSpace

Datasets provided from various sources (various in this instance means Wandrille and
Takanori, as well as "The Internet") are typically provided in CSV files with at least X,
Y, and hopefully Z coordinates. A number of other parameters, loosely termed "metadata",
may also be provided. This script takes the CSV file as input creates OpenSpace files
(asset, label, etc) as necessary.

Additionally, every CSV file has slightly different parameters as far as how it's drawn by
openspace. This info is all contained in the dataset csv file and these parameters are
used to create the speck and asset files.

Labels are handled differently than points, even though they're plotted at the same
locations as the points. The labels are RenderablePointClouds that have no points, only
the locations of the labels. The label locations are in the CSV file, which must be
converted and copied to the OpenSpace asset dir as a label file. Additionally, several
different taxonomic levels and naming conventions may be used, which requires different
label files for each. Each line of the dataset CSV file determines which column in the CSV
file to use for generating labels. The 'type' column in the dataset CSV file determines
whether to make a stars or labels asset file.

This script used to create star assets as well, but these were removed because they were
not used.

"""

import argparse
import pandas as pd
import shutil
import os
import math
from pathlib import Path
import sys
import json
from src import StringRenderer

parser = argparse.ArgumentParser(description="Process input CSV files for OpenSpace.")
parser.add_argument("-i", "--input_dataset_json_file", help="Input dataset JSON file.", 
                    required=True)
parser.add_argument("-a", "--asset_dir", help="OpenSpace directory for assets.",
                    required=True)
parser.add_argument("-o", "--output_dir", help="Directory for local copy of output files.",
                    default=".")
parser.add_argument("-t", "--texture_dir", help="Directory holding texture files for points.",
                    default="textures")

# Copying assets when running this script under WSL can be very slow. We can skip this
# and use another script/utility to copy the files later. 
parser.add_argument("-s", "--skip_asset_copy", help="Verbose output.", action="store_true")
parser.add_argument("-v", "--verbose", help="Verbose output.", action="store_true")
args = parser.parse_args()

# Make a StringRenderer. This class is a singleton and keeps track of all the
# fonts loaded. This is used to render the labels to PNG files.
string_renderer = StringRenderer.StringRenderer()

# Some csv files refer to points in other CSV files in a parent-child relationship.
# Let's keep all these around because we may need to refer to them later. We'll keep
# them in a dictionary of dictionaries. The key for the first dictionary is the 
# csv_file name. The second dictionary has a few keys, "points" is the dataframe 
# created from the CSV file. "parent" is the name of the parent CSV file, if there is
# one. "parent_column" is the name of the column in the parent CSV file that refers to
# the child CSV file. "parent_point" is the name of the point in the parent CSV file
# that this child data should be centered on.
dataset_dict = {}

# Output files. We make a lot of output files, and they should all eventually go into
# the right OpenSpace asset directory. While these files are being created, there's a
# possibility that two files with the same name could be created. We'll keep track of
# all the files we create in a list, and then move them to the asset directory at the
# end of the script. We'll also add directories to be copied recursively.
output_files = []
output_directories = []

def add_output_file(filename):
    # Make sure this file isn't already in the list. Throw an exception if it is,
    # UNLESS the file is a colormap file. A colormap can be used in multiple
    # assets. Colormaps end in .cmap.
    if filename in output_files:
        # Check if the file is a colormap file. If it is, we can skip this check.
        if filename.endswith(".cmap"):
            # This is a colormap file, so we can skip this check.
            print(f"Colormap file {filename} already in output_files list. Skipping check.")
            pass
        else:
            raise Exception(f"File {filename} already in output_files list.")
    else:
        output_files.append(filename)

def add_output_directory(directory):
    # Make sure this directory isn't already in the list. Throw an exception if it is.
    if directory in output_directories:
        raise Exception(f"Directory {directory} already in output_directories list.")
    else:
        output_directories.append(directory)

# Transforms. These are global for all assets. The filename is the dataset name with
# "_transforms.asset" appended. The transform_list is a list of Transform objects that
# will be written to the transforms file. The actual filename is set in main().
transforms_filename = ""
transform_list = []

class Transform:
    def __init__(self, 
                 output_asset_position_name,
                 parent,
                 csv_filename,
                 units):
        self.output_asset_position_name = output_asset_position_name
        self.parent = parent
        self.csv_filename = csv_filename
        self.units = units

# Many assets require the transforms asset file to be imported. This helper
# function dumps those lines into the currenty open output_file, presumably
# the asset file.
def write_transform_asset_import_to_file(output_file):
    transforms_filename_base = transforms_filename.split(".")[0]
    print("local transforms = asset.require(\"./" + transforms_filename_base + "\")", file=output_file)

# Many assets (maybe all?) also require standard conversion factors. Write
# these to the current open output_file.
def write_standard_conversion_factors_to_file(output_file):
    print("local meters_in_pc = 3.0856775814913673e+16", file=output_file)
    print("local meters_in_Km = 1000", file = output_file)

def write_transform_file():

    transforms_file_path = args.output_dir + "/" + transforms_filename

    with open(transforms_file_path, "w") as transforms_file:
        # Some boilerpate that goes in every transform file.
        print("local earthTransforms = asset.require(\"scene/solarsystem/planets/earth/transforms\")", file=transforms_file)
        write_standard_conversion_factors_to_file(transforms_file)

        for transform in transform_list:
            print(f"local {transform.output_asset_position_name} = {{", file=transforms_file)
            print(f"    Identifier = \"{transform.output_asset_position_name}\",", file=transforms_file)
            if not transform.parent:
                #print( "    Parent = earthTransforms.EarthCenter.Identifier,", file=transforms_file)
                print( "    Parent = \"Earth\",", file=transforms_file)
            else:
                # Get the coordinates of the parent point. First get the dataframe for the parent
                # points. This is in the dataset_dict dictionary.
                parent_csv_file = transform.parent['csv_file']
                parent_type = transform.parent['parent_type']

                parent_df = dataset_dict[(parent_csv_file, parent_type)]['points']

                # Now get the X, Y, and Z of the parent point from the parent_df.
                parent_column = transform.parent['parent_column']
                parent_point = transform.parent['parent_point']

                # We want to get the row of the dataframe where the value in parent_point
                # is found in the parent_column. This is the parent point.
                parent_row = parent_df[parent_df[parent_column] == parent_point]

                parent_x = parent_row['x'].values[0]
                parent_y = parent_row['y'].values[0]
                parent_z = parent_row['z'].values[0]

                # Now get the transform position name from the CSV file of the parent.
                parent_position_name = ""
                for t in transform_list:
                    if t.csv_filename == parent_csv_file:
                        parent_position_name = t.output_asset_position_name

                print(f"    Parent = {parent_position_name}.Identifier,", file=transforms_file)

                print( "    Transform = {", file=transforms_file)
                print( "      Translation = {", file=transforms_file)
                print( "        Type = \"StaticTranslation\",", file=transforms_file)
                print( "        Position = {", file=transforms_file)
                print(f"          {parent_x} * meters_in_{transform.units},", file=transforms_file)
                print(f"          {parent_y} * meters_in_{transform.units},", file=transforms_file)
                print(f"          {parent_z} * meters_in_{transform.units},", file=transforms_file)
                print( "        }", file=transforms_file)
                print( "      }", file=transforms_file)
                print( "    },", file=transforms_file)
                
            print( "    GUI = {", file=transforms_file)
            print(f"        Name = \"{transform.output_asset_position_name}\",", file=transforms_file)
            print( "        Path = \"/Transforms\",", file=transforms_file)
            print( "        Hidden = true", file=transforms_file)
            print( "    }", file=transforms_file)
            print( "}", file=transforms_file)

        print("asset.onInitialize(function()", file=transforms_file)
        for transform in transform_list:
            print(f"    openspace.addSceneGraphNode({transform.output_asset_position_name})", file=transforms_file)
        print("end)", file=transforms_file)

        print("asset.onDeinitialize(function()", file=transforms_file)
        for transform in transform_list:
            print(f"    openspace.removeSceneGraphNode({transform.output_asset_position_name})", file=transforms_file)
        print("end)", file=transforms_file)

        for transform in transform_list:
            print(f"asset.export({transform.output_asset_position_name})", file=transforms_file)

    add_output_file(str(transforms_file_path))

# Check for duplicate x, y, z values. This is a common problem with data
# files. If we find any, print a warning.
def report_duplicate_xyz(input_points_df):
    duplicate_xyz = input_points_df[input_points_df.duplicated(subset=["x", "y", "z"], keep=False)]
    if len(duplicate_xyz) > 0:
        print("Warning: Found duplicate x, y, z values in the dataset.")
        print(duplicate_xyz)

def write_scene_graph_node_initializers_to_file(asset_variable_name,
                                                output_file):
    print("asset.onInitialize(function()", file=output_file)
    print(f"    openspace.addSceneGraphNode({asset_variable_name});", file=output_file)
    print("end)", file=output_file)
    print("asset.onDeinitialize(function()", file=output_file)
    print(f"    openspace.removeSceneGraphNode({asset_variable_name});", file=output_file)
    print("end)", file=output_file)
    print(f"asset.export({asset_variable_name})", file=output_file)
        

def make_points_asset_and_csv_from_dataframe(input_points_df, 
                                             filename_base,
                                             fade_targets,
                                             interaction_sphere,
                                             default_texture,
                                             size_scale_factor,
                                             size_scale_exponent,
                                             max_size,
                                             units,
                                             enabled,
                                             rendered_labels,
                                             gui_top_level,
                                             parent,
                                             colormapping,
                                             images_column_name,
                                             images_mapping,
                                             dataset_csv_filename,
                                             gui_info):
    
    #report_duplicate_xyz(input_points_df)

    # First the CSV file. This is just the points in CSV format, however we may need to
    # add color mapping columns. If specified, for each column, we make an index for each
    # unique value that is used to index into a colormap. You can then pick which color
    # index column to use in OpenSpace to color the points.
    color_index_column_suffix = "_color_index"
    color_by_columns = colormapping["color_by_columns"]
    for color_by_column in color_by_columns:
        unique_values = input_points_df[color_by_column].unique()
        num_unique_values = len(unique_values)
        color_index = 1
        color_map = {}
        for value in unique_values:
            color_map[value] = color_index
            color_index += 1

        # Add a column for this color index to the dataframe.
        color_index_column = color_by_column + color_index_column_suffix
        input_points_df[color_index_column] = input_points_df[color_by_column].map(color_map)

    # Are we also making an images asset for this dataset? If so, we need to make a new
    # CSV file that has an image index column as well. The images_mapping is a list of
    # image filenames for each unique value in the images_column_name column. So we need to
    # make a new dataframe with the following:
    # 1. The name of the entry from the orignal CSV file in the images_column_name column
    # 2. x, y, z from the original CSV file
    # 3. The image mapping filename that tell us what image file to use for each entry.
    images_csv_filename = None
    if images_column_name and images_mapping:
        # Now make a dataframe from the images_mapping file. One of the column
        # names must match the images_column_name. The other column is
        # "image_filename", the name of the image file to use for that entry.
        images_mapping_df = pd.read_csv(images_mapping)

        # The next thing we need to do is add the x, y, z coordinates to the
        # images_mapping_df dataframe from the input_points_df column, using the
        # images_column_name to match the entries.
        images_mapping_df["x"] = images_mapping_df[images_column_name].map(input_points_df.set_index(images_column_name)["x"])
        images_mapping_df["y"] = images_mapping_df[images_column_name].map(input_points_df.set_index(images_column_name)["y"])
        images_mapping_df["z"] = images_mapping_df[images_column_name].map(input_points_df.set_index(images_column_name)["z"])

        # Finally we need to add an index column for the image index. This is
        # just a sequential number for each entry. These will be used to make
        # the texture mapping .tmap file, which will have the index and the
        # image filename. The image index starts at 1, and the column name is
        # the images_column_name + "_image_index".
        images_mapping_df[f"{images_column_name}_image_index"] = range(1, len(images_mapping_df) + 1)

        # Now write the images_mapping_df dataframe to a CSV file. Also add it
        # to the list of output files.
        images_csv_filename = args.output_dir + "/" + filename_base + "_" + images_column_name + "_images.csv"
        images_mapping_df.to_csv(images_csv_filename, index=False)
        print(f"Wrote images CSV file {images_csv_filename}")
        add_output_file(images_csv_filename)

        # Next, the tmap file. This is a simple text file with two columns, the
        # image index and the image filename.
        images_tmap_filename = args.output_dir + "/" + filename_base + "_" + images_column_name + "_images.tmap"
        with open(images_tmap_filename, "w") as tmap_file:
            for index, row in images_mapping_df.iterrows():
                print(f"{row[f'{images_column_name}_image_index']} {row['image_filename']}", file=tmap_file)
        tmap_file.close()
        print(f"Wrote images tmap file {images_tmap_filename}")
        add_output_file(images_tmap_filename)

    # Next up is "rendered labels". These are rendered as textures, and each label has an
    # index into a texture file that specifies what texture to use for each index. This
    # means that for each label column, we need a label index that has a unique number for
    # each label. This keeps us from having lots of duplicate texture files.

    # We'll need the directory later for setting up the asset file. We also need just
    # the directory name for the asset file, as it uses relative paths when setting
    # up the texture directory in the asset dir using asset.resource().
    rendered_labels_dir = ""
    rendered_labels_relative_path = ""
    if (rendered_labels):
        # First make sure a directory exists for all the rendered labels.
        rendered_labels_dir = filename_base + "_rendered_labels"
        rendered_labels_relative_path = args.output_dir + "/" + rendered_labels_dir
        if not os.path.exists(rendered_labels_relative_path):
            os.makedirs(rendered_labels_relative_path)

        for label in rendered_labels:
            # Let's get the unique values in the specified label column. 
            unique_labels = input_points_df[label["column"]].unique()
            # Make a table of the unique labels and their indices.
            label_map = {}
            label_index = 1
            for label_value in unique_labels:
                if str(label_value) == "nan":
                    label_value = "NaN"
                label_map[label_value] = label_index
                label_index += 1
            
            # Add a column for this label index to the dataframe.
            label_index_column = label["column"] + "_label_index"
            input_points_df[label_index_column] = input_points_df[label["column"]].map(label_map)

            # Let's make the tmap file at the same time.
            tmap_filename = args.output_dir + "/" + filename_base + "_" + label["column"] + ".tmap"
            tmap_file = open(tmap_filename, "w")

            for curr_label in label_map.keys():
                # Get the label index for this label.
                label_index = label_map[curr_label]

                # Now render the label to a PNG file. The filename is the label column name
                # with the index appended. The text is the label value.
                rendered_label_filename = filename_base + "_" + label["column"] + "_" + str(label_index) + ".png"

                # Render the label to a PNG file. This is done by calling the StringRenderer
                # class to render the string to a PNG file.
                font_color_triple = (label["font_color"][0], label["font_color"][1], label["font_color"][2])

                # Default is to not draw a box.
                if label.get("box", False):
                    # Draw a box around the text.
                    string_renderer.render_string_to_png_with_box(text=curr_label,
                                                     font_name=label["font_file"], 
                                                     font_size=label["font_size"],
                                                     font_color_triple=font_color_triple,
                                                     filename = f"{rendered_labels_relative_path}/{rendered_label_filename}")
                else:
                    if label.get("offset", False):
                        # Draw the text with an offset.
                        string_renderer.render_string_to_png_offset(text=curr_label,
                                                        font_name=label["font_file"], 
                                                        font_size=label["font_size"],
                                                        font_color_triple=font_color_triple,
                                                        filename = f"{rendered_labels_relative_path}/{rendered_label_filename}",
                                                        offset=label["offset"])
                    else:
                        string_renderer.render_string_to_png(text=curr_label,
                                                             font_name=label["font_file"], 
                                                             font_size=label["font_size"],
                                                             font_color_triple=font_color_triple,
                                                             filename = f"{rendered_labels_relative_path}/{rendered_label_filename}")
                
                print(f"{label_index} {rendered_label_filename}", file=tmap_file)

            tmap_file.close()

            add_output_file(tmap_filename)

        # All the rendered labels go in a single dir    
        add_output_directory(rendered_labels_dir)

    # Write the CSV file of the points. This used to just cump out the XYZ coords, but now
    # it includes the color index columns as well.
    points_csv_filename = args.output_dir + "/" + filename_base + "_points.csv"
    # Local filename is just the filename with no path.
    local_points_csv_filename = os.path.basename(points_csv_filename)

    # Now just dump the points to the CSV file.
    input_points_df.to_csv(points_csv_filename, index=False)

    add_output_file(points_csv_filename)

    output_asset_filename = args.output_dir + "/" + filename_base + "_points.asset"
    output_asset_variable_name = filename_base + "_points"
    output_asset_position_name = output_asset_variable_name + "_position"

    with open(output_asset_filename, "w") as output_file:

        # The earth is the parent for all of the points, as there are many visualizations
        # where we move points from above the earth down to specific locations. Use
        # OpenSpace's provided transformations for this.
        print("local colormaps = asset.require(\"util/default_colormaps\")", file=output_file)
        write_transform_asset_import_to_file(output_file)

        # "Declare" fade var so it can be used below.
        fade_varname = ""
        if fade_targets:
            fade_varname = f"{filename_base}_fade_command"

            print(f"local {fade_varname} = {{", file=output_file)
            print(f"    Identifier = \"{fade_varname}\",", file=output_file)
            print(f"    Name = \"{fade_varname}\",", file=output_file)
            print("    Command = [[", file=output_file)
            print("      openspace.printInfo(\"Node: \" .. args.Node)", file=output_file)
            print("      openspace.printInfo(\"Transition: \" .. args.Transition)", file=output_file)
            print("", file=output_file)
            print("      if args.Transition == \"Approaching\" then", file=output_file)
            # Fade targets are made up of two parts - the overall name and the type of
            # target to fade - points, labels, etc.
            for fade_target in fade_targets:
                print(f"        openspace.setPropertyValueSingle(\"Scene.{fade_target[0] + "_" + fade_target[1]}.Renderable.Fade\", 0.0, 1.0)", file=output_file)
            print("      elseif args.Transition == \"Exiting\" then", file=output_file)
            for fade_target in fade_targets:
                print(f"        openspace.setPropertyValueSingle(\"Scene.{fade_target[0] + "_" + fade_target[1]}.Renderable.Fade\", 1.0, 1.0)", file=output_file)
            print("      end", file=output_file)
            print("    ]],", file=output_file)
            print("    IsLocal = true", file=output_file)
            print("}", file=output_file)

        transform_list.append(Transform(output_asset_position_name, parent, dataset_csv_filename, units))

        write_standard_conversion_factors_to_file(output_file)

        print(f"local {output_asset_variable_name} = {{", file=output_file)
        print(f"    Identifier = \"{output_asset_variable_name}\",", file=output_file)
        print(f"    Parent = transforms.{output_asset_position_name}.Identifier,", file=output_file)
        print( "    Renderable = {", file=output_file)
        print( "        Type = \"RenderablePointCloud\",", file=output_file)
        print(f"        Enabled = {enabled},", file=output_file)
        print( "        UseAdditiveBlending = true,", file=output_file)
        print( "        RenderBinMode = \"PostDeferredTransparent\",", file=output_file)
        print( "        SizeSettings = {", file=output_file)
        if max_size:
            print(f"            MaxSize = {max_size},", file=output_file)
            print( "            EnableMaxSizeControl = true,", file=output_file) 
        print(f"            ScaleExponent = {size_scale_exponent}, ScaleFactor = {size_scale_factor}", file=output_file)
        print( "        },", file=output_file)
        print(f"        File = asset.resource(\"{local_points_csv_filename}\"),", file=output_file)
        if default_texture:
            print(f"        Texture = {{ File = asset.resource(\"{default_texture}\") }},", file=output_file)
        print(f"        Unit = \"{units}\",", file=output_file)


        # Grab the first column in the color_by_columns list.
        color_param = color_by_columns[0] + color_index_column_suffix
        print( "        Coloring = {", file=output_file)
        print( "            ColorMapping = {", file=output_file)
        if colormapping.get("local_colormap", False):
            print(f"                File = asset.resource(\"{colormapping['colormap']}\"),", file=output_file)
            add_output_file(colormapping['colormap'])

        else:
            print(f"                File = {colormapping['colormap']},", file=output_file)
        if colormapping.get("range", False):
            print( "                ParameterOptions = {", file=output_file)

            for color_range in colormapping["range"]:
                range_low = color_range['range'][0]
                range_high = color_range['range'][1]
                key = color_range['key'] + color_index_column_suffix
                print(f"                    {{ Key = \"{key}\", Range = {{ {range_low}, {range_high} }} }}", file=output_file)
            print( "                },", file=output_file)
        print(f"                Parameter = \"{color_param}\"", file=output_file)
        print( "            }", file=output_file)
        print( "        },", file=output_file)

        #print(f"        Coloring = {{ FixedColor = {{ 1.0, 0.0, 0.0 }} }},", file=output_file)
        print("    },", file=output_file)
        print(f"    InteractionSphere = {interaction_sphere} * meters_in_{units},", file=output_file)
        print("    ApproachFactor = 1000.0,", file=output_file)
        print("    ReachFactor = 5.0,", file=output_file)
        if fade_targets:
            print(f"    OnApproach = {{ \"{fade_varname}\" }},", file=output_file)
            print(f"    OnReach = {{ \"{fade_varname}\" }},", file=output_file)
            print(f"    OnRecede = {{ \"{fade_varname}\" }},", file=output_file)
            print(f"    OnExit = {{ \"{fade_varname}\" }},", file=output_file)
        print("    GUI = {", file=output_file)
        if gui_info:
            print(f"        Path = \"/{gui_top_level}/{gui_info['path']}\",", file=output_file)
            print(f"        Name = \"{gui_info['name']}\"", file=output_file)
        else:
            print(f"        Path = \"/{gui_top_level}/Points\",", file=output_file)
            print(f"        Name = \"{output_asset_variable_name}\"", file=output_file)
        print("    }", file=output_file)
        print("}", file=output_file)
        print("asset.onInitialize(function()", file=output_file)
        if fade_targets:
            print(f"  openspace.action.registerAction({fade_varname})", file=output_file)
        print(f"    openspace.addSceneGraphNode({output_asset_variable_name});", file=output_file)
        print("end)", file=output_file)
        print("asset.onDeinitialize(function()", file=output_file)
        print(f"    openspace.removeSceneGraphNode({output_asset_variable_name});", file=output_file)
        if fade_targets:
            print(f"  openspace.action.removeAction({fade_varname})", file=output_file)
        print("end)", file=output_file)
        print(f"asset.export({output_asset_variable_name})", file=output_file)

    add_output_file(output_asset_filename)

    # Let's handle any rendered labels here as well.
    if (rendered_labels):
        # Iterate over the rendered labels and create the assets for each one.
        for label in rendered_labels:
            max_size = label.get("max_size", None)

            output_asset_variable_name = filename_base + "_" + label["column"] + "_rendered_labels"
            output_rendered_labels_asset_filename = args.output_dir + "/" + output_asset_variable_name + ".asset"
            output_asset_position_name = output_asset_variable_name + "_position"

            with open(output_rendered_labels_asset_filename, "w") as output_file:

                # The earth is the parent for all of the points, as there are many visualizations
                # where we move points from above the earth down to specific locations. Use
                # OpenSpace's provided transformations for this.
                print("local colormaps = asset.require(\"util/default_colormaps\")", file=output_file)
                write_transform_asset_import_to_file(output_file)

                # The CSV file for the points already has a transform in it, so we can
                # use that transform as the parent for the labels.
                for t in transform_list:
                    if t.csv_filename == dataset_csv_filename:
                        parent_position_name = t.output_asset_position_name

                write_standard_conversion_factors_to_file(output_file)

                print(f"local {output_asset_variable_name} = {{", file=output_file)
                print(f"    Identifier = \"{output_asset_variable_name}\",", file=output_file)
                print(f"    Parent = transforms.{parent_position_name}.Identifier,", file=output_file)
                print( "    Renderable = {", file=output_file)
                print( "        Type = \"RenderablePointCloud\",", file=output_file)
                labels_enabled = label["enabled"] if "enabled" in label else True
                labels_enabled = str(labels_enabled).lower()  # Convert to lowercase string for Lua
                print(f"        Enabled = {labels_enabled},", file=output_file)
                print( "        UseAdditiveBlending = true,", file=output_file)
                print( "        RenderBinMode = \"PostDeferredTransparent\",", file=output_file)
                print( "        SizeSettings = {", file=output_file)
                if max_size:
                    print(f"            MaxSize = {label["max_size"]},", file=output_file)
                    print( "            EnableMaxSizeControl = true,", file=output_file) 
                print(f"            ScaleExponent = {label["point_scale_exponent"]}, ScaleFactor = {label["point_scale_factor"]}", file=output_file)
                print( "        },", file=output_file)
                # The file is the CSV file from the points, above.
                print(f"        File = asset.resource(\"{local_points_csv_filename}\"),", file=output_file)
                print(f"            Unit = \"{units}\",", file=output_file)

                # Here is the different stuff, where we reference the texture column, etc.
                print( "        DataMapping = {", file=output_file)
                print(f"            TextureColumn=\"{label["column"]}_label_index\",", file=output_file)
                # This is kinda hacky. This filename has to be constructed just like above.
                print(f"            TextureMapFile=asset.resource(\"{filename_base + "_" + label["column"]}.tmap\")", file=output_file)
                print( "        },", file=output_file)
                print( "        Texture = { ", file=output_file)
                print(f"            Folder = asset.resource(\"./{rendered_labels_dir}\")", file=output_file)
                print( "        }", file=output_file)  
                print( "    },", file=output_file)

                print("    GUI = {", file=output_file)
                gui_info = label.get("gui_info", None)
                if gui_info:
                    print(f"        Path = \"/{gui_top_level}/{gui_info['path']}\",", file=output_file)
                    print(f"        Name = \"{gui_info['name']}\"", file=output_file)
                else:
                    print(f"        Path = \"/{gui_top_level}/Labels\",", file=output_file)
                    print(f"        Name = \"{output_asset_variable_name}\"", file=output_file)
                print("    }", file=output_file)
                print("}", file=output_file)

                write_scene_graph_node_initializers_to_file(output_asset_variable_name,
                                                            output_file)

            add_output_file(output_rendered_labels_asset_filename)



def make_labels_from_dataframe(input_points_df, 
                               filename_base,
                               label_column, 
                               label_size, 
                               label_minsize, 
                               label_maxsize,
                               text_color,
                               enabled,
                               units,
                               gui_top_level,
                               dataset_csv_filename,
                               gui_info):

    label_filename = args.output_dir + "/" + filename_base + "_" + label_column + ".label"
    local_label_filename = os.path.basename(label_filename)
    with open(label_filename, "w") as output_file:
        for index, row in input_points_df.iterrows():
            print(f"{row['x']} {row['y']} {row['z']} id {index} text {row[label_column]}", file=output_file)

    add_output_file(label_filename)

    # Get the position name from the Transforms list. Search by the dataset_csv_filename.
    # This is the name of the position asset that the labels will be attached to.
    output_asset_position_name = ""
    for transform in transform_list:
        if transform.csv_filename == dataset_csv_filename:
            output_asset_position_name = transform.output_asset_position_name

    # Asset filename for labels. Same name as points filename, but with the label column
    # included.
    output_asset_filename = args.output_dir + "/" + filename_base + "_" + label_column + ".asset"
    output_asset_variable_name = filename_base + "_" + label_column + "_labels"

    with open(output_asset_filename, "w") as output_file:
        write_transform_asset_import_to_file(output_file)
        write_standard_conversion_factors_to_file(output_file)

        print(f"local {output_asset_variable_name} = {{", file=output_file)
        print(f"    Identifier = \"{output_asset_variable_name}\",", file=output_file)
        print(f"    Parent = transforms.{output_asset_position_name}.Identifier,", file=output_file)
        print( "    Renderable = {", file=output_file)
        print( "        Type = \"RenderablePointCloud\",", file=output_file)
        print(f"        Enabled = {enabled},", file=output_file)
        print( "        Labels = {", file=output_file)
        print(f"            File = asset.resource(\"{local_label_filename}\"),", file=output_file)
        print(f"            Unit = \"{units}\",", file=output_file)
        print( "            FaceCamera = true,", file=output_file)
        print( "            Enabled= true,", file=output_file)
        print(f"            Size = {label_size},", file=output_file)
        if (text_color):
            print(f"            Color = {{ {text_color[0]}, {text_color[1]}, {text_color[2]} }},", file=output_file)
        print(f"            MinMaxSize = {{ {label_minsize},{label_maxsize} }}", file=output_file)
        print( "        }", file=output_file)
        print( "    },", file=output_file)
        print( "    GUI = {", file=output_file)
        if gui_info:
            print(f"        Path = \"/{gui_top_level}/{gui_info['path']}\",", file=output_file)
            print(f"        Name = \"{gui_info['name']}\"", file=output_file)
        else:
            print(f"        Path = \"/{gui_top_level}/Points\",", file=output_file)
            print(f"        Name = \"{output_asset_variable_name}\"", file=output_file)
        print("    }", file=output_file)
        print("}", file=output_file)

        write_scene_graph_node_initializers_to_file(output_asset_variable_name,
                                                    output_file)

    add_output_file(output_asset_filename)

def make_group_labels_from_dataframe(input_points_df,
                                     filename_base,
                                     label_column, 
                                     label_size, 
                                     label_minsize, 
                                     label_maxsize, 
                                     text_color,
                                     enabled,
                                     units,
                                     gui_top_level,
                                     dataset_csv_filename,
                                     gui_info):

    print("Making group labels is no longer supported in this script. Use the "
          "group_labels.py script to generate a grouped dataset, CSV file, then "
          "import that CSV file using the points import functionality.")
    
    # Exit with an error.
    sys.exit(1)

def make_branches_from_dataframe(branch_points_df,
                                 filename_base,
                                 ID_column,
                                 units,
                                 enabled,
                                 data_points_csv_filename,
                                 gui_top_level,
                                 line_opacity,
                                 line_width,
                                 gui_info):

    # First the speck and dat files. These are the points used to draw the
    # RenderableConstellationLines asset.
    branches_speck_filename = args.output_dir + "/" + filename_base + "_branches.speck"
    branches_dat_filename = args.output_dir + "/" + filename_base + "_branches.dat"
    with open(branches_speck_filename, "w") as speck, open(branches_dat_filename, "w") as dat:
        for _, row in branch_points_df.iterrows():
            print('mesh -c 1 {', file=speck)
            print(f"  id {ID_column}", file=speck)
            print('  2', file=speck)
            print(f"  {row['x0']:.8f} {row['y0']:.8f} {row['z0']:.8f}", file=speck)
            print(f"  {row['x1']:.8f} {row['y1']:.8f} {row['z1']:.8f}", file=speck)
            print('}', file=speck)

            print(f"{ID_column} {ID_column}", file=dat)
    add_output_file(branches_speck_filename)
    add_output_file(branches_dat_filename)

    # Now the asset file for the branches.
    output_asset_filename = args.output_dir + "/" + filename_base + "_branches.asset"
    output_asset_variable_name = filename_base + "_branches"

    # Branches are like labels, they're always associated with a CSV points file. Get
    # the position from the Transforms list.
    output_asset_position_name = ""
    for t in transform_list:
        if t.csv_filename == data_points_csv_filename:
            output_asset_position_name = t.output_asset_position_name

    with open(output_asset_filename, "w") as output_file:
        write_transform_asset_import_to_file(output_file)
        write_standard_conversion_factors_to_file(output_file)

        print(f"local {output_asset_variable_name} = {{", file=output_file)
        print(f"    Identifier = \"{output_asset_variable_name}\",", file=output_file)
        print(f"    Parent = transforms.{output_asset_position_name}.Identifier,", file=output_file)
        print( "    Renderable = {", file=output_file)
        print( "        Type = \"RenderableConstellationLines\",", file=output_file)
        print(f"        Colors = {{ {{ 0.6, 0.4, 0.4 }}, {{ 0.8, 0.0, 0.0 }}, {{ 0.0, 0.3, 0.8 }} }},",
                file=output_file)
        print(f"        Opacity = {line_opacity},", file=output_file)
        print(f"        Enabled = {enabled},", file=output_file)
        print(f"        File = asset.resource(\"{os.path.basename(branches_speck_filename)}\"),", file=output_file)
        print(f"        NamesFile = asset.resource(\"{os.path.basename(branches_dat_filename)}\"),", file=output_file)
        print(f"        LineWidth = {line_width},", file=output_file)
        print(f"        Unit = \"{units}\",", file=output_file)
        print( "    },", file=output_file)
        print( "    GUI = {", file=output_file)
        if gui_info:
            print(f"        Path = \"/{gui_top_level}/{gui_info['path']}\",", file=output_file)
            print(f"        Name = \"{gui_info['name']}\"", file=output_file)
        else:
            print(f"        Name = \"{output_asset_variable_name}\",", file=output_file)
            print(f"        Path = \"/{gui_top_level}/Branches\"", file=output_file)
        print( "    }", file=output_file)
        print( "}", file=output_file)

        write_scene_graph_node_initializers_to_file(output_asset_variable_name,
                                                    output_file)

    add_output_file(output_asset_filename)

def make_models_from_dataframe(model_points_df,
                               filename_base,
                               model_list,
                               data_points_csv_filename,
                               units,
                               gui_top_level):

    output_asset_filename = args.output_dir + "/" + filename_base + "_models.asset"

    # Models are like branches or labels, they're always associated with a CSV points
    # file. Get the position from the Transforms list.
    output_asset_position_name = ""
    for t in transform_list:
        if t.csv_filename == data_points_csv_filename:
            output_asset_position_name = t.output_asset_position_name

    with open(output_asset_filename, "w") as output_file:
        write_transform_asset_import_to_file(output_file)
        write_standard_conversion_factors_to_file(output_file)

        # We need to keep track of all the model assets we create so they can be
        # initialized/deinitialized/exported for OpenSpace.
        output_asset_variable_list = []

        # Now, for each model, make a new asset.
        for model in model_list:

            # Do we skip this model?
            if model.get("skip", False):
                continue

            # First let's make sure we can get the position of the model.
            model_name = model["taxon"]
            search_column = model["column"]
            model_row = model_points_df[model_points_df[search_column] == model_name]

            gui_info = model.get("gui_info", None)

            if len(model_row) == 0:
                print(f"Error: Could not find model {model_name} in the dataset.")
                sys.exit(1)

            # The asset name should have the model name in it. Replace spaces with
            # underscores. Some models have sub-models, such as tracheae of insects.
            # If there's a sub-model associated with this model, name it appropriately
            # so it doesn't conflict with the parent model.
            if "sub_model" in model:
                output_asset_variable_name = filename_base + "_" + model_name.replace(" ", "_") + "_" + model["sub_model"] + "_model"
            else:
                output_asset_variable_name = filename_base + "_" + model_name.replace(" ", "_") + "_model"

            if model["download_type"] == "url":
                print(f"local syncData_{output_asset_variable_name} = asset.resource({{", file=output_file)
                print(f"    Name = \"{output_asset_variable_name}\",", file=output_file)
                print(f"    Identifier = \"{output_asset_variable_name}\",", file=output_file)
                print(f"    Type = \"UrlSynchronization\",", file=output_file)
                print(f"    Url = \"{model['model_url']}\",", file=output_file)
                print(f"    Filename = \"{model['model_filename']}\"", file=output_file)
                print("})", file=output_file)

            print(f"local {output_asset_variable_name} = {{", file=output_file)
            print(f"    Identifier = \"{output_asset_variable_name}\",", file=output_file)
            print(f"    Parent = transforms.{output_asset_position_name}.Identifier,", file=output_file)
            print( "    Transform = {", file=output_file)
            print( "        Translation = {", file=output_file)
            print( "          Type = \"StaticTranslation\",", file=output_file)
            print( "          Position = {", file=output_file)
            print(f"            {model_row['x'].values[0]} * meters_in_{units},", file=output_file)
            print(f"            {model_row['y'].values[0]} * meters_in_{units},", file=output_file)
            print(f"            {model_row['z'].values[0]} * meters_in_{units},", file=output_file)
            print( "          }", file=output_file)
            print( "        }", file=output_file)
            print( "    },", file=output_file)
            print( "    Renderable = {", file=output_file)
            print( "        Type = \"RenderableModel\",", file=output_file)
            model_enabled = model["enabled"] if "enabled" in model else True
            print(f"        Enabled = {str(model_enabled).lower()},", file=output_file)
            print(f"        AmbientIntensity = 0.0,", file=output_file)
            print(f"        Opacity = 1.0,", file=output_file)
            if model["download_type"] == "url":
                print(f"        GeometryFile = syncData_{output_asset_variable_name} .. \"{model['model_filename']}\",", file=output_file)
            else:
                print(f"        GeometryFile = asset.resource(\"./{model['model_path']}\"),", file=output_file)
            print(f"        ModelScale = {model['model_scale']},", file=output_file)
            print( "        LightSources = {", file=output_file)
            # Default light intensity is 0.5. This is a good value for most models, but can be
            # overridden in the model JSON block
            camera_light_intensity = model.get("camera_light_intensity", 0.5)
            print(f"            {{ Identifier = \"Camera\", Type = \"CameraLightSource\", Intensity={camera_light_intensity} }}", file=output_file)
            print( "        }", file=output_file)
            print( "    },", file=output_file)


            print( "    GUI = {", file=output_file)
            if gui_info:
                print(f"        Path = \"/{gui_top_level}/{gui_info['path']}\",", file=output_file)
                print(f"        Name = \"{gui_info['name']}\"", file=output_file)
            else:
                print(f"        Name = \"{output_asset_variable_name}\",", file=output_file)
                print(f"        Path = \"/Models/{data_points_csv_filename.split(".")[0]}\"", file=output_file)
            print( "    }", file=output_file)
      

            print( "}", file=output_file)

            output_asset_variable_list.append(output_asset_variable_name)

        # Now we need to dump all the initialize  and deinitialize functions for the
        # models.
        print("asset.onInitialize(function()", file=output_file)
        for output_asset_variable_name in output_asset_variable_list:
            print(f"    openspace.addSceneGraphNode({output_asset_variable_name})", file=output_file)
        print("end)", file=output_file)
        print("asset.onDeinitialize(function()", file=output_file)
        for output_asset_variable_name in output_asset_variable_list:
            print(f"    openspace.removeSceneGraphNode({output_asset_variable_name})", file=output_file)
        print("end)", file=output_file)
        for output_asset_variable_name in output_asset_variable_list:
            print(f"asset.export({output_asset_variable_name})", file=output_file)

    add_output_file(output_asset_filename)

def make_pdb_from_dataframe(protein_points_df,
                            filename_base,
                            protein_list,
                            data_points_csv_filename,
                            units,
                            gui_top_level):

    # Let's only import pymol if we need it.
    try:
        from pymol import cmd
    except ImportError:
        print("Error: Could not import pymol. Please install it with 'pip install pymol'.") 
        sys.exit(1)

    # Now the asset file for the branches.
    output_asset_filename = args.output_dir + "/" + filename_base + "_pdb.asset"

    # PDB proteins are like branches or labels, they're always associated with a CSV points
    # file. Get the position from the Transforms list.
    output_asset_position_name = ""
    for t in transform_list:
        if t.csv_filename == data_points_csv_filename:
            output_asset_position_name = t.output_asset_position_name

    with open(output_asset_filename, "w") as output_file:
        write_transform_asset_import_to_file(output_file)
        write_standard_conversion_factors_to_file(output_file)

        output_asset_variable_list = []

        # Now, for each model, make a new asset.
        for protein in protein_list:

            # First let's make sure we can get the position of the protein.
            taxon_name = protein["taxon"]

            search_column = protein["column"]
            taxon_row = protein_points_df[protein_points_df[search_column] == taxon_name]
            if len(taxon_row) == 0:
                print(f"Error: Could not find {taxon_name} in the dataset.")
                sys.exit(1)

            pdb_code = protein["pdb_code"]

            # Now we need to get the protein model from pymol.
            cmd.reinitialize()
            cmd.fetch(pdb_code)
            glb_filename = pdb_code + ".gltf"
            glb_fullpath = args.output_dir + "/" + glb_filename

            # How to display it?
            cmd.hide("all")
            cmd.show_as(protein["show_as"])

            cmd.get_gltf(glb_fullpath, 1)

            add_output_file(glb_fullpath)

            gui_info = protein.get("gui_info", None)

            # The asset name should have the protein name in it. Replace spaces with
            # underscores.
            output_asset_variable_name = filename_base + "_" + pdb_code + "_" + \
                taxon_name.replace(" ", "_") + protein["show_as"] + \
                "_protein"

            model_offset = protein.get("model_offset", [0, 0, 0])

            print(f"local {output_asset_variable_name} = {{", file=output_file)
            print(f"    Identifier = \"{output_asset_variable_name}\",", file=output_file)
            print(f"    Parent = transforms.{output_asset_position_name}.Identifier,", file=output_file)
            print( "    Transform = {", file=output_file)
            print( "        Translation = {", file=output_file)
            print( "          Type = \"StaticTranslation\",", file=output_file)
            print( "          Position = {", file=output_file)
            print(f"            {taxon_row['x'].values[0] + model_offset[0]} * meters_in_{units},", 
                  file=output_file)
            print(f"            {taxon_row['y'].values[0] + model_offset[1]} * meters_in_{units},", 
                  file=output_file)
            print(f"            {taxon_row['z'].values[0] + model_offset[2]} * meters_in_{units},", 
                  file=output_file)
            print( "          }", file=output_file)
            print( "        }", file=output_file)
            print( "    },", file=output_file)
            print( "    Renderable = {", file=output_file)
            print( "        Type = \"RenderableModel\",", file=output_file)
            pdb_enabled = protein.get("enabled", True)
            print(f"        Enabled = {str(pdb_enabled).lower()},", file=output_file)
            print(f"        AmbientIntensity = 0.0,", file=output_file)
            print(f"        Opacity = 1.0,", file=output_file)
            print(f"        GeometryFile = asset.resource(\"./{glb_filename}\"),", file=output_file)
            print(f"        ModelScale = {protein['model_scale']},", file=output_file)
            print( "        LightSources = {", file=output_file)
            print( "            { Identifier = \"Camera\", Type = \"CameraLightSource\", Intensity=0.5 }", file=output_file)
            print( "        }", file=output_file)
            print( "    },", file=output_file)


            print( "    GUI = {", file=output_file)
            if gui_info:
                print(f"        Path = \"/{gui_top_level}/{gui_info['path']}\",", file=output_file)
                print(f"        Name = \"{gui_info['name']}\"", file=output_file)
            else:
                print(f"        Name = \"{output_asset_variable_name}\",", file=output_file)
                print(f"        Path = \"/Models/{data_points_csv_filename.split(".")[0]}\"", file=output_file)
            print( "    }", file=output_file)
      

            print( "}", file=output_file)

            output_asset_variable_list.append(output_asset_variable_name)

        # Now we need to dump all the initialize  and deinitialize functions for the
        # models.
        print("asset.onInitialize(function()", file=output_file)
        for output_asset_variable_name in output_asset_variable_list:
            print(f"    openspace.addSceneGraphNode({output_asset_variable_name})", file=output_file)
        print("end)", file=output_file)
        print("asset.onDeinitialize(function()", file=output_file)
        for output_asset_variable_name in output_asset_variable_list:
            print(f"    openspace.removeSceneGraphNode({output_asset_variable_name})", file=output_file)
        print("end)", file=output_file)
        for output_asset_variable_name in output_asset_variable_list:
            print(f"asset.export({output_asset_variable_name})", file=output_file)

    add_output_file(output_asset_filename)

def main():
    # If an output directory was specified, make sure it exists.
    if args.output_dir != ".":
        Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    # Read the dataset JSON file. This file contains the names of the CSV files
    # that contain the data for the dataset. It also contains a bunch of other
    # metadata that we will use to create the appropriate OpenSpace files.

    try:
        input_dataset = json.load(open(args.input_dataset_json_file))
    except FileNotFoundError:
        print("Error: Could not open dataset JSON file: " + args.input_dataset_json_file)
        sys.exit(1)

    # A list of all the files created for this dataset. These are all copied to
    # the asset directory.
    files_created = []

    # Get the dataset name from the input dataset JSON file. This is used to
    # make the GUI folder in openspace for this dataset.
    gui_top_level = input_dataset["gui_top_level"]

    # Set the transforms filename. This is the file that contains the transforms
    # (positions) of the assets.
    global transforms_filename
    transforms_filename = gui_top_level + "_transforms.asset"

    print("Creating dataset: " + gui_top_level)

    # For each entry in the datasets list, read the CSV file and create the
    # appropriate OpenSpace files.    
    for row in input_dataset["datasets"]:

        # If there's a "skip" entry for this row, skip it.
        if "skip" in row and row["skip"]:
            print(f"Skipping dataset: {row['csv_file']} data type {row['type']}")
            continue

        dataset_csv_filename = row["csv_file"]
        print("Reading file: " + dataset_csv_filename + "... ", end="", flush=True)

        input_points_df = pd.read_csv(dataset_csv_filename)

        # If the first column is empty, pandas renames it to "Unnamed: 0". Let's
        # rename it to "ID" so we can refer to it later. This is kinda hacky.
        if input_points_df.columns[0] == "Unnamed: 0":
            input_points_df.rename(columns={input_points_df.columns[0]: "ID"},
                                   inplace=True)
            
        # We can use the tuple of the csv filename and the type as a key to the
        # dataset_dict. This is because the same CSV file may be used for different
        # types of data, such as points and labels. We can use this key to refer to
        # the dataframe later.
        dataset_dict[(dataset_csv_filename, row["type"])] = {"points": input_points_df}
        
        # The fade_targets argument is optional. If it's not there, set it to None.
        fade_targets = row.get("fade_targets", None)

        # Let's get the base of the filename (no extension) to use for generating
        # output files. Also, replace all the periods with underscores, as periods
        # are not allowed in asset names. The file may also be in a subdir, so replace
        # all slashes with underscores. All files get placed in the output (and asset)
        # directory.
        filename_base = dataset_csv_filename.replace(".csv", "")
        filename_base = filename_base.replace(".", "_")
        filename_base = filename_base.replace("/", "_")

        parent = row.get("parent", None)
        gui_info = row.get("gui_info", None)
    
        # If there is no entry in the row for "enabled", default to true. Otherwise,
        # convert the value to a string so it can be used in the asset file.
        enabled = row.get("enabled", True)
        if enabled:
            row["enabled"] = "true"
        else:
            row["enabled"] = "false"

        text_color = row.get("text_color", None)

        # Different datasets may have different scaling factors. We need to scale
        # each dataset according to a provided, empirically determined scaling factor.
        # This is so that the points are a reasonable size in OpenSpace.
        # There are multiple column names that need to be scaled. Let's make
        # a list of them and then scale them all at once. Not every file will
        # have all these columns, so we need to check for them.
        columns_to_scale = ["x", "y", "z", "x0", "y0", "z0", "x1", "y1", "z1"]
        for column in columns_to_scale:
            if column in input_points_df.columns:
                input_points_df[column] = input_points_df[column] * row["data_scale_factor"]

        # The units for the dataset. Assume Km if not specified.
        units = "Km"
        if "units" in row:
            units = row["units"]

        if row["type"] == "labels":
            print(f"Creating {row["label_column"]} labels... ", end="", flush=True)
            # Let's do the labels first. The following functions modify the original
            # dataframe, adding lots of columns for the speck file, but making labels
            # doesn't. So we can do this first.
            make_labels_from_dataframe(input_points_df=input_points_df,
                                        filename_base=filename_base,
                                        label_column=row["label_column"],
                                        label_size=row["label_size"],
                                        label_minsize=row["label_minsize"],
                                        label_maxsize=row["label_maxsize"],
                                        enabled=row["enabled"],
                                        text_color=text_color,
                                        units=units,
                                        gui_top_level=gui_top_level,
                                        dataset_csv_filename=dataset_csv_filename,
                                        gui_info=gui_info)
            
            
        elif row["type"] == "points":
            # These are all optional arguments for making points.

            print("Creating points... ", end="", flush=True)
            make_points_asset_and_csv_from_dataframe(input_points_df=input_points_df, 
                                                        filename_base=filename_base,
                                                        fade_targets=fade_targets,
                                                        interaction_sphere=row["interaction_sphere"],
                                                        default_texture=row.get("default_texture", None),
                                                        size_scale_factor=row["point_scale_factor"],
                                                        size_scale_exponent=row["point_scale_exponent"],
                                                        max_size=row.get("max_size", None),
                                                        units=units,
                                                        enabled=row["enabled"],
                                                        rendered_labels=row.get("rendered_labels", None),
                                                        gui_top_level=gui_top_level,
                                                        parent=parent,
                                                        colormapping=row.get("colormapping", None),
                                                        images_column_name=row.get("images_column_name", None),
                                                        images_mapping=row.get("images_mapping", None),
                                                        dataset_csv_filename=dataset_csv_filename,
                                                        gui_info=gui_info)
            
        # Making grouped datasets is no longer done in this script. This code is
        # left here to catch any references to it and exit with an error.
        # Use the group_dataset.py script to generate a grouped dataset CSV file,
        # then import that CSV file as points (or whatever).
        elif row["type"] == "group_labels":
            print(f"Creating {row["label_column"]} group labels... ", end="", flush=True)
            make_group_labels_from_dataframe(input_points_df=input_points_df,
                                                filename_base=filename_base,
                                                label_column=row["label_column"],
                                                label_size=row["label_size"],
                                                label_minsize=row["label_minsize"],
                                                label_maxsize=row["label_maxsize"],
                                                enabled=row["enabled"],
                                                units=units,
                                                text_color=text_color,
                                                gui_top_level=gui_top_level,
                                                dataset_csv_filename=dataset_csv_filename,
                                                gui_info=gui_info)


        elif row["type"] == "branches":
            print("Creating branches... ", end="", flush=True)
            # If the column to specify the ID isn't given, default to "ID".
            ID_column = row.get("ID_column", "ID")
            make_branches_from_dataframe(branch_points_df=input_points_df,
                                            filename_base=filename_base,
                                            ID_column=ID_column,
                                            units=units,
                                            enabled = row["enabled"],
                                            data_points_csv_filename=row["points_file"],
                                            gui_top_level=gui_top_level,
                                            line_opacity=row["line_opacity"],
                                            line_width=row["line_width"],
                                            gui_info=gui_info)
            
        elif row["type"] == "models":
            print("Creating models... ", end="", flush=True)
            make_models_from_dataframe(model_points_df=input_points_df,
                                        filename_base=filename_base,
                                        model_list=row["model_list"],
                                        data_points_csv_filename=row["csv_file"],
                                        units=units,
                                        gui_top_level=gui_top_level)

        elif row["type"] == "pdb":
            print("Creating proteins... ", end="", flush=True)
            make_pdb_from_dataframe(protein_points_df=input_points_df,
                                    filename_base=filename_base,
                                    protein_list=row["protein_list"],
                                    data_points_csv_filename=row["csv_file"],
                                    units=units,
                                    gui_top_level=gui_top_level)

        elif row["type"] == "stars":
            print("*** Stars are no longer supported. ***")
            sys.exit(1)
 
        print("Done.")

    # Write the transforms file. This file contains the positions of all the assets
    # in the dataset.
    print(f"Writing transforms file: {transforms_filename}... ", end="", flush=True)
    write_transform_file()
    print("Done.")

    # Do we skip copying files?
    if args.skip_asset_copy:
        print("***\n*** Skipping copying files to asset directory.\n***")
        return

    print(f"Copying files to asset directory ({args.asset_dir})... ", end="", flush=True)
    Path(args.asset_dir).mkdir(parents=True, exist_ok=True)
    for file in output_files:
        if args.verbose:
            print(f"{file} ", end="", flush=True)
        try:
            shutil.copy2(file, args.asset_dir)
        except Exception as e:
            print(f"Error copying file {file} to asset directory: {e}")
            sys.exit(1)
    print("Done.")

    print("Copying directories to asset dir (on WSL this may take a few minutes)... ", end="", flush=True)
    # Copy the directory using shutil. This is kinda hacky, but it works.
    for dir in output_directories:
        if args.verbose:
            print(f"{dir} ", end="", flush=True)
        shutil.copytree(args.output_dir + "/" + dir, args.asset_dir + "/" + dir, dirs_exist_ok=True)
    print("Done.")
    
    # Copy any texture files to the output directory. Get a list of all the 
    # "default_texture" entries in the dataset JSON file. These are the texture
    # files that need to be copied.
    textures = []
    for row in input_dataset["datasets"]:
        if "default_texture" in row:
            textures.append(row["default_texture"])
    textures = list(set(textures))
    print(f"Copying textures to output directory ({args.asset_dir})... ", end="", flush=True)
    for texture in textures:
        print(f"{texture} ", end="", flush=True)
        shutil.copy2(args.texture_dir + "/" + texture, args.asset_dir)
    print("Done.")

if __name__ == '__main__':
    main()
    
