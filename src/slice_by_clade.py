# Cosmic View of Life on Earth

# Author: Brian Abbott <abbott@amnh.org>
# Created: September 2022
"""
This module returns subsets of the DNA samples based on a given clade. The clade can be a name or a lineage code number. Clade is merely a group with a common ancestor at any node on the tree, so these names or codes fed to this function must be one of the lineage names or codes found in the :file:`lineage.dat` or :file:`lineage_codes.csv`.
"""

import sys
from pathlib import Path

from src import common



def process_data(datainfo, clade):
    """
    Given an input clade, pull DNA samples from the main :file:`sequences.speck` file.

    :param datainfo: Metadata about the dataset.
    :type datainfo: dict of {str : list}
    :param clade: The lineage name or code.
    :type clade: str

    The input argument, ``clade``, can either be the lineage code number (eg, 31009 for 'Homo'), or it can be the proper name (eg, 'Homo'). It can be any name or number from the lineage codes table. The resulting files have names combining the lineage information, e.g. For example, ``31009_homo.speck``.

    Output files:
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    :file:`[{order}]/[{version}]/clades/[{lineage_code}]_[{lineage_name}].speck`
        The OpenSpace-ready file for the DNA sequence data.
    """

    # Open the lineage_codes.csv and look up the code number for the clade, 
    # return the lineage key tuple of tuples.
    lineage_key = common.parse_lineage_csv(datainfo)

    # Step through each row of the lineage key csv to pull out the
    # lineage code (if lineage name is given), or the lineage name (if the lineage code is given)
    # Cycle through the lineage_key tuple of tuples
    for lineage_row in lineage_key:
        
        # If the clade is in the row, grab its corresponding lineage information.
        if clade in lineage_row:

            # If the input clade is all letters, get the code from the matching tuple
            if clade.isalpha():
                lineage_code = lineage_row[0]
                lineage_name = clade

            # If the input clade is a number (code), then get the corresponding name
            else:
                lineage_code = clade
                lineage_name = lineage_row[1]
            

    
    # Define some metadata
    datainfo['data_group_title'] = datainfo['sub_project'] + ': ' + lineage_name + ' DNA sequence data (code ' + lineage_code + ')'
    datainfo['data_group_desc'] = 'DNA sample data for ' + lineage_name + '. Each point represents one DNA sample.'


    # Open the *.speck and pull the lines with the lineage code.
    # Rather than pass the sequence dataframe into the function, we simply
    # read the speck file resulting from sequence_data.py
    # Parse the speck file and return the header, datavar, and data lines as strings
    # ---------------------------------------------------------------------------
    infile_speck = 'sequences.speck'
    inpath_speck = Path.cwd() / datainfo['dir'] / datainfo['catalog_directory'] / common.SEQUENCE_DIRECTORY / infile_speck
    common.test_input_file(inpath_speck)

    # Parse the speck file and return the header, datavar, and data lines as strings
    (_, datavar_lines, data_lines) = common.parse_speck(inpath_speck, lineage_code)



    # Print the data
    # ---------------------------------------------------------------------------
    outpath = Path.cwd() / datainfo['dir'] / datainfo['catalog_directory'] / common.CLADE_DIRECTORY
    common.test_path(outpath)

    outfile = str(lineage_code) + '_' + lineage_name.lower() + '.speck'
    outpath = outpath / outfile

    with open(outpath, 'wt') as speck:

        header = common.header(datainfo, process_data.__name__, Path(__file__).name)
        print(header, file=speck)

        # print the datavar lines
        print(datavar_lines, file=speck)

        # Print the data lines
        print(data_lines, file=speck)


    # Report to stdout
    common.out_file_message(outpath)






def make_asset(datainfo):
    """
    Generate the asset file for the clade speck files.

    :param datainfo: Metadata about the dataset.
    :type datainfo: dict of {str : list}

    This asset generator gets a listing of the clade speck files, then creates a data object for each file, while sampling from the main color table to assign colors to each object.

    
    Output files:
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    :file:`[{order}]/[{version}]/clades.asset`
        The OpenSpace-ready asset file for the clade subsets of DNA sequence data.
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
    path = Path.cwd() / datainfo['dir'] / datainfo['catalog_directory'] / common.CLADE_DIRECTORY
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
        
        asset_info[file]['asset_rel_path'] = common.CLADE_DIRECTORY

        asset_info[file]['os_scenegraph_var'] = datainfo['dir'] + '_' + datainfo['catalog_directory'] + '_' + common.CLADE_DIRECTORY + '_' + path.stem
        asset_info[file]['os_identifier_var'] = datainfo['dir'] + '_' + datainfo['catalog_directory'] + '_' + common.CLADE_DIRECTORY + '_' + path.stem

        asset_info[file]['gui_name'] = path.stem.replace('_', ' ').title()
        asset_info[file]['gui_path'] = '/' + datainfo['sub_project'] + '/' + datainfo['catalog_directory'] + '/' + common.CLADE_DIRECTORY.title()
        



    # Define a dict for the color table, then set the main input color file
    color_table = {}
    color_table_file = 'crayola.dat'
    input_color_table = common.CHOSEN_COLOR_TABLE

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
    outfile = common.CLADE_DIRECTORY + '.asset'
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
        print('local texture_file = asset.resource("point3A.png")')
        print('local earthAsset = asset.require("scene/solarsystem/planets/earth/earth")')
        print()


        print('-- Set some parameters for OpenSpace settings')
        print('local scale_factor = '   + common.SCALE_FACTOR)
        print('local scale_exponent = ' + common.SCALE_EXPONENT)
        print('local text_size = '      + common.TEXT_SIZE)
        print('local text_min_size = '  + common.TEXT_MIN_SIZE)
        print('local text_max_size = '  + common.TEXT_MAX_SIZE)
        print()


        for file in asset_info:

            print('local ' + asset_info[file]['os_scenegraph_var'] + ' = {')
            print('    Identifier = "' + asset_info[file]['os_identifier_var'] + '",')
            print('    Renderable = {')
            print('        Type = "RenderablePointCloud",')
            print('        Coloring = { FixedColor = {' + asset_info[file]['rgb'] + ' }, },\t-- ' + asset_info[file]['color_name'])
            print('        Opacity = 1.0,')
            print('        SizeSettings = { ScaleExponent = scale_exponent, ScaleFactor = scale_factor },')
            print('        File = ' + asset_info[file]['speck_var'] + ',')
            print('        DrawLabels = false,')
            print('        Unit = "Km",')
            print('        Texture = { File = texture_file },')
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
