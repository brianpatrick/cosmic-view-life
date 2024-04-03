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
    

    Reads in the raw data and prints out the processed data to a speck and label file.
    Note, we include a "dummy" column of zeros because OpenSpace needs four columns in a speck file.

    Output files:
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    :file:`[{order}]/[{version}]/consensus_species/consensus.speck`
        The OpenSpace-ready data file.

    :file:`[{order}]/[{version}]/consensus_species/consensus.label`
        The openSpace-readhy label file.

    :file:`logs/[{order}]/[{version}]/consensus_species.py.log`
        A file of stats on these data, and a list of taxons.

    """

    common.print_subhead_status('Processing consensus species')

    datainfo['data_group_title'] = datainfo['sub_project'] + ': Consensus species'
    datainfo['data_group_desc'] = 'Consensus species for the ' + datainfo['sub_project'].lower() + ' data, which includes one data point per species. This point is an average of the DNA information.'
    

    
    # Read and process the raw data file
    # ---------------------------------------------------------------------------
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

    # Add a dummy column for OpenSpace (which needs 4 data columns -- silly!)
    df['dummy'] = '0'


    # Coalate this DF with the vocabulary DF
    df = pd.merge(df, vocab, left_on='taxon', right_on='scientific name', how='left').drop(['taxId', 'scientific name'], axis=1)
    

    # Construct the .speck and .label columns
    # The speck name is ideally the taxon plyus common name, but if there is no common name, we just use the taxon
    df.loc[df['common name'].notnull(), 'speck_name'] = df['taxon'] + ' | ' + df['common name']
    df.loc[df['common name'].isnull(), 'speck_name'] = df['taxon']

    # The label is only the common name, so if there is no common name, then there is no label
    df.loc[df['common name'].notnull(), 'label_name'] = df['common name']
    df.loc[df['common name'].isnull(), 'label_name'] = None



    # Print the data in a speck and label file
    # ---------------------------------------------------------------------------
    out_file_stem = 'consensus'
    outpath = Path.cwd() / datainfo['dir'] / datainfo['catalog_directory'] / common.CONSENSUS_DIRECTORY
    #outpath = Path.cwd() / datainfo['dir'] / datainfo['catalog_directory'] / common.CONSENSUS_DIRECTORY / common.MORPH_DIRECTORY
    common.test_path(outpath)

    outfile_speck = out_file_stem + '.speck'
    outpath_speck = outpath / outfile_speck

    with open(outpath_speck, 'wt') as speck:

        header = common.header(datainfo, script_name=Path(__file__).name)
        print(header, file=speck)
        
        # Set the columns to print as datavar columns. This is a list of columns to print after x,y,z
        cols_to_print = ['dummy']

        # set a counter for the datavar number (dv), and cycle through the
        # columns to print list and print the datavar lines
        dv = 0
        for col in cols_to_print:
            print('datavar ' + str(dv) + ' ' + col, file=speck)
            dv += 1

        
        # Print the rows to the speck file
        for _, row in df.iterrows():

            # Print the x,y,z
            print(f"{row['x']:.8f} {row['y']:.8f} {row['z']:.8f}", file=speck, end ='')

            # Print the data for the columns in the selected columns in cols_to_print
            for column in cols_to_print:
                print(f" {row[column]}", file=speck, end ='')
            
            # Print the speck label commented at the end of the line
            print(f" # {row['speck_name']}", file=speck)

        # Report to stdout
        common.out_file_message(outpath_speck)



    # Print the labels
    # ---------------------------------------------------------------------------
    outfile_label = out_file_stem + '.label'
    outpath = Path.cwd() / datainfo['dir'] / datainfo['catalog_directory'] / common.CONSENSUS_DIRECTORY
    outpath_label = outpath / outfile_label

    with open(outpath_label, 'wt') as label:

        header = common.header(datainfo, script_name=Path(__file__).name)
        print(header, file=label)

        # Print the label file
        print('textcolor 1', file=label)

        # Loop thru the df and print the label row if a label exists
        ############ HH             row = df.loc[df[lineage_code_col]==code].iloc[0]

        for _, row in df.iterrows():
            if row['label_name'] is not None:
                print(f"{row['x']:.8f} {row['y']:.8f} {row['z']:.8f} text {row['label_name']}", file=label)

        # Report to stdout
        common.out_file_message(outpath_label)




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






    # datainfo['data_group_title'] = datainfo['sub_project'] + ': Consensus Tree'
    # datainfo['data_group_desc'] = 'Data points for the primate consensus tree.'


    # # First, convert the csv raw files into speck files.
    # # These are the internal branch points
    # inpath = Path.cwd() / common.DATA_DIRECTORY / datainfo['dir'] / 'tree' / 'primates.internal.csv'
    # common.test_input_file(inpath)

    # internal_branches = pd.read_csv(inpath)

    # # Rearrange the columns
    # internal_branches = internal_branches[['x', 'y', 'z', 'name']]

    # # Move the z values down, to transform the data down from the origin
    # internal_branches.loc[:, 'z'] = internal_branches['z'].apply(lambda x: x - common.TRANSFORM_TREE_Z)
    # #print(internal_branches)



    # # These are the "leaves"--the current day species.
    # inpath = Path.cwd() / common.DATA_DIRECTORY / datainfo['dir'] / 'tree' / 'primates.leaves.csv'
    # common.test_input_file(inpath)

    # leaves = pd.read_csv(inpath)

    # # Rearrange the columns
    # leaves = leaves[['x', 'y', 'z', 'name']]

    # # Move the z values down, to transform the data down from the origin
    # leaves.loc[:, 'z'] = leaves['z'].apply(lambda x: x - common.TRANSFORM_TREE_Z)

    # # Add underscores to the taxon names
    # leaves['name'] = leaves['name'].str.replace(' ', '_')

    # # Move the z values down
    # leaves.loc[:, 'z'] = leaves['z'].apply(lambda x: x - common.TRANSFORM_TREE_Z)
    # #print(leaves)


    # # Write data to files
    # outpath = Path.cwd() / datainfo['dir'] / datainfo['catalog_directory'] / common.CONSENSUS_DIRECTORY / common.MORPH_DIRECTORY
    # common.test_path(outpath)

    # outfile_speck = 'consensus_tree.speck'
    # outpath_speck = outpath / outfile_speck
    

    # with open(outpath_speck, 'wt') as speck:

    #     datainfo['author'] = 'Brian Abbott (American Museum of Natural History, New York), Wandrille Duchemin (University of Basel & SIB Swiss Institute of Bioinformatics), Robin Ridell (Univ Linköping), Märta Nilsson (Univ Linköping)'

    #     header = common.header(datainfo, script_name=Path(__file__).name)
    #     print(header, file=speck)

    #     for _, row in leaves.iterrows():
    #         print(f"{row['x']:.8f} {row['y']:.8f} {row['z']:.8f} # {row['name']}", file=speck)


    # # Report to stdout
    # common.out_file_message(outpath_speck)


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
    # Get a listing of the speck files in the path, then set the dict
    # values based on the filename.
    path = Path.cwd() / datainfo['dir'] / datainfo['catalog_directory'] / common.CONSENSUS_DIRECTORY
    files = sorted(path.glob('*.speck'))


    for path in files:
        
        file = path.name

        # Set the nested dict
        asset_info[file] = {}

        asset_info[file]['speck_file'] = path.name
        #print(asset_info[file]['speck_file'], path, path.name)
        asset_info[file]['speck_var'] = common.file_variable_generator(asset_info[file]['speck_file'])

        asset_info[file]['label_file'] = path.stem + '.label'
        asset_info[file]['label_var'] = common.file_variable_generator(asset_info[file]['label_file'])

        #asset_info[file]['cmap_file'] = path.stem + '.cmap'
        #asset_info[file]['cmap_var'] = common.file_variable_generator(asset_info[file]['cmap_file'])

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

        #print('local ' + asset_info[file]['filevar'] + ' = asset.resource("' + asset_info[file]['rel_path'] + '/' + asset_info[file]['speck_file'] + '")')

        for file in asset_info:
            print('local ' + asset_info[file]['speck_var'] + ' = asset.resource("' + asset_info[file]['asset_rel_path'] + '/' + asset_info[file]['speck_file'] + '")')

            print('local ' + asset_info[file]['label_var'] + ' = asset.resource("' + asset_info[file]['asset_rel_path'] + '/' + asset_info[file]['label_file'] + '")')



        
        #     print('local label_file = asset.resource("' + asset_info[file]['label_file'] + '")')
        #     #print('local color_file = asset.resource("' + asset_info[file]['cmap_file'] + '")')

        print('local texture_file = asset.resource("point3A.png")')
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
            print('         Coloring = {')
            print('            FixedColor = { 0.8, 0.8, 0.8 }')
            print('        },')
            #print('        ColorMap = ' + asset_info[file]['cmap_var'] + ',')
            #print('        ColorOption = { "lineage_30_code", "taxon_code" },')
            #print('        ColorRange = { {30001, 30025}, {1, 322} },')
            print('        Opacity = 1.0,')
            print('        SizeSettings = { ScaleFactor = scale_factor, ScaleExponent = scale_exponent },')
            print('        File = ' + asset_info[file]['speck_var'] + ',')
            print('        DrawLabels = false,')
            print('        LabelFile = ' + asset_info[file]['label_var'] + ',')
            print('        TextColor = { 1.0, 1.0, 1.0 },')
            print('        TextSize = text_size,')
            print('        TextMinMaxSize = { text_min_size, text_max_size },')
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
