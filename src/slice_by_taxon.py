# Cosmic View of Life on Earth

# Author: Brian Abbott <abbott@amnh.org>
# Created: September 2022
"""
This script returns subsets of the DNA samples from a specific taxon. Taxons can be found in the :file:`taxon_codes.csv` processed catalog file, or at the end of each :file:`sequence.speck` line.
"""

import sys
from pathlib import Path

from src import common


def process_data(datainfo, species_taxon):
    """
    This function pulls out the DNA data for a particular species taxon.

    :param datainfo: Metadata about the dataset.
    :type datainfo: dict of {str : list}
    :param species_taxon: Name of the species, or taxon, we want to isolate.
    :type species_taxon: str

    Read the main speck file for the DNA sequence data and pull out all the samples with matching taxon names. This isolates specific taxons for display.

    Output files:
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    :file:`[{order}]/[{version}]/taxon/[{taxon_name}].speck`
        The OpenSpace-ready files for the DNA sequence data. This module outputs one file, but may be run several times to generate multiple files for multiple taxons.
    """

    # Define some metadata
    datainfo['data_group_title'] = datainfo['sub_project'] + ': ' + species_taxon + ' DNA sequence data'
    datainfo['data_group_desc'] = 'DNA sample data for ' + species_taxon + '. Each point represents one DNA sample.'


    # Rather than pass the sequence dataframe into the function, we simply
    # read the speck file resulting from sequence.py
    # Read and process the raw data file
    # ---------------------------------------------------------------------------
    infile = 'sequences.speck'
    inpath = Path.cwd() / datainfo['dir'] / datainfo['catalog_directory'] / common.SEQUENCE_DIRECTORY / infile
    common.test_input_file(inpath)

    # Parse the speck file and return the header, datavar, and data lines as strings
    (_, datavar_lines, data_lines) = common.parse_speck(inpath, species_taxon)




    # Print the data
    # ---------------------------------------------------------------------------
    outpath = Path.cwd() / datainfo['dir'] / datainfo['catalog_directory'] / common.TAXON_DIRECTORY
    common.test_path(outpath)

    outfile = species_taxon.lower().replace(' ', '_') + '.speck'
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
    Generate the asset file for the species (taxon) files.

    :param datainfo: Metadata about the dataset.
    :type datainfo: dict of {str : list}

    Each time this is run, it will gather all the speck files in the ``taxon`` directory, and create a data object for each of them in this asset file.

    Output files:
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    :file:`[{order}]/[{version}]/taxon.asset`
        The OpenSpace-ready asset file for the taxon-specific files.
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
    path = Path.cwd() / datainfo['dir'] / datainfo['catalog_directory'] / common.TAXON_DIRECTORY
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
        
        asset_info[file]['asset_rel_path'] = common.TAXON_DIRECTORY

        asset_info[file]['os_scenegraph_var'] = datainfo['dir'] + '_' + datainfo['catalog_directory'] + '_' + path.stem
        asset_info[file]['os_identifier_var'] = datainfo['dir'] + '_' + datainfo['catalog_directory'] + '_' + path.stem

        asset_info[file]['gui_name'] = path.stem.replace('_', ' ').title()
        asset_info[file]['gui_path'] = '/' + datainfo['sub_project'] + '/' + datainfo['catalog_directory'] + '/' + common.TAXON_DIRECTORY.replace('_', ' ').title()

    

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
    outfile = common.TAXON_DIRECTORY + '.asset'
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
