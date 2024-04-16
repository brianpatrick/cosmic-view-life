# Cosmic View of Life on Earth

# Author: Brian Abbott <abbott@amnh.org>
# Created: September 2022
"""
This module returns a series of files with various columns for color mapping to trace on taxon lineage. The idea is to trace one taxon back to the order level (primates, aves, etc). Files are generated for each lineage level with common lineage codes. For example, we can trace Homo lineage back to the primates common ancestor, and have one file for each of those lineage levels.
"""


import sys
import re
from pathlib import Path
import numpy as np
import pandas as pd

from src import common



def process_data(datainfo, taxon):
    """
    For a single taxon or species, gather the common ancestors for each lineage level all the way back to the order's common ancestor.

    :param datainfo: Metadata about the dataset.
    :type datainfo: dict of {str : list}
    :param taxon: Name of the species, or taxon, we want to trace through its lineage.
    :type taxon: str

    Given a species' taxon name, pull DNA samples from the sequences data to trace its lineage. First, collect the data that have the same lineage code (all Homo sapiens, for example), then progress back to the next lineage level and collect all of those with the same lineage code (Homo sapiens' last ancestor plus all the other species that shared that ancestor), etc. until we reach the order, which, in the case of Homo would be Primates.

    A speck file is generated for each lineage level so they may be given a constant color at each level. For example, start with the order level, in our example, this would be order primates. Every DNA sample at that lineage level shares the same common ancestor, so they will all be the same color. As we sample the next lineage level, some species have peeled off, evolving from a different common ancestor than Homo. We traverse the lineage levels until we reach genus Homo, which is the end of the branch, and now will only show those points in one color.
    

    Output files:
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    :file:`[{order}]/[{version}]/[{lineage_branches}]/[{taxon_name}]/[{lineage_code}]_[{lineage_name}].speck`
        The OpenSpace-ready files for the DNA sequence data. There will be one speck file for each lineage level.
    """

    datainfo['data_group_title'] = datainfo['sub_project'] + ': Traced lineage DNA sequence data for taxon ' + taxon
    datainfo['data_group_desc'] = 'DNA sample data for primates. Each point represents one DNA sample and is colored by lineage tracing.'


    # Open the sequences.csv file and put it into a df
    # ---------------------------------------------------------------------------
    infile_speck = 'sequences.csv'
    inpath_speck = Path.cwd() / common.PROCESSED_DATA_DIRECTORY / datainfo['dir'] / datainfo['catalog_directory'] / infile_speck
    common.test_input_file(inpath_speck)

    df = pd.read_csv(inpath_speck, low_memory=False)


    # Get the first line that contains the taxon, and 
    seq_line = {}
    ########### HH             row = df.loc[df[lineage_code_col]==code].iloc[0]

    for _, row in df.iterrows():
        if re.search(taxon, row['speck_name']):
            seq_line = row.to_dict()
            break
    

    # Generate the lineage codes/indicies.
    lineage_code_cols = []
    lineage_name_cols = []
    for code_index in range(datainfo['lineage_columns'][0], datainfo['lineage_columns'][1] + 1):
        lineage_name_cols.append('lineage_' + str(code_index))
        lineage_code_cols.append('lineage_' + str(code_index) + '_code')


    # Pluck out the lineage codes from the row dict seq_line
    lineage_codes = []
    lineage_names = []
    for lin_code_col, lin_name_col in zip(lineage_code_cols, lineage_name_cols):
        lineage_codes.append(int(seq_line[lin_code_col]))
        lineage_names.append(seq_line[lin_name_col])

    
    
    # For each lineage code, scan the df and get those lines containing that lineage code to print to a speck
    for lin_code_col, lin_code, lin_name in zip(lineage_code_cols, lineage_codes, lineage_names):

        # This insures that we do not include lineage columns with a zero code, meaning there
        # is no lineage for that taxon on that level. Noticed this when i chose the Anas (ducks) 
        # and their code is 33084, so there is no 34-level lineage member, and it died.
        if(lin_code == 0):
            break

        # For a particular lineage column, pluck the lines with the lineage code and save in a new df
        lineage_df = df[df[lin_code_col] == lin_code]
        

        # Print the speck file
        # --------------------------------------------------------------------------
        taxon_file_name = taxon.replace(' ', '_').lower()
        lineage_file_name = lin_name.replace(' ', '_').lower()

        subfolder_name = taxon_file_name
        out_file_stem = str(lin_code) + '_' + lineage_file_name
        outpath = Path.cwd() / datainfo['dir'] / datainfo['catalog_directory'] / common.BRANCHES_DIRECTORY / subfolder_name
        common.test_path(outpath)

        outfile_speck = out_file_stem + '.speck'
        outpath_speck = outpath / outfile_speck
        with open(outpath_speck, 'wt') as speck:

            header = common.header(datainfo, script_name=Path(__file__).name)
            print(header, file=speck)


            print('datavar 0 ' + lin_code_col, file=speck)


            # Print the rows to the speck file
            for _, row in lineage_df.iterrows():

                # Print the x,y,z
                print(f"{row['x']:.8f} {row['y']:.8f} {row['z']:.8f} {int(row[lin_code_col])}  # {row['seq_id']} | {lin_name} | {row['taxon']}", file=speck)

        common.out_file_message(outpath_speck)




    ####  This is old code that, based on a tuple of color names, will build a color map file
    #### We abandonded this code because we decided to handle it in the make_asset code, slightly differently.

 
    # # Build and print the color map files.
    # # ---------------------------------------------------------------------------
    # # First, for the continents (codes 1-5: 5 total)
    
    # # Define the color table for this file
    # color_table = ('Peach', 'Fuchsia', 'Orchid', 'Indigo', 'Sky Blue', 'Asparagus', 'Maize', 'Lemon Yellow')

    # # Specify the color table we want to sample from
    # color_table_file = 'crayola.dat'

    # outpath = Path.cwd() / datainfo['dir'] /common.BRANCHES_DIRECTORY
    # common.test_path(outpath)

    # outfile_cmap = out_file_stem + '.cmap'
    # outpath_cmap = outpath / outfile_cmap

    # with open(outpath_cmap, 'wt') as cmap:

    #     header = common.header(datainfo, script_name=Path(__file__).name)
    #     print(header, file=cmap)

    #     # Print the number of colors
    #     print(len(color_table), file=cmap)
        
    #     # Print the rows to the cmap file
    #     for color_name in color_table:

    #         # Get the RGB from the color table file given the color name
    #         rgb = common.find_color(color_table_file, color_name)

    #         # Print to the file
    #         print(f"{rgb} 1.0 # {color_name}", file=cmap)

    # # Report to stdout
    # common.out_file_message(outpath_cmap)

    # return lineage_codes






def make_asset(datainfo, taxon):
    """
    Generate the asset file for the lineage branch speck files.

    :param datainfo: Metadata about the dataset.
    :type datainfo: dict of {str : list}
    :param taxon: The name of the taxon for the lineage trace.
    :type taxon: str

    This asset generator will include a data object for each speck file in the given directory.

    
    Output files:
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    :file:`[{order}]/[{version}]/branch_[{taxon}].asset`
        The OpenSpace-ready asset file for the lineage branch files. For example, :file:`primates/branch_homo_sapiens.asset`.
    """

    # We shift the stdout to our filehandle so that we don't have to keep putting
    # the filehandle in every print statement.
    # Save the original stdout so we can switch back later
    original_stdout = sys.stdout


    # Define the main dict that will hold all the info needed per file
    # This is a nested dict with the format:
    # { file_name: { root:  , filevar:  , os_variable:  , os_identifier:  , name:  } }
    asset_info = {}



    # Gather info about the files
    # Get a listing of the speck files in the path, then set the dict
    # values based on the filename.
    sub_directory = taxon.replace(' ', '_').lower()
    path = Path.cwd() / datainfo['dir'] / datainfo['catalog_directory'] / common.BRANCHES_DIRECTORY / sub_directory
    files = sorted(path.glob('*.speck'))


    for path in files:
        
        file = path.name

        # Set the nested dict
        asset_info[file] = {}

        asset_info[file]['speck_file'] = path.name
        asset_info[file]['speck_var'] = common.file_variable_generator(asset_info[file]['speck_file'])

        # asset_info[file]['label_file'] = path.stem + '.label'
        # asset_info[file]['label_var'] = common.file_variable_generator(asset_info[file]['label_file'])

        # asset_info[file]['cmap_file'] = path.stem + '_taxon.cmap'
        # asset_info[file]['cmap_var'] = common.file_variable_generator(asset_info[file]['cmap_file'])
        
        asset_info[file]['asset_rel_path'] = common.BRANCHES_DIRECTORY + '/' + taxon.replace(' ', '_').lower()

        asset_info[file]['os_scenegraph_var'] = datainfo['dir'] + '_' + datainfo['catalog_directory'] + '_' + path.stem + '_' + taxon.replace(' ', '_').lower()
        asset_info[file]['os_identifier_var'] = datainfo['dir'] + '_' + datainfo['catalog_directory'] + '_' + path.stem + '_' + taxon.replace(' ', '_').lower()

        asset_info[file]['gui_name'] = path.stem.replace('_', ' ').title()
        asset_info[file]['gui_path'] = '/' + datainfo['sub_project'] + '/' + datainfo['catalog_directory'] + '/' + common.BRANCHES_DIRECTORY.replace('_', ' ').title() + '/' + taxon



    # Define a dict for the color table, then set the main input color file
    color_table = {}
    color_table_file = 'crayola.dat'
    input_color_table = ('Peach', 'Fuchsia', 'Orchid', 'Indigo', 'Sky Blue', 'Asparagus', 'Maize', 'Lemon Yellow')

    # Send the main color file and input color table to the color2dict function.
    # This function returns a dict of (color_name: rgb_values), where the RGBs
    # are comma-separated, ready to go into the asset file Color command.
    color_table = common.color2dict(color_table_file, input_color_table)


    # Combine the files list and the color_table dictionaries
    # Expect the color table to be equal or greater in length
    # Check to make sure we have more files than colors, else quit
    if(len(asset_info) <= len(color_table)):

        # Step through the file_info and color_table dictionaries and 
        # set the color info to the file_info dict
        for file, (color_name, rgb) in zip(asset_info, color_table.items()):
            asset_info[file]['color_name'] = color_name
            asset_info[file]['rgb'] = rgb

    else:
        sys.exit(f"{make_asset.__name__}() function inside {Path(__file__).name}:\nNot enough colors for all the files. Add colors to the input_color_table.\nQuitting...")



    # Open the file to write to
    outfile = 'branches_' + taxon.replace(' ', '_').lower() + '.asset'
    outpath = Path.cwd() / datainfo['dir'] / datainfo['catalog_directory'] / outfile
    with open(outpath, 'wt') as out_asset:

        # Switch stdout to the file
        sys.stdout = out_asset


        print('-- ' + datainfo['project'] + ' / ' + datainfo['data_group_title'])
        print("-- This file is auto-generated in the " + make_asset.__name__ + "() function inside " + Path(__file__).name)
        print('-- Author: Brian Abbott <abbott@amnh.org>')
        print()


        print('-- Set file paths')
        for file in asset_info:
            print('local ' + asset_info[file]['speck_var'] + ' = asset.resource("' + asset_info[file]['asset_rel_path'] + '/' + asset_info[file]['speck_file'] + '")')

        print()

        print('-- Set some parameters for OpenSpace settings')
        print('local scale_factor = ' + common.POINT_SCALE_FACTOR)
        print('local scale_exponent = ' + common.POINT_SCALE_EXPONENT)
        print('local text_size = ' + common.TEXT_SIZE)
        print('local text_min_size = ' + common.TEXT_MIN_SIZE)
        print('local text_max_size = ' + common.TEXT_MAX_SIZE)
        print()


        for file in asset_info:

            print('local ' + asset_info[file]['os_scenegraph_var'] + ' = {')
            print('    Identifier = "' + asset_info[file]['os_identifier_var'] + '",')
            print('    Renderable = {')
            print('        UseCaching = false,')
            print('        Type = "RenderablePointCloud",')
            print('        Coloring = { FixedColor = {' + asset_info[file]['rgb'] + ' }, },\t-- ' + asset_info[file]['color_name'])
            print('        Opacity = 1.0,')
            print('        SizeSettings = { ScaleExponent = scale_exponent, ScaleFactor = scale_factor },')
            print('        File = ' + asset_info[file]['speck_var'] + ',')
            print('        DrawLabels = false,')
            print('        Unit = "Km",')
            print('        BillboardMinMaxSize = { 0.0, 25.0 },')
            print('        EnablePixelSizeControl = true,')
            print('        EnableLabelFading = false,')
            print('        Enabled = false')
            print('    },')
            print('    GUI = {')
            print('        Name = "' + asset_info[file]['gui_name'] + '",')
            print('        Path = "' + asset_info[file]['gui_path'] + '",')
            print('    }')
            print('}')
            print()



        print('asset.onInitialize(function()')
        for file in asset_info:
            print('    openspace.addSceneGraphNode(' + asset_info[file]['os_scenegraph_var'] + ')')

        print('end)')
        print()


        print('asset.onDeinitialize(function()')
        for file in asset_info:
            print('    openspace.removeSceneGraphNode(' + asset_info[file]['os_scenegraph_var'] + ')')
        
        print('end)')
        print()


        for file in asset_info:
            print('asset.export(' + asset_info[file]['os_scenegraph_var'] + ')')

        print()

    # Switch the stdout back to normal stdout (screen)
    sys.stdout = original_stdout

    # Report to stdout
    common.out_file_message(outpath)
    print()
