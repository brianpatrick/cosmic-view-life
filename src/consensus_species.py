# Cosmic View of Life on Earth
#
# Author: Brian Abbott <abbott@amnh.org>
# Created: September 2022
'''
Consensus species is an average point that represents an entire species' data, spatially. It should be a point that sits in the middle of the "cloud" of points from the sequence data for that species.

This module consists of a data processing function and an asset file creation file.
'''

import sys
import pandas as pd
from pathlib import Path

from src import common


def process_data(datainfo, vocab):
    """
    Process the consensus species data. 
    
    We fold in the vocabulary (common names), and output various data files. Each record in this step represents one species, so one data point per species. Not all points have common names though.

    :param datainfo: Metadata about the dataset.
    :type datainfo: dict of {str : list}
    :param vocab: A taxon to common name DataFrame.
    :type vocab: DataFrame
    :return: A table of consensus species data.
    :rtype: DataFrame
    

    Reads in the raw data and prints out the processed data to a csv file. Also prints out a log file with some stats on the data.

    Output files:
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    :file:`[{order}]/[{version}]/consensus_species/consensus.csv`
        The OpenSpace-ready data file.

    :file:`logs/[{order}]/[{version}]/consensus_species.py.log`
        A file of stats on these data, and a list of taxons.

    """

    common.print_subhead_status('Processing consensus species')

    datainfo['data_group_title'] = datainfo['sub_project'] + ': Consensus species'
    datainfo['data_group_desc'] = 'Consensus species for the ' + datainfo['sub_project'].lower() + ' data, which includes one data point per species. This point is an average of the DNA information.'
    

    
    # Read and process the raw data file
    # ---------------------------------------------------------------------------
    # Example:
    #           .       /       data            /     primates    /     consensus                 / primates.cleaned.species.MDS.euclidean.csv
    inpath = Path.cwd() / common.DATA_DIRECTORY / datainfo['dir'] / datainfo['catalog_directory'] / datainfo['consensus_file']
    common.test_input_file(inpath)

    # Read in the CSV file
    # 'Taxon' header is not present in the CSV, so remove all the headers, and add them manually
    df = pd.read_csv(inpath, header=0, names=['taxon', 'x', 'y', 'z'])

    #print(df)

    # Rearrange the columns
    df = df[['x', 'y', 'z', 'taxon']]

    # Rescale the position data
    df['x'] = df['x'].multiply(common.POSITION_SCALE_FACTOR)
    df['y'] = df['y'].multiply(common.POSITION_SCALE_FACTOR)
    df['z'] = df['z'].multiply(common.POSITION_SCALE_FACTOR)

    # Coalate this DF with the vocabulary DF
    df = pd.merge(df, vocab, left_on='taxon', right_on='scientific name', how='left').drop(['taxId', 'scientific name'], axis=1)

    # Print the data in a single CSV file.
    # ---------------------------------------------------------------------------
    out_file_stem = 'consensus'
    outpath = Path.cwd() / datainfo['dir'] / datainfo['catalog_directory'] / common.CONSENSUS_DIRECTORY
    common.test_path(outpath)

    outfile_csv = out_file_stem + '.csv'
    outpath_csv = outpath / outfile_csv

    with open(outpath_csv, 'w') as csvfile:

        header = common.header(datainfo, script_name=Path(__file__).name)
        print(header, file=csvfile)
        
        # Print the data to the CSV file. Don't include the index.
        # For some reason, we have to include the lineterminator='\n' to get the newlines to work.
        # Without this, newlines default to '\r\r\n', which is particularly bizarre.
        df.to_csv(csvfile, index=False, lineterminator='\n')

        # Report to stdout
        common.out_file_message(outpath_csv)

    # Print a log file
    # ---------------------------------------------------------------------------
    outfile_log = Path(__file__).name + '.log'
    
    log_path = Path.cwd() / common.LOG_DIRECTORY / datainfo['dir'] / datainfo['catalog_directory']
    common.test_path(log_path)
    outpath_log = log_path / outfile_log

    with open(outpath_log, 'wt') as log:

        print('Generated log from ' + Path(__file__).name + ' run with the ' + datainfo['sub_project'].lower() + ' data set.', file=log)
        print('================================================================================', file=log)

        # Some general stats, number of rows
        print('Number of rows: ' + str(len(df.index)), file=log)
        print('Number of columns: ' + str(len(df.columns)), file=log)
        print(file=log)


        # Print all the column names
        print('Columns:', file=log)
        print(pd.DataFrame({"column": df.columns, "non-nulls": len(df)-df.isnull().sum().values, "nulls": df.isnull().sum().values, "type": df.dtypes.values}), file=log)
        print(file=log)

        # Print the unique values and their count, sorted by the column, not the highest count
        print(df['taxon'].value_counts().sort_index(), file=log)
        print(file=log)


    # Report to stdout
    common.out_file_message(outpath_log)

    return df




def make_asset(datainfo):
    """
    Generate the asset file for the consensus species data.

    :param datainfo: Metadata about the dataset.
    :type datainfo: dict of {str : list}

    Output files:
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    :file:`[{order}]/[{version}]/consensus_species.asset`
        The asset file containing the OpenSpace configurations for the consensus species.
    """

    # We shift the stdout to our filehandle so that we don't have to keep putting
    # the filehandle in every print statement.
    # Save the original stdout so we can switch back later
    original_stdout = sys.stdout



    # Define the main dict that will hold all the info needed per file
    # This is a nested dict with the format:
    #      { path: { root:  , filevar:  , os_variable:  , os_identifier:  , name:  } }
    asset_info = {}

    # Gather info about the files
    # Get a listing of the csv files in the path, then set the dict
    # values based on the filename.
    path = Path.cwd() / datainfo['dir'] / datainfo['catalog_directory'] / common.CONSENSUS_DIRECTORY
    files = sorted(path.glob('*.csv'))


    for path in files:
        
        file = path.name

        # Set the nested dict
        asset_info[file] = {}

        asset_info[file]['csv_file'] = path.name
        asset_info[file]['csv_var'] = common.file_variable_generator(asset_info[file]['csv_file'])

        asset_info[file]['asset_rel_path'] = common.CONSENSUS_DIRECTORY

        asset_info[file]['os_scenegraph_var'] = datainfo['dir'] + '_' + datainfo['catalog_directory'] + '_' + common.CONSENSUS_DIRECTORY
        asset_info[file]['os_identifier_var'] = datainfo['dir'] + '_' + datainfo['catalog_directory'] + '_' + common.CONSENSUS_DIRECTORY

        asset_info[file]['gui_name'] = common.CONSENSUS_DIRECTORY.replace('_', ' ').title()
        asset_info[file]['gui_path'] = '/' + datainfo['sub_project'] + '/' + datainfo['catalog_directory']

    # Open the file to write to
    outfile = common.CONSENSUS_DIRECTORY + '.asset'
    outpath = Path.cwd() / datainfo['dir'] / datainfo['catalog_directory'] / outfile
    with open(outpath, 'wt') as asset:

        # Switch stdout to the file
        sys.stdout = asset

        print('-- ' + datainfo['project'] + ' / ' + datainfo['data_group_title'])
        print("-- This file is auto-generated in the " + make_asset.__name__ + "() function inside " + Path(__file__).name)
        print('-- Author: Brian Abbott <abbott@amnh.org>')
        print()

        for file in asset_info:
            print('local ' + asset_info[file]['csv_var'] + ' = asset.resource("' + asset_info[file]['asset_rel_path'] + '/' + asset_info[file]['csv_file'] + '")')

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
            print('         Coloring = {')
            print('            FixedColor = { 0.8, 0.8, 0.8 }')
            print('        },')
            print('        Opacity = 1.0,')
            print('        SizeSettings = { ScaleFactor = scale_factor, ScaleExponent = scale_exponent },')
            print('        File = ' + asset_info[file]['csv_var'] + ',')
            print('        DataMapping = { Name="taxon"},')
            print('        Labels = { Enabled = false, Size = text_size  },')
            print('        --FadeLabelDistances = { 0.0, 0.5 },')
            print('        --FadeLabelWidths = { 0.001, 0.5 },')
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

    # Switch the stdout back to normal stdout (screen)
    sys.stdout = original_stdout

 
    # Report to stdout
    common.out_file_message(outpath)
    print()
