'''
Cosmic View of Life on Earth

This script returns a file with various columns for color mapping to trace on taxon lineage.
The idea is to trace one clade back to the Class level (primates, aves, etc).
So, one speck file with all the sequence data in it, but we add columns
so that we can add one color mapping per lineage level. The rest will be "grayed out".

Author: Brian Abbott <abbott@amnh.org>
Created: September 2022
'''

import sys
import re
from pathlib import Path
import numpy as np
import pandas as pd

from src import common



def process_data(datainfo, taxon):
    '''
    Pull DNA samples from the main speck file given an input taxon.
    This input argument, taxon, is the species name we want to consider. 
    We then pull the lineage codes from that taxon line, and begin mapping 
    a new color amp file based on each lineage level. In the first level,
    10% might carry the color code (which is just the lineage code) 
    and the rest will be set to zero. On the next lineage level, more will 
    carry their code so they will be mapped to a color, and the rest gray, etc.
    for each lineage level back to Class.

    Input:
        dict(datainfo)
        str(clade)                  A lineage name or code number
        sequence.speck

    Output:
        branches/[taxon].speck      For example, "branches/homo_sapians.speck"

    '''

    datainfo['data_group_title'] = datainfo['sub_project'] + ': Traced lineage DNA sequence data for taxon ' + taxon
    datainfo['data_group_desc'] = 'DNA sample data for primates. Each point represents one DNA sample and is colored by lineage tracing.'


    # Open the sequences.csv file and put it into a df
    # ---------------------------------------------------------------------------
    infile_speck = 'sequences.csv'
    inpath_speck = Path.cwd() / common.PROCESSED_DATA_DIRECTORY / datainfo['dir'] / datainfo['catalog_directory'] / infile_speck
    common.test_input_file(inpath_speck)

    df = pd.read_csv(inpath_speck)


    # Get the first line that contains the taxon, and 
    seq_line = {}
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
        lineage_codes.append(seq_line[lin_code_col])
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
                print(f"{row['x']:.8f} {row['y']:.8f} {row['z']:.8f} {row[lin_code_col]}  # {row['seq_id']} | {lin_name} | {row['taxon']}", file=speck)

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
    '''
    Generate the asset file for the species lineage branch files.

    Input:
        dict(datainfo)
        str(directory)             The folder where the taxon branch files exist. This is a subfolder under 'branches'
        A list of .speck files in the 'branches' directory
        A color table file
        An input color table
    
    Output:
        [directory]/[taxon].asset   The asset file will live inside the "branches"/[directory] folder
    '''

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
            print('local ' + asset_info[file]['speck_var'] + ' = asset.localResource("' + asset_info[file]['asset_rel_path'] + '/' + asset_info[file]['speck_file'] + '")')

        print()
        print('local texture_file = asset.localResource("point3A.png")')
        print()


        print('-- Set some parameters for OpenSpace settings')
        print('local scale_factor = ' + common.SCALE_FACTOR)
        print('local text_size = ' + common.TEXT_SIZE)
        print('local text_min_size = ' + common.TEXT_MIN_SIZE)
        print('local text_max_size = ' + common.TEXT_MAX_SIZE)
        print()


        for file in asset_info:

            print('local ' + asset_info[file]['os_scenegraph_var'] + ' = {')
            print('    Identifier = "' + asset_info[file]['os_identifier_var'] + '",')
            print('    Renderable = {')
            print('        Type = "RenderableCosmicPoints",')
            print('        Color = { ' + asset_info[file]['rgb'] + ' },\t-- ' + asset_info[file]['color_name'])
            print('        Opacity = 1.0,')
            print('        ScaleFactor = scale_factor,')
            print('        File = ' + asset_info[file]['speck_var'] + ',')
            print('        DrawLabels = false,')
            print('        Unit = "Km",')
            print('        Texture = texture_file,')
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
