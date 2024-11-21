#!/bin/env python

"""

# CSV to OpenSpace

Datasets provided from various sources (various in this instance means
Wandrille and Takanori, as well as "The Internet") are typically provided in
CSV files with at least X, Y, and hopefully Z coordinates. A number of other
parameters, loosely termed "metadata", may also be provided. This script takes
the CSV file as input, centers and scales the points as necessary for display
in openspace, and then creates OpenSpace files (asset, label, etc) as necessary.

Originally, this script created stars and labels, and this stuff still works. However,
the preferred method is to use RenderablePointCloud as it is more flexible, specifically
regarding point sizes and colors.

For Stars, first is the speck file, which contains the actual XYZ coordinates of the
points, drawn using RenderableStars. We also need to create label files, which are
RenderablePointClouds, except without the actual points (though it does have point
locations for the labels). These turn into individual asset files. Each set of stars can
have more than one set of labels.

Additionally, every CSV file has slightly different parameters as far as how it's drawn by
openspace. This info is all contained in the dataset csv file and these parameters are
used to create the speck and asset files.

Labels are handled differently than stars, even though they're plotted at the same
locations as the stars. The labels are RenderablePointClouds that have no points, only the
locations of the labels. The label locations are in the CSV file, which must be converted
and copied to the OpenSpace asset dir as a label file. Additionally, several different
taxonomic levels and naming conventions may be used, which requires different label files
for each. Each line of the dataset CSV file determines which column in the CSV file to use
for generating labels. The 'type' column in the dataset CSV file determines whether to
make a stars or labels asset file.

Alternatively, or additionally, points can be rendered as RenderablePointClouds. These are
very similar to the stars, except for some parameter differences regarding size and color.
Stars are a bit less flexible with colors, but a bit more flexible regarding sizes. Points
can also have a custom glyph/texture, which (I think) is not available for stars.

"""

import argparse
import pandas as pd
from glob import glob
import shutil
import os
import math
from pathlib import Path
import sys

parser = argparse.ArgumentParser(description="Process input CSV files for OpenSpace.")
parser.add_argument("-i", "--input_dataset_csv_file", help="Input dataset CSV file.", 
                    required=True)
parser.add_argument("-c", "--cache_dir", help="OpenSpace cache directory.",
                    required=True)
parser.add_argument("-a", "--asset_dir", help="OpenSpace directory for assets.",
                    required=True)
parser.add_argument("-o", "--output_dir", help="Directory for local copy of output files.",
                    default=".")
parser.add_argument("-t", "--texture_dir", help="Directory holding texture files for points.",
                    default="textures")
parser.add_argument("-v", "--verbose", help="Verbose output.", action="store_true")
args = parser.parse_args()

def make_stars_speck_from_dataframe(input_points_df, filename_base,
                                    lum, absmag, colorb_v, texnum):

    output_speck_filename = args.output_dir + "/" + filename_base + ".speck"

    with open(output_speck_filename, "w") as output_file:
        # Dump the speck file header info. 
        print("datavar 0 colorb_v", file=output_file)
        print("datavar 1 lum", file=output_file)
        print("datavar 2 absmag", file=output_file)
        print("datavar 3 appmag", file=output_file)
        print("datavar 4 texnum", file=output_file)
        print("datavar 5 distly", file=output_file)
        print("datavar 6 dcalc", file=output_file)
        print("datavar 7 plx", file=output_file)
        print("datavar 8 plxerr", file=output_file)
        print("datavar 9 vx", file=output_file)
        print("datavar 10 vy", file=output_file)
        print("datavar 11 vz", file=output_file)
        print("datavar 12 speed", file=output_file)
        print("texturevar 4", file=output_file)
        print("texture -M 1 halo.sgi", file=output_file)

        # Let's add columns for all the data we need to add to the speck file.
        input_points_df["colorb_v"] = colorb_v
        input_points_df["lum"] = lum
        input_points_df["absmag"] = absmag
        input_points_df["appmag"] = 0.0
        input_points_df["texnum"] = texnum
        input_points_df["distly"] = 0.0
        input_points_df["dcalc"] = 0
        input_points_df["plx"] = 0.0
        input_points_df["plxerr"] = 0.0
        input_points_df["vx"] = 0
        input_points_df["vy"] = 0
        input_points_df["vz"] = 0
        input_points_df["speed"] = 0

        # For each row in the CSV file (pandas dataframe), we will write a line to the output file.
        num_rows = len(input_points_df)
        for index, row in input_points_df.iterrows():
            # Split the line into a list of strings.
            datavars = []

            datavars.append(str(row["x"]))
            datavars.append(str(row["y"]))
            datavars.append(str(row["z"]))
            
            datavars.append(str(row["colorb_v"]))
            #scale_fac = index / num_rows
            #datavars.append(str(scale_fac))

            datavars.append(str(row["lum"]))
            datavars.append(str(row["absmag"]))
            datavars.append(str(row["appmag"]))
            datavars.append(str(row["texnum"]))
            datavars.append(str(row["distly"]))
            datavars.append(str(row["dcalc"]))
            datavars.append(str(row["plx"]))
            datavars.append(str(row["plxerr"]))
            datavars.append(str(row["vx"]))
            datavars.append(str(row["vy"]))
            datavars.append(str(row["vz"]))
            datavars.append(str(row["speed"]))

            # Write the modified line to the output file.
            output_file.write(" ".join(datavars) + "\n")

    # Return the name of the speck file we created.
    return([output_speck_filename])

def make_stars_asset_from_dataframe(input_points_df, 
                                    input_points_world_position,
                                    filename_base, 
                                    magnitude_exponent,
                                    core_multiplier,
                                    core_gamma,
                                    core_scale,
                                    glare_multiplier,
                                    glare_gamma,
                                    glare_scale,
                                    fade_targets):

    output_filename = args.output_dir + "/" + filename_base + ".asset"
    output_asset_position_name = filename_base + "_position"

    with open(output_filename, "w") as output_file:
        print("local sunspeck = asset.resource({", file=output_file)
        print("  Name = \"Stars Speck Files\",", file=output_file)
        print("  Type = \"HttpSynchronization\",", file=output_file)
        print("  Identifier = \"digitaluniverse_sunstar_speck\",", file=output_file)
        print("  Version = 1", file=output_file)
        print("})", file=output_file)
        print("", file=output_file)
        """
        print("local colormaps = asset.resource({", file=output_file)
        print("  Name = \"Stars Color Table\",", file=output_file)
        print("  Type = \"HttpSynchronization\",", file=output_file)
        print("  Identifier = \"stars_colormap\",", file=output_file)
        print("  Version = 3", file=output_file)
        print("})", file=output_file)
        print("", file=output_file)
        """
        print("local textures = asset.resource({", file=output_file)
        print("  Name = \"Stars Textures\",", file=output_file)
        print("  Type = \"HttpSynchronization\",", file=output_file)
        print("  Identifier = \"stars_textures\",", file=output_file)
        print("  Version = 1", file=output_file)
        print("})", file=output_file)
        print("", file=output_file)

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
            for fade_target in fade_targets:
                print(f"        openspace.setPropertyValueSingle(\"Scene.{fade_target}.Renderable.Fade\", 0.0, 1.0)", file=output_file)
            print("      elseif args.Transition == \"Exiting\" then", file=output_file)
            for fade_target in fade_targets:
                print(f"        openspace.setPropertyValueSingle(\"Scene.{fade_target}.Renderable.Fade\", 1.0, 1.0)", file=output_file)
            print("      end", file=output_file)
            print("    ]],", file=output_file)
            print("    IsLocal = true", file=output_file)
            print("}", file=output_file)

        print("local meters_in_pc = 3.0856775814913673e+16", file=output_file)
        print(f"local {output_asset_position_name} = {{", file=output_file)
        print(f"    Identifier = \"{output_asset_position_name}\",", file=output_file)
        print("  Transform = {", file=output_file)
        print("    Translation = {", file=output_file)
        print("      Type = \"StaticTranslation\",", file=output_file)
        print("      Position = {", file=output_file)
        print(f"        {input_points_world_position["x"]} * meters_in_pc,", file=output_file)
        print(f"        {input_points_world_position["y"]} * meters_in_pc,", file=output_file)
        print(f"        {input_points_world_position["z"]} * meters_in_pc,", file=output_file)
        print("      }", file=output_file)
        print("     }", file=output_file)
        print("    },", file=output_file)
        print("  GUI = {", file=output_file)
        print(f"    Name = \"{output_asset_position_name}\",", file=output_file)
        print(f"    Path = \"/Positions\",", file=output_file)
        print(f"    Hidden = true", file=output_file)
        print("  }", file=output_file)
        print("}", file=output_file)

        # Hack - colormap file.
        cmap_filename = args.output_dir + "/" + filename_base + ".cmap"
        with open(cmap_filename, "w") as cmap_file:
            print("# OpenSpace colormap file", file=cmap_file)
            print("", file=cmap_file)
            print("5", file=cmap_file)
            print("1.0 1.0 1.0 0.5", file=cmap_file)
            print("1.0 0.0 0.0 1.0", file=cmap_file)
            print("0.0 1.0 0.0 1.0", file=cmap_file)
            print("0.0 0.0 1.0 1.0", file=cmap_file)
            print("1.0 1.0 1.0 1.0", file=cmap_file)
            cmap_file.close()

        print(f"local {filename_base}_speck = asset.resource(\"{filename_base}.speck\")", file=output_file)
        print(f"local {filename_base}_color = asset.resource(\"{cmap_filename}\")", file=output_file)
        print("", file=output_file)
        print(f"local {filename_base} = {{", file=output_file)
        print(f"  Identifier = \"{filename_base}\",", file=output_file)
        print(f"  Parent = {output_asset_position_name}.Identifier,", file=output_file)
        print(f"  Renderable = {{", file=output_file)
        print("    UseCaching = false,", file=output_file)
        print("    Type = \"RenderableStars\",", file=output_file)
        print(f"    File = {filename_base}_speck,", file=output_file)
        print("    Core = {", file=output_file)
        print("      Texture = textures .. \"glare.png\",", file=output_file)
        print(f"      Multiplier = {core_multiplier},", file=output_file)
        print(f"      Gamma = {core_gamma},", file=output_file)
        print(f"      Scale = {core_scale}", file=output_file)
        print("    },", file=output_file)
        print("    Glare = {", file=output_file)
        print("      Texture = textures .. \"halo.png\",", file=output_file)
        print(f"      Multiplier = {glare_multiplier},", file=output_file)
        print(f"      Gamma = {glare_gamma},", file=output_file)
        print(f"      Scale = {glare_scale}", file=output_file)
        print("    },", file=output_file)
        print(f"    MagnitudeExponent = {magnitude_exponent},", file=output_file)
        print(f"    ColorMap = {filename_base}_color,", file=output_file)
        print("     ColorOption = \"Other Data\",", file=output_file)
        print("    OtherData = \"texnum\",", file=output_file)
        print(f"    OtherDataColorMap = {filename_base}_color,", file=output_file)
        print(f"    OtherDataValueRange = {{ 0.0, 4.0 }},", file=output_file)
        print("    SizeComposition = \"Distance Modulus\",", file=output_file)
        print("    DataMapping = {", file=output_file)
        print("      Bv = \"colorb_v\",", file=output_file)
        print("      Luminance = \"lum\",", file=output_file)
        print("      AbsoluteMagnitude = \"absmag\",", file=output_file)
        print("      ApparentMagnitude = \"appmag\",", file=output_file)
        print("      Vx = \"vx\",", file=output_file)
        print("      Vy = \"vy\",", file=output_file)
        print("      Vz = \"vz\",", file=output_file)
        print("      Speed = \"speed\"", file=output_file)
        print("    },", file=output_file)
        print("    DimInAtmosphere = true", file=output_file)
        print("  },", file=output_file)
        print("    InteractionSphere = 1 * meters_in_pc,", file=output_file)
        print("    ApproachFactor = 1000.0,", file=output_file)
        print("    ReachFactor = 5.0,", file=output_file)
        print("", file=output_file)
        if fade_targets:
            print(f"    OnApproach = {{ \"{fade_varname}\" }},", file=output_file)
            print(f"    OnReach = {{ \"{fade_varname}\" }},", file=output_file)
            print(f"    OnRecede = {{ \"{fade_varname}\" }},", file=output_file)
            print(f"    OnExit = {{ \"{fade_varname}\" }},", file=output_file)
        print("  GUI = {", file=output_file)
        print(f"    Name = \"{filename_base}\",", file=output_file)
        print(f"    Path = \"/Stars\",", file=output_file)
        print("  }", file=output_file)
        print("}", file=output_file)
        print("asset.onInitialize(function()", file=output_file)
        if fade_targets:
            print(f"  openspace.action.registerAction({fade_varname})", file=output_file)
        print(f"  openspace.addSceneGraphNode({output_asset_position_name})", file=output_file)
        print(f"  openspace.addSceneGraphNode({filename_base})", file=output_file)
        print("end)", file=output_file)
        print("asset.onDeinitialize(function()", file=output_file)
        print(f"  openspace.removeSceneGraphNode({filename_base})", file=output_file)
        print(f"  openspace.removeSceneGraphNode({output_asset_position_name})", file=output_file)
        if fade_targets:
            print(f"  openspace.action.removeAction({fade_varname})", file=output_file)
        print("end)", file=output_file)
        print(f"asset.export({output_asset_position_name})", file=output_file)
        print(f"asset.export({filename_base})", file=output_file)

    # Return the name of the asset file we created.
    return([output_filename, cmap_filename])

def make_points_asset_and_csv_from_dataframe(input_points_df, 
                                             input_points_world_position,
                                             filename_base,
                                             fade_targets,
                                             color_by_column,
                                             default_texture):
    output_files = []

    # First the CSV file. This is just the points in CSV format, however we may need to
    # add a color column. If specified, we need to look at the color_by_column and
    # figure out how many unique values there are in that column. We'll assign a color
    # index between 1 and whatever the number of unique values is. We'll then use a
    # colormap to assign a color to each index.
    if str(color_by_column) != "nan":
        unique_values = input_points_df[color_by_column].unique()
        num_unique_values = len(unique_values)
        color_index = 1
        color_map = {}
        for value in unique_values:
            color_map[value] = color_index
            color_index += 1

        # Add the color column to the dataframe.
        input_points_df["color"] = input_points_df[color_by_column].map(color_map)

        # Add another column that is the value of the color_by_column. This is useful for
        # labels.
        input_points_df["color_by_column"] = input_points_df[color_by_column]
    else:
        color_by_column = False

    # Now a color file, since we know how many colors we need.
    color_filename = args.output_dir + "/" + filename_base + ".cmap"
    color_local_filename = os.path.basename(color_filename)
    with open(color_filename, "w") as color_file:
        print("# OpenSpace colormap file", file=color_file)
        print("", file=color_file)
        #print(f"{num_unique_values}", file=color_file)
        #for value in unique_values:
        #    print(f"1.0 0.0 0.0 1.0", file=color_file)
        print("5", file=color_file)
        print("1.0 0.0 0.0 1.0", file=color_file)
        print("0.0 1.0 0.0 1.0", file=color_file)
        print("0.0 0.0 1.0 1.0", file=color_file)
        print("1.0 0.0 1.0 1.0", file=color_file)
        print("0.0 1.0 1.0 1.0", file=color_file)
        color_file.close()
    output_files.append(color_filename)

    # Now write the CSV file.
    points_csv_filename = args.output_dir + "/" + filename_base + "_points.csv"
    # Local filename is just the filename with no path.
    local_points_csv_filename = os.path.basename(points_csv_filename)
    with open(points_csv_filename, "w") as output_file:
        if color_by_column:
            print(f"x,y,z,color,{color_by_column}", file=output_file)
        else:
            print("x,y,z", file=output_file)
        for index, row in input_points_df.iterrows():
            if color_by_column:
                print(f"{row['x']},{row['y']},{row['z']},{row['color']},{row['color_by_column']}", file=output_file)
            else:
                print(f"{row['x']},{row['y']},{row['z']}", file=output_file)
        output_file.close()

    output_files.append(points_csv_filename)

    # Next the asset file for the label file. Same name as the label file, but with .asset
    # extension.
    output_asset_filename = args.output_dir + "/" + filename_base + "_points.asset"
    output_asset_variable_name = filename_base + "_points"
    output_asset_position_name = output_asset_variable_name + "_position"
    with open(output_asset_filename, "w") as output_file:

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
            # This is pretty hacky - adding in the _points suffix...
            for fade_target in fade_targets:
                print(f"        openspace.setPropertyValueSingle(\"Scene.{fade_target + "_points"}.Renderable.Fade\", 0.0, 1.0)", file=output_file)
            print("      elseif args.Transition == \"Exiting\" then", file=output_file)
            for fade_target in fade_targets:
                print(f"        openspace.setPropertyValueSingle(\"Scene.{fade_target + "_points"}.Renderable.Fade\", 1.0, 1.0)", file=output_file)
            print("      end", file=output_file)
            print("    ]],", file=output_file)
            print("    IsLocal = true", file=output_file)
            print("}", file=output_file)

        print("local meters_in_pc = 3.0856775814913673e+16", file=output_file)
        print(f"local {output_asset_position_name} = {{", file=output_file)
        print(f"    Identifier = \"{output_asset_position_name}\",", file=output_file)
        print("  Transform = {", file=output_file)
        print("    Translation = {", file=output_file)
        print("      Type = \"StaticTranslation\",", file=output_file)
        print("      Position = {", file=output_file)
        print(f"        {input_points_world_position["x"]} * meters_in_pc,", file=output_file)
        print(f"        {input_points_world_position["y"]} * meters_in_pc,", file=output_file)
        print(f"        {input_points_world_position["z"]} * meters_in_pc,", file=output_file)
        print("      }", file=output_file)
        print("     }", file=output_file)
        print("    },", file=output_file)
        print("  GUI = {", file=output_file)
        print(f"    Name = \"{output_asset_position_name}\",", file=output_file)
        print(f"    Path = \"/Points\",", file=output_file)
        print(f"    Hidden = true", file=output_file)
        print("  }", file=output_file)
        print(" }", file=output_file)

        print(f"local {output_asset_variable_name} = {{", file=output_file)
        print(f"    Identifier = \"{output_asset_variable_name}\",", file=output_file)
        print(f"    Parent = {output_asset_position_name}.Identifier,", file=output_file)
        print("    Renderable = {", file=output_file)
        print("        Type = \"RenderablePointCloud\",", file=output_file)
        print(f"        File = asset.resource(\"{local_points_csv_filename}\"),", file=output_file)
        print(f"         Texture = {{ File = asset.resource(\"{default_texture}\") }},", file=output_file)
        print("         Unit = \"pc\",", file=output_file)
        #print(f"        Coloring = {{ FixedColor = {{ 1.0, 0.0, 0.0 }} }},", file=output_file)
        print(f"        Coloring = {{ ColorMapping = {{ File = asset.resource(\"{color_local_filename}\"),", file=output_file)
        print(f"                                      Parameter = \"color\" }} }},", file=output_file)
        print("    },", file=output_file)
        print("    InteractionSphere = 1 * meters_in_pc,", file=output_file)
        print("    ApproachFactor = 1000.0,", file=output_file)
        print("    ReachFactor = 5.0,", file=output_file)
        if fade_targets:
            print(f"    OnApproach = {{ \"{fade_varname}\" }},", file=output_file)
            print(f"    OnReach = {{ \"{fade_varname}\" }},", file=output_file)
            print(f"    OnRecede = {{ \"{fade_varname}\" }},", file=output_file)
            print(f"    OnExit = {{ \"{fade_varname}\" }},", file=output_file)
        print("    GUI = {", file=output_file)
        print(f"        Name = \"{output_asset_variable_name}\",", file=output_file)
        print(f"        Path = \"/Points\"", file=output_file)
        print("    }", file=output_file)
        print("}", file=output_file)
        print("asset.onInitialize(function()", file=output_file)
        if fade_targets:
            print(f"  openspace.action.registerAction({fade_varname})", file=output_file)
        print(f"    openspace.addSceneGraphNode({output_asset_position_name});", file=output_file)
        print(f"    openspace.addSceneGraphNode({output_asset_variable_name});", file=output_file)
        print("end)", file=output_file)
        print("asset.onDeinitialize(function()", file=output_file)
        print(f"    openspace.removeSceneGraphNode({output_asset_variable_name});", file=output_file)
        print(f"    openspace.removeSceneGraphNode({output_asset_position_name});", file=output_file)
        if fade_targets:
            print(f"  openspace.action.removeAction({fade_varname})", file=output_file)
        print("end)", file=output_file)
        print(f"asset.export({output_asset_position_name})", file=output_file)
        print(f"asset.export({output_asset_variable_name})", file=output_file)


    output_files.append(output_asset_filename)

    return(output_files)

def make_labels_from_dataframe(input_points_df, 
                               input_points_world_position,
                               filename_base,
                               label_column, label_size, label_minsize, label_maxsize, enabled):
    output_files = []

    label_filename = args.output_dir + "/" + filename_base + "_" + label_column + ".label"
    local_label_filename = os.path.basename(label_filename)
    with open(label_filename, "w") as output_file:
        for index, row in input_points_df.iterrows():
            print(f"{row['x']} {row['y']} {row['z']} id {index} text {row[label_column]}", file=output_file)

    output_files.append(label_filename)

    # Next the asset file for the label file. Same name as the label file, but with .asset
    # extension.
    output_asset_filename = args.output_dir + "/" + filename_base + "_" + label_column + ".asset"
    output_asset_variable_name = filename_base + "_" + label_column + "_labels"
    output_asset_position_name = output_asset_variable_name + "_position"
    with open(output_asset_filename, "w") as output_file:
        print("local meters_in_pc = 3.0856775814913673e+16", file=output_file)
        print(f"local {output_asset_position_name} = {{", file=output_file)
        print(f"    Identifier = \"{output_asset_position_name}\",", file=output_file)
        print("  Transform = {", file=output_file)
        print("    Translation = {", file=output_file)
        print("      Type = \"StaticTranslation\",", file=output_file)
        print("      Position = {", file=output_file)
        print(f"        {input_points_world_position["x"]} * meters_in_pc,", file=output_file)
        print(f"        {input_points_world_position["y"]} * meters_in_pc,", file=output_file)
        print(f"        {input_points_world_position["z"]} * meters_in_pc,", file=output_file)
        print("      }", file=output_file)
        print("     }", file=output_file)
        print("    },", file=output_file)
        print("  GUI = {", file=output_file)
        print(f"    Name = \"{output_asset_position_name}\",", file=output_file)
        print(f"    Path = \"/Positions\",", file=output_file)
        print(f"    Hidden = true", file=output_file)
        print("  }", file=output_file)
        print(" }", file=output_file)

        print(f"local {output_asset_variable_name} = {{", file=output_file)
        print(f"    Identifier = \"{output_asset_variable_name}\",", file=output_file)
        print(f"    Parent = {output_asset_position_name}.Identifier,", file=output_file)
        print("    Renderable = {", file=output_file)
        print("        Type = \"RenderablePointCloud\",", file=output_file)
        print("        Labels = {", file=output_file)
        print(f"            File = asset.resource(\"{local_label_filename}\"),", file=output_file)
        print(f"            Enabled = {enabled},", file=output_file)
        print("            Unit = \"pc\",", file=output_file)
        print(f"            Size = {label_size},", file=output_file)
        print(f"            MinMaxSize = {{ {label_minsize},{label_maxsize} }}", file=output_file)
        print("        }", file=output_file)
        print("    },", file=output_file)
        print("    GUI = {", file=output_file)
        print(f"        Name = \"{output_asset_variable_name}\",", file=output_file)
        print(f"        Path = \"/Labels\"", file=output_file)
        print("    }", file=output_file)
        print("}", file=output_file)
        print("asset.onInitialize(function()", file=output_file)
        print(f"    openspace.addSceneGraphNode({output_asset_position_name});", file=output_file)
        print(f"    openspace.addSceneGraphNode({output_asset_variable_name});", file=output_file)
        print("end)", file=output_file)
        print("asset.onDeinitialize(function()", file=output_file)
        print(f"    openspace.removeSceneGraphNode({output_asset_variable_name});", file=output_file)
        print(f"    openspace.removeSceneGraphNode({output_asset_position_name});", file=output_file)
        print("end)", file=output_file)
        print(f"asset.export({output_asset_position_name})", file=output_file)
        print(f"asset.export({output_asset_variable_name})", file=output_file)


    output_files.append(output_asset_filename)

    return(output_files)

def make_group_labels_from_dataframe(input_points_df,
                                     input_points_world_position,
                                     filename_base,
                                     label_column, 
                                     label_size, 
                                     label_minsize, 
                                     label_maxsize, 
                                     enabled):

    # First we want to figure out the unique values in the label column. These
    # are the groups we want to create labels for.
    groups = input_points_df[label_column].unique()

    # Now we want to make a new empty dataframe with the same columns as the
    # input_points_df. This new dataframe will contain the centroids of the
    # groups.
    centroids_df = pd.DataFrame(columns=input_points_df.columns)
    for group in groups:
        # Get the rows that belong to this group.
        group_rows = input_points_df[input_points_df[label_column] == group]
        # Calculate the centroid of the group.
        centroid = {}
        centroid["x"] = group_rows["x"].mean()
        centroid["y"] = group_rows["y"].mean()
        centroid["z"] = group_rows["z"].mean()
        # Add the group name to the centroid.
        centroid[label_column] = group

        # If x is non nan, add the centroid to the new dataframe.
        if not math.isnan(centroid["x"]):
            centroids_df.loc[len(centroids_df)] = centroid

    # Now we have a dataframe with the centroids of the groups. We can use this
    # to create the labels using the make_labels_from_dataframe function.
    output_files = make_labels_from_dataframe(input_points_df=centroids_df,
                                              input_points_world_position=input_points_world_position,
                                              filename_base=filename_base + "_group",
                                              label_column=label_column,
                                              label_size=label_size,
                                              label_minsize=label_minsize,
                                              label_maxsize=label_maxsize,
                                              enabled=enabled)

    return(output_files)

def main():
    # If an output directory was specified, make sure it exists.
    if args.output_dir != ".":
        Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    # Read the dataset CSV file into a pandas dataframe.
    try:
        input_dataset_df = pd.read_csv(args.input_dataset_csv_file, 
                                    comment="#")
    except FileNotFoundError:
        print("Error: Could not open dataset CSV file: " + args.input_dataset_csv_file)
        sys.exit(1)

    # A list of all the files created for this dataset. Each function below
    # returns the files it creates, so we can use this list to clean up the
    # cache directory.
    files_created = []

    # Now run the functions to create the speck and asset files for each csv
    # file in the dataset csv file.
    for index, row in input_dataset_df.iterrows():
        print("Reading file: " + row["csv_file"] + "... ", end="", flush=True)

        input_points_df = pd.read_csv(row["csv_file"])
        # The first column might be unnamed. It's basically the ID, so we'll
        # call it that for now.
        input_points_df.rename(columns={input_points_df.columns[0]: "ID"},
                                inplace=True)
        
        # The fade_targets argument is optional. If it's blank, it's a NaN, which
        # is weird to test for if it might be a string. So convert it.
        fade_targets = None
        if (str(row["fade_targets"]) != "nan"):
            # There may be more than one fade target, separated by commas.
            fade_targets = row["fade_targets"].split(",")

        # Let's get the base of the filename (no extension) to use for generating
        # output files. Also, replace all the periods with underscores, as periods
        # are not allowed in asset names.
        filename_base = row["csv_file"].replace(".csv", "")
        filename_base = filename_base.replace(".", "_")

        # All points are originally in world coordinates. A problem with this is we
        # need to be able to point the camera to certain locations, such as the center
        # of a set of points. To do this, we need to translate the points so that the
        # centroid of the points is locally at 0,0,0, and then move that whole set of
        # points to its original location using a transform.
        input_points_world_position = {}
        input_points_world_position["x"] = input_points_df["x"].mean()
        input_points_world_position["y"] = input_points_df["y"].mean()
        input_points_world_position["z"] = input_points_df["z"].mean()
        #print("Centroid (world position of center of points): ", input_points_world_position)

        # Translate all the points so that the new centroid of the points is 0,0,0.
        input_points_df["x"] = input_points_df["x"] - input_points_world_position["x"]
        input_points_df["y"] = input_points_df["y"] - input_points_world_position["y"]
        input_points_df["z"] = input_points_df["z"] - input_points_world_position["z"]

        if row["type"] == "labels":
            print("Creating labels... ", end="", flush=True)
            # Let's do the labels first. The following functions modify the original
            # dataframe, adding lots of columns for the speck file, but making labels
            # doesn't. So we can do this first.
            # "enabled" is wonky. It is 1 or 0 in the CSV file, we need to change
            # it to true or false.
            if row["enabled"] == 1:
                row["enabled"] = "true"
            else:
                row["enabled"] = "false"
            files_created += \
                make_labels_from_dataframe(input_points_df=input_points_df,
                                           input_points_world_position=input_points_world_position,
                                           filename_base=filename_base,
                                           label_column=row["label_column"],
                                           label_size=row["label_size"],
                                           label_minsize=row["label_minsize"],
                                           label_maxsize=row["label_maxsize"],
                                           enabled=row["enabled"])
            
        elif row["type"] == "points":
            print("Creating points... ", end="", flush=True)
            files_created += \
                make_points_asset_and_csv_from_dataframe(input_points_df=input_points_df, 
                                                         input_points_world_position=input_points_world_position,
                                                         filename_base=filename_base,
                                                         fade_targets=fade_targets,
                                                         color_by_column=row["color_by_column"],
                                                         default_texture=row["default_texture"])
            
        # Datasets contain many points that fall into common groupings, such as phyla,
        # classes, kingdoms, etc. Rather than have many points with the same label, we
        # can create a single label for the group that sits in the middle of all these
        # points. This is useful for large datasets where the labels would otherwise
        # overlap.
        elif row["type"] == "group_labels":
            print("Creating group labels... ", end="", flush=True)
            # Same thing as above, for enabled.
            if row["enabled"] == 1:
                row["enabled"] = "true"
            else:
                row["enabled"] = "false"
            files_created += \
                make_group_labels_from_dataframe(input_points_df=input_points_df,
                                                 input_points_world_position=input_points_world_position,
                                                 filename_base=filename_base,
                                                 label_column=row["label_column"],
                                                 label_size=row["label_size"],
                                                 label_minsize=row["label_minsize"],
                                                 label_maxsize=row["label_maxsize"],
                                                 enabled=row["enabled"])



        elif row["type"] == "stars":
            print("Creating stars... ", end="", flush=True)
            # Now the speck file. This is what RenderableStars will use to draw the
            # points. The speck file doesn't care about the centroid; the translation
            # to "world" space is applied by the renderable.
            files_created += \
                make_stars_speck_from_dataframe(input_points_df=input_points_df, 
                                                filename_base=filename_base,
                                                lum=row["lum"], 
                                                absmag=row["absmag"],
                                                colorb_v=row["colorb_v"],
                                                texnum=row["texnum"])

            # Now an asset file that will be used to load the speck file into OpenSpace.
            files_created += \
                make_stars_asset_from_dataframe(input_points_df=input_points_df, 
                                                input_points_world_position=input_points_world_position,
                                                filename_base=filename_base,
                                                magnitude_exponent=row["MagnitudeExponent"],
                                                core_multiplier=row["core_multiplier"],
                                                core_gamma=row["core_gamma"],
                                                core_scale=row["core_scale"],
                                                glare_multiplier=row["glare_multiplier"],
                                                glare_gamma=row["glare_gamma"],
                                                glare_scale=row["glare_scale"],
                                                fade_targets=fade_targets)
        print("Done.")

    # Now we need to make a list of all the .asset and .speck files we created
    # so these can be flushed from the cache directory.
    print("Cleaning cache directory...", end="", flush=True)
    for file in files_created:
        # Get just the filename, not the path.
        file = os.path.basename(file)
        # Ignore any errors if the file doesn't exist.
        try:
            if args.verbose:
                print(f"Removing {args.cache_dir + '/' + file}")
            shutil.rmtree(args.cache_dir + "/" + file)
        except FileNotFoundError:
            pass
        # Notify all other exceptions.
        except Exception as e:
            print(f"Error removing file {args.cache_dir + '/' + file}: {e}")
    print("Done.")
    
    # Now copy the speck and asset files to the output directory.
    print(f"Copying files to output directory ({args.asset_dir}).")
    Path(args.asset_dir).mkdir(parents=True, exist_ok=True)
    for file in files_created:
        if args.verbose:
            print(f"{file} ", end="", flush=True)
        shutil.copy2(file, args.asset_dir)
    print("Done.")

    # Now copy any texture files to the output directory. Run through the input_points_df
    # and make a list of unique textures, then copy them all from the texture directory
    # to the output dir.
    textures = input_dataset_df["default_texture"].unique()
    for texture in textures:
        if args.verbose:
            print(f"Copying {texture} ", end="", flush=True)
        shutil.copy2(args.texture_dir + "/" + texture, args.asset_dir)

if __name__ == '__main__':
    main()
    