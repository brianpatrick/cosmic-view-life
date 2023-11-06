'''
Cosmic View of Life on Earth

Process the tree of primates which makes the points and the lines that
represent the evolution.

Author: Brian Abbott <abbott@amnh.org>
Created: June 2023
'''

import sys
#import re
import pandas as pd
from pathlib import Path

import common



def process_data(datainfo):
    '''
    Process the primate tree of life points. These consist of "leaves" which are the 
    present day species/taxon, and the interrnal branch points, which are the nexus
    of common ancestors, all the way down to the one common ancestor of all primates.

    Input:
        dict(datainfo)

    Output:
        .speck
        .csv
        .cmap
    '''

    common.print_subhead_status('Processing Primate tree data')

    datainfo['data_group_title'] = datainfo['sub_project'] + ': Consensus Tree'
    datainfo['data_group_desc'] = 'Data points for the primate consensus tree.'


    # First, convert the csv raw files into speck files.
    # These are the internal branch points
    inpath = Path.cwd() / common.DATA_DIRECTORY / datainfo['dir'] / 'tree' / 'primates.internal.csv'
    common.test_input_file(inpath)

    internal_branches = pd.read_csv(inpath)

    # Rearrange the columns
    internal_branches = internal_branches[['x', 'y', 'z', 'name']]

    # Move the z values down, to transform the data down from the origin
    internal_branches.loc[:, 'z'] = internal_branches['z'].apply(lambda x: x - common.TRANSFORM_TREE_Z)
    #print(internal_branches)



    # These are the "leaves"--the current day species.
    inpath = Path.cwd() / common.DATA_DIRECTORY / datainfo['dir'] / 'tree' / 'primates.leaves.csv'
    common.test_input_file(inpath)

    leaves = pd.read_csv(inpath)

    # Rearrange the columns
    leaves = leaves[['x', 'y', 'z', 'name']]

    # Move the z values down, to transform the data down from the origin
    leaves.loc[:, 'z'] = leaves['z'].apply(lambda x: x - common.TRANSFORM_TREE_Z)

    # Add underscores to the taxon names
    leaves['name'] = leaves['name'].str.replace(' ', '_')

    # Move the z values down
    leaves.loc[:, 'z'] = leaves['z'].apply(lambda x: x - common.TRANSFORM_TREE_Z)
    #print(leaves)


    # Write data to files
    outpath = Path.cwd() / datainfo['dir'] / common.TREE_DIRECTORY
    common.test_path(outpath)

    outfile_speck = 'primates_leaves.speck'
    outpath_speck = outpath / outfile_speck
    

    with open(outpath_speck, 'wt') as speck:

        datainfo['author'] = 'Brian Abbott (American Museum of Natural History, New York), Wandrille Duchemin (University of Basel & SIB Swiss Institute of Bioinformatics), Robin Ridell (Univ Linköping), Märta Nilsson (Univ Linköping)'

        header = common.header(datainfo, script_name=Path(__file__).name)
        print(header, file=speck)

        for _, row in leaves.iterrows():
            print(f"{row['x']:.8f} {row['y']:.8f} {row['z']:.8f} # {row['name']}", file=speck)


    # Report to stdout
    common.out_file_message(outpath_speck)

    




def process_branches(datainfo):
    '''
    Create the lines (branches) for the primate tree of life.
    This creates a file of "mesh" statements, used to draw the lines, and
    a dat file that OpenSpace needs to attach each line with an identifier.

    Input: 
        dict(datainfo)
        primates.branches.csv: file with the pairs of points that make up each line

    Output:
        primate_branches.speck: Series of "mesh" commands that will draw a line in OpenSpace.
        primate_branches.dat: a "key" file that is used by OpenSpace under the hood.
    '''


    inpath = Path.cwd() / common.DATA_DIRECTORY / datainfo['dir'] / common.TREE_DIRECTORY / 'primates.branches.csv'
    common.test_input_file(inpath)

    branch_lines = pd.read_csv(inpath)

    # Transform the 'z' axis
    branch_lines.loc[:, 'z0'] = branch_lines['z0'].apply(lambda x: x - common.TRANSFORM_TREE_Z)
    branch_lines.loc[:, 'z1'] = branch_lines['z1'].apply(lambda x: x - common.TRANSFORM_TREE_Z)

    branch_lines.loc[:, 'z0'] = branch_lines['z0'].apply(lambda x: x * common.SCALE_TREE_Z)
    branch_lines.loc[:, 'z1'] = branch_lines['z1'].apply(lambda x: x * common.SCALE_TREE_Z)


    # remove the 'branch_' from the beginning for each name
    branch_lines['name'] = branch_lines.name.str.replace('branch_' , '')

    # Add underscores for spaces
    branch_lines['name'] = branch_lines.name.str.replace(' ' , '_')


    # Write data to files
    outpath = Path.cwd() / datainfo['dir'] / common.TREE_DIRECTORY
    common.test_path(outpath)

    outfile_speck = 'primates_branches.speck'
    outpath_speck = outpath / outfile_speck
    outfile_dat = 'primates_branches.dat'
    outpath_dat = outpath / outfile_dat

    with open(outpath_speck, 'wt') as speck, open(outpath_dat, 'wt') as dat:

        datainfo['author'] = 'Brian Abbott (American Museum of Natural History, New York), Wandrille Duchemin (University of Basel & SIB Swiss Institute of Bioinformatics), Robin Ridell (Univ Linköping), Märta Nilsson (Univ Linköping)'

        header = common.header(datainfo, script_name=Path(__file__).name)
        print(header, file=speck)

        for _, row in branch_lines.iterrows():
            print('mesh -c 1 {', file=speck)
            print(f"  id {row['name']}", file=speck)
            print('  2', file=speck)
            print(f"  {row['x0']:.8f} {row['y0']:.8f} {row['z0']:.8f}", file=speck)
            print(f"  {row['x1']:.8f} {row['y1']:.8f} {row['z1']:.8f}", file=speck)
            print('}', file=speck)

            print(f"{row['name']} {row['name']}", file=dat)


    # Report to stdout
    common.out_file_message(outpath_speck)
    common.out_file_message(outpath_dat)









def make_asset_branches(datainfo):
    '''
    Generate the asset file for the primate tree of life.
    
    Input: 
        dict(datainfo)

    Output:
        primate_braanches.asset
    '''

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
    path = Path.cwd() / datainfo['dir'] / common.TREE_DIRECTORY
    #files = sorted(path.glob('*.speck'))



    #for path in files:
        
    file = path.name
    #file = 'primates_branches.speck'

    # Set the nested dict
    asset_info[file] = {}

    asset_info[file]['speck_file'] = 'primates_branches.speck'
    
    #print(asset_info[file]['speck_file'], path, path.name)
    asset_info[file]['speck_var'] = common.file_variable_generator(asset_info[file]['speck_file'])

    #asset_info[file]['label_file'] = path.stem + '.label'
    #asset_info[file]['label_var'] = common.file_variable_generator(asset_info[file]['label_file'])

    #asset_info[file]['cmap_file'] = path.stem + '.cmap'
    #asset_info[file]['cmap_var'] = common.file_variable_generator(asset_info[file]['cmap_file'])

    asset_info[file]['dat_file'] = 'primates_branches.dat'
    asset_info[file]['dat_var'] = common.file_variable_generator(asset_info[file]['dat_file'])

    asset_info[file]['asset_rel_path'] = '.'

    asset_info[file]['os_scenegraph_var'] = datainfo['dir'] + '_' + common.TREE_DIRECTORY
    asset_info[file]['os_identifier_var'] = datainfo['dir'] + '_' + common.TREE_DIRECTORY

    asset_info[file]['gui_name'] = common.TREE_DIRECTORY.replace('_', ' ').title()
    asset_info[file]['gui_path'] = '/' + datainfo['sub_project']



    # Open the file to write to
    outfile = datainfo['dir'] + '_' + common.TREE_DIRECTORY + '.asset'
    outpath = Path.cwd() / datainfo['dir'] / common.TREE_DIRECTORY / outfile
    with open(outpath, 'wt') as asset:

        # Switch stdout to the file
        sys.stdout = asset

        print('-- ' + datainfo['project'] + ' / ' + datainfo['data_group_title'])
        print("-- This file is auto-generated in the " + make_asset_branches.__name__ + "() function inside " + Path(__file__).name)
        print('-- Author: Brian Abbott <abbott@amnh.org>')
        print()


        print('local ' + asset_info[file]['dat_var'] + ' = asset.localResource("' + asset_info[file]['asset_rel_path'] + '/' + asset_info[file]['dat_file'] + '")')

        for file in asset_info:
            print('local ' + asset_info[file]['speck_var'] + ' = asset.localResource("' + asset_info[file]['asset_rel_path'] + '/' + asset_info[file]['speck_file'] + '")')


        for file in asset_info:

            print('local ' + asset_info[file]['os_scenegraph_var'] + ' = {')
            print('    Identifier = "' + asset_info[file]['os_identifier_var'] + '",')
            print('    Renderable = {')
            print('        Type = "RenderableConstellationLines",')
            print('        Colors = { { 0.6, 0.4, 0.4 }, { 0.8, 0.0, 0.0 }, { 0.0, 0.3, 0.8 } },')
            print('        Opacity = 0.7,')
            print('        NamesFile = ' + asset_info[file]['dat_var'] + ',')
            print('        File = ' + asset_info[file]['speck_var'] + ',')
            print('        Unit = "Km",')
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


        

        # asset.meta = {
        # Name = "Constellations_2023",
        # Version = "1.3",
        # Description = "Digital Universe asset for constellation lines",
        # Author = "Brian Abbott (AMNH)",
        # URL = "https://www.amnh.org/research/hayden-planetarium/digital-universe",
        # License = "AMNH Digital Universe"
        # }


        # Switch the stdout back to normal stdout (screen)
        sys.stdout = original_stdout

    
        # Report to stdout
        common.out_file_message(outpath)
        print()









def make_asset_data(datainfo):
    '''
    Generate the asset file for the primate tree of life data.
    
    Input: 
        dict(datainfo)

    Output:
        primate_branches_data.asset
    '''

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
    path = Path.cwd() / datainfo['dir'] / common.TREE_DIRECTORY
    #files = sorted(path.glob('*.speck'))



    #for path in files:
        
    # file = path.name
    file = 'primates_leaves.speck'

    # Set the nested dict
    asset_info[file] = {}

    asset_info[file]['speck_file'] = path.name
    #print(asset_info[file]['speck_file'], path, path.name)
    asset_info[file]['speck_var'] = common.file_variable_generator(asset_info[file]['speck_file'])

    #asset_info[file]['label_file'] = path.stem + '.label'
    #asset_info[file]['label_var'] = common.file_variable_generator(asset_info[file]['label_file'])

    #asset_info[file]['cmap_file'] = path.stem + '.cmap'
    #asset_info[file]['cmap_var'] = common.file_variable_generator(asset_info[file]['cmap_file'])

    asset_info[file]['dat_file'] = path.stem + '.dat'
    asset_info[file]['dat_var'] = common.file_variable_generator(asset_info[file]['dat_file'])

    asset_info[file]['asset_rel_path'] = '.'

    asset_info[file]['os_scenegraph_var'] = datainfo['dir'] + '_' + common.TREE_DIRECTORY
    asset_info[file]['os_identifier_var'] = datainfo['dir'] + '_' + common.TREE_DIRECTORY

    asset_info[file]['gui_name'] = common.TREE_DIRECTORY.replace('_', ' ').title()
    asset_info[file]['gui_path'] = '/' + datainfo['sub_project']



    # Open the file to write to
    outfile = datainfo['dir'] + '_' + common.TREE_DIRECTORY + '.asset'
    outpath = Path.cwd() / datainfo['dir'] / common.TREE_DIRECTORY / outfile
    with open(outpath, 'wt') as asset:

        # Switch stdout to the file
        sys.stdout = asset

        print('-- ' + datainfo['project'] + ' / ' + datainfo['data_group_title'])
        print("-- This file is auto-generated in the " + make_asset_branches.__name__ + "() function inside " + Path(__file__).name)
        print('-- Author: Brian Abbott <abbott@amnh.org>')
        print()


        print('local ' + asset_info[file]['dat_var'] + ' = asset.localResource("' + asset_info[file]['asset_rel_path'] + '/' + asset_info[file]['dat_file'] + '")')

        for file in asset_info:
            print('local ' + asset_info[file]['speck_var'] + ' = asset.localResource("' + asset_info[file]['asset_rel_path'] + '/' + asset_info[file]['speck_file'] + '")')


        for file in asset_info:

            print('local ' + asset_info[file]['os_scenegraph_var'] + ' = {')
            print('    Identifier = "' + asset_info[file]['os_identifier_var'] + '",')
            print('    Renderable = {')
            print('        Type = "RenderableConstellationLines",')
            print('        Colors = { { 0.6, 0.4, 0.4 }, { 0.8, 0.0, 0.0 }, { 0.0, 0.3, 0.8 } },')
            print('        Opacity = 0.7,')
            print('        NamesFile = ' + asset_info[file]['dat_var'] + ',')
            print('        File = ' + asset_info[file]['speck_var'] + ',')
            print('        Unit = "Km",')
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


        

        # asset.meta = {
        # Name = "Constellations_2023",
        # Version = "1.3",
        # Description = "Digital Universe asset for constellation lines",
        # Author = "Brian Abbott (AMNH)",
        # URL = "https://www.amnh.org/research/hayden-planetarium/digital-universe",
        # License = "AMNH Digital Universe"
        # }


        # Switch the stdout back to normal stdout (screen)
        sys.stdout = original_stdout

    
        # Report to stdout
        common.out_file_message(outpath)
        print()