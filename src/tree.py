'''
Cosmic View of Life on Earth

Tree processing code. Trees are comprised of 3 elements: 
1. Leaves: The current day species/taxon
2. Clades: The internal branch points, which represent the hypothetical common ancestor of
   a group of species.
3. Branches: The lines that connect the leaves and clades.
Assets are created for each of these elements. Some assets have multiple files, some are
CSV and some are speck.

Author: Brian Abbott <abbott@amnh.org>, Hollister Herhold <hherhold@amnh.org>

Created: June 2023
'''

import sys
#import re
import pandas as pd
from pathlib import Path
from Bio import Phylo

from src import common

class tree:
    '''
    This class processes tree data for the Cosmic View of Life on Earth project. Trees are
    comprised of 3 elements: 
    1. Leaves: The current day species/taxon
    2. Clades: The internal branch points, which represent the hypothetical common
       ancestor of a group of species.
    3. Branches: The lines that connect the leaves and clades.

    These three elements are processed separately, with .csv files for the clades and
    leaves, and a .speck file for the branches.
    '''

    def __init__(self):

        # Number of leaves in the tree
        self.num_leaves = 0

    def process_leaves(self, datainfo):
        '''
        Process the tree leaves csv file. This file contains the current day
        species/taxon. 

        Input:
            dict(datainfo)

        Output:
            .csv
        '''

        common.print_subhead_status('Processing tree data - leaves')

        # Generate the Consensus points for the tree. These will be points that sit on the
        # tips of the tree branches -- the leaves.
        # ------------------------------------------------------------------------------------------
        datainfo['data_group_title'] = datainfo['sub_project'] + ': Consensus Tree'
        datainfo['data_group_desc'] = 'Data points for the tree - leaves.'

        # These are the "leaves"--the current day (extant) species.
        inpath = Path.cwd() / common.DATA_DIRECTORY / datainfo['dir'] / datainfo['tree_dir'] / datainfo['tree_leaves_file']
        common.test_input_file(inpath)

        leaves = pd.read_csv(inpath)

        # Rearrange the columns
        leaves = leaves[['x', 'y', 'z', 'name']]

        # Add underscores to the taxon names
        leaves['name'] = leaves['name'].str.replace(' ', '_')

        # Move the z values down
        leaves.loc[:, 'z'] = leaves['z'].apply(lambda x: x - common.TRANSFORM_TREE_Z * 2.15)
        #print(leaves)


        # Write data to files
        outpath = Path.cwd() / datainfo['dir'] / datainfo['tree_dir']
        common.test_path(outpath)

        outfile_csv = datainfo['dir'] + '_leaves.csv'
        outpath_csv = outpath / outfile_csv
        

        with open(outpath_csv, 'w') as csvfile:

            datainfo['author'] = 'Brian Abbott (American Museum of Natural History, New York), Wandrille Duchemin (University of Basel & SIB Swiss Institute of Bioinformatics), Robin Ridell (Univ Linköping), Märta Nilsson (Univ Linköping)'

            header = common.header(datainfo, script_name=Path(__file__).name)
            print(header, file=csvfile)

            leaves.to_csv(csvfile, index=False, lineterminator='\n')
            
        # Report to stdout
        common.out_file_message(outpath_csv)

    def process_internal(self, datainfo):
        '''
        Process the tree clades csv file. This file contains the internal branch points of
        the tree. Not all of these are to be displayed - many are simply internal branch
        points and do not have named clades. These are named "internalXX" where XX is a
        number. (It may have more than two digits, or only have one. It depends on the
        number of internal branch points.)

        Input:
            dict(datainfo)

        Output:
            .speck
        '''

        common.print_subhead_status('Processing tree data - internal/clades')

        datainfo['data_group_title'] = datainfo['sub_project'] + ': Consensus Tree'
        datainfo['data_group_desc'] = 'Data points for the tree - internal nodes (clades).'

        inpath = Path.cwd() / common.DATA_DIRECTORY / datainfo['dir'] / datainfo['tree_dir'] / datainfo['tree_internal_file']
        common.test_input_file(inpath)

        nodes = pd.read_csv(inpath)

        # Discard the internal nodes that start with 'internal' and have no name.
        nodes = nodes[nodes['name'].str.contains('internal') == False]

        # Rearrange the columns
        nodes = nodes[['x', 'y', 'z', 'name']]

        # Add underscores to the taxon names
        nodes['name'] = nodes['name'].str.replace(' ', '_')

        # Move the z values down
        nodes.loc[:, 'z'] = nodes['z'].apply(lambda x: x - common.TRANSFORM_TREE_Z)
        nodes.loc[:, 'z'] = nodes['z'].apply(lambda x: x * common.SCALE_TREE_Z)

        # Write data to files
        outpath = Path.cwd() / datainfo['dir'] / datainfo['tree_dir']
        common.test_path(outpath)

        outfile_csv = datainfo['dir'] + '_internal.csv'
        outpath_csv = outpath / outfile_csv
        

        with open(outpath_csv, 'w') as csvfile:

            datainfo['author'] = 'Brian Abbott (American Museum of Natural History, New York), Wandrille Duchemin (University of Basel & SIB Swiss Institute of Bioinformatics), Robin Ridell (Univ Linköping), Märta Nilsson (Univ Linköping)'

            header = common.header(datainfo, script_name=Path(__file__).name)
            print(header, file=csvfile)

            nodes.to_csv(csvfile, index=False, lineterminator='\n')
            
        # Report to stdout
        common.out_file_message(outpath_csv)
        

    def process_leaves_interpolated(self, datainfo):
        '''
        Process the tree points that can be interpolated. These are
        A. the consensus points that are placed in XYZ space as a result of
            indicator vector computation and data reduction
        B. The leaves of the tree, along with the tree, which indicate 
            phylogenetic relationships.
        The idea is to show the relationship between the data reduced consensus points
        and the "actual" tree of life. (Big quotes on "actual" here because all trees
        are hypotheses.)

        Input:
            dict(datainfo)

        Output:
            .csv
            The format of this file has columns as follows:
                time, x, y, z, name
            The first set of points are the leaves of the tree at t=0, and the 
            second set is the consensus points at t=1.
        '''

        common.print_subhead_status('Processing tree data - interpolated')

        # Generate the Consensus points for the tree. These will be points that sit on the tips
        # of the tree branches -- the leaves.
        # ------------------------------------------------------------------------------------------
        datainfo['data_group_title'] = datainfo['sub_project'] + ': Consensus Tree'
        datainfo['data_group_desc'] = 'Interpolatable points for the tree.'

        # These are the "leaves"--the current day species.
        inpath = Path.cwd() / common.DATA_DIRECTORY / datainfo['dir'] / datainfo['tree_dir'] / datainfo['tree_leaves_file']
        common.test_input_file(inpath)

        # The data is in the format of x, y, z, name.
        leaves = pd.read_csv(inpath)

        # We need to sort the leaves by the name. This is because the consensus points
        # may be in a different order than the leaves, and they all need to be in the same
        # order for the interpolation to work.
        leaves = leaves.sort_values(by='name')

        # Add underscores to the taxon names
        leaves['name'] = leaves['name'].str.replace(' ', '_')

        # Move the z values down. This is all of the transforms that are applied to the
        # non-interpolated data, also called the "tabletop" points that sit at the tips of
        # the tree.
        leaves.loc[:, 'z'] = leaves['z'].apply(lambda x: x - common.TRANSFORM_TREE_Z * 2.15)

        # Next load in the consensus points. Note that these do not get scaled or
        # transformed as they're already in the correct position (which we want to
        # interpolate to).
        # ------------------------------------------------------------------------------------------
        # Architecturally, this is a little bit of a hack. We're going to read in the
        # consensus points which are actually processed in consensus_species.py, and we
        # need to read them here and do the exact same processing as done in
        # consensus_species.py. Ideally we'd be able to ask consensus_species.py what the
        # processed data is, but that's a bit of a pain. So we're going to read in the
        # data here and do the same processing. This is a bit of a hack, but it's the best
        # we can do for now.
        inpath = Path.cwd() / common.DATA_DIRECTORY / datainfo['dir'] / datainfo['catalog_directory'] / datainfo['consensus_file']
        common.test_input_file(inpath)
    
        # Read in the CSV file
        # 'Taxon' header is not present in the CSV, so remove all the headers, and add them manually
        consensus = pd.read_csv(inpath, header=0, names=['name', 'x', 'y', 'z'])

        # Like the leaves, we need to sort the consensus points by the name. This is
        # because the leaves are sorted by name, and we need to make sure that the
        # consensus points are in the same order.
        consensus = consensus.sort_values(by='name')

        consensus['name'] = consensus['name'].str.replace(' ', '_')

        # Rescale consensus points. This is the same scaling that is done in
        # consensus_species.py, so if that changes, this needs to change as well.
        consensus['x'] = consensus['x'].multiply(common.POSITION_SCALE_FACTOR)
        consensus['y'] = consensus['y'].multiply(common.POSITION_SCALE_FACTOR)
        consensus['z'] = consensus['z'].multiply(common.POSITION_SCALE_FACTOR)

        # Write data to files
        outpath = Path.cwd() / datainfo['dir'] / datainfo['tree_dir']
        common.test_path(outpath)

        outfile_csv = datainfo['dir'] + '_interpolated.csv'
        outpath_csv = outpath / outfile_csv
        
        with open(outpath_csv, 'wt') as csvfile:

            datainfo['author'] = 'Brian Abbott (American Museum of Natural History, New York), Wandrille Duchemin (University of Basel & SIB Swiss Institute of Bioinformatics), Robin Ridell (Univ Linköping), Märta Nilsson (Univ Linköping)'

            header = common.header(datainfo, script_name=Path(__file__).name)
            print(header, file=csvfile)

            # OpenSpace requires a header that describes the columns.
            print('time,x,y,z,name', file=csvfile)

            # There are only two points in time:
            # 0: The leaves of the tree
            # 1: The consensus points
            for _, row in leaves.iterrows():
                print(f"0,{row['x']:.8f},{row['y']:.8f},{row['z']:.8f},{row['name']}", file=csvfile)

            # There may be more consensus points than leaves. Write out the consensus points but skip
            # any points that are not in the leaves.
            for _, row in consensus.iterrows():
                if row['name'] in leaves['name'].values:
                    print(f"1,{row['x']:.8f},{row['y']:.8f},{row['z']:.8f},{row['name']}", file=csvfile)

        # Finally, set the number of leaves for this tree. This value is used in the asset file.
        self.num_leaves = len(leaves)

        # Report to stdout
        common.out_file_message(outpath_csv)





    def process_branches(self, datainfo):
        '''
        Create the lines (branches) for a tree. This creates a file of "mesh" statements,
        used to draw the lines, and a dat file that OpenSpace needs to attach each line
        with an identifier.

        Input: 
            dict(datainfo) datainfo['dir'].branches.csv: file with the pairs of points
            that make up each line

        Output:
            datainfo['dir']_branches.speck: Series of "mesh" commands that will draw a
            line in OpenSpace. datainfo['dir']_branches.dat: a "key" file that is used by
            OpenSpace under the hood.
        '''


        inpath = Path.cwd() / common.DATA_DIRECTORY / datainfo['dir'] / datainfo['tree_dir'] / datainfo['tree_branches_file']
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
        outpath = Path.cwd() / datainfo['dir'] / datainfo['tree_dir']
        common.test_path(outpath)

        outfile_speck = datainfo['dir'] + '_branches.speck'
        outpath_speck = outpath / outfile_speck
        outfile_dat = datainfo['dir'] + '_branches.dat'
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


    def make_asset_branches(self, datainfo):
        '''
        Generate the asset file for the tree.
        
        Input: 
            dict(datainfo)

        Output:
            datainfo['dir']_branches.asset
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
        path = Path.cwd() / datainfo['dir'] / datainfo['tree_dir']
        #files = sorted(path.glob('*.speck'))



        #for path in files:
            
        file = path.name

        # Set the nested dict
        asset_info[file] = {}

        asset_info[file]['speck_file'] = datainfo['dir'] + '_branches.speck'
        
        #print(asset_info[file]['speck_file'], path, path.name)
        asset_info[file]['speck_var'] = common.file_variable_generator(asset_info[file]['speck_file'])

        #asset_info[file]['label_file'] = path.stem + '.label'
        #asset_info[file]['label_var'] = common.file_variable_generator(asset_info[file]['label_file'])

        #asset_info[file]['cmap_file'] = path.stem + '.cmap'
        #asset_info[file]['cmap_var'] = common.file_variable_generator(asset_info[file]['cmap_file'])

        asset_info[file]['dat_file'] = datainfo['dir'] + '_branches.dat'
        asset_info[file]['dat_var'] = common.file_variable_generator(asset_info[file]['dat_file'])

        asset_info[file]['asset_rel_path'] = '.'

        asset_info[file]['os_scenegraph_var'] = datainfo['dir'] + '_' + datainfo['tree_dir'] + '_branches'
        asset_info[file]['os_identifier_var'] = datainfo['dir'] + '_' + datainfo['tree_dir'] + '_branches'

        asset_info[file]['gui_name'] = 'Branches'
        asset_info[file]['gui_path'] = '/' + datainfo['sub_project'] + '/' + datainfo['tree_dir'].replace('_', ' ').title()

        # Open the file to write to
        outfile = datainfo['dir'] + '_branches.asset'
        outpath = Path.cwd() / datainfo['dir'] / datainfo['tree_dir'] / outfile
        with open(outpath, 'wt') as asset:

            # Switch stdout to the file
            sys.stdout = asset

            print('-- ' + datainfo['project'] + ' / ' + datainfo['data_group_title'])
            print("-- This file is auto-generated in the " + self.make_asset_branches.__name__ + "() function inside " + Path(__file__).name)
            print('-- Author: Brian Abbott <abbott@amnh.org>')
            print()


            print('local ' + asset_info[file]['dat_var'] + ' = asset.resource("' + asset_info[file]['asset_rel_path'] + '/' + asset_info[file]['dat_file'] + '")')

            for file in asset_info:
                print('local ' + asset_info[file]['speck_var'] + ' = asset.resource("' + asset_info[file]['asset_rel_path'] + '/' + asset_info[file]['speck_file'] + '")')


            for file in asset_info:

                print('local ' + asset_info[file]['os_scenegraph_var'] + ' = {')
                print('    Identifier = "' + asset_info[file]['os_identifier_var'] + '",')
                print('    Renderable = {')
                print('        UseCache = false,')
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

            # Switch the stdout back to normal stdout (screen)
            sys.stdout = original_stdout

        
            # Report to stdout
            common.out_file_message(outpath)
            print()


    def make_asset_for_taxa(self, datainfo, taxa):
        '''
        Generate the asset file for the tree.
        
        Input: 
            dict(datainfo)

        Output:
            datainfo['dir']_'taxa'.asset
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
        path = Path.cwd() / datainfo['dir'] / datainfo['tree_dir']
        #files = sorted(path.glob('*.speck'))

        #for path in files:
            
        file = path.name

        # Set the nested dict
        asset_info[file] = {}

        asset_info[file]['csv_file'] = datainfo['dir'] + '_' + taxa + '.csv'
        asset_info[file]['csv_var'] = common.file_variable_generator(asset_info[file]['csv_file'])

        #asset_info[file]['label_file'] = path.stem + '.label'
        #asset_info[file]['label_var'] = common.file_variable_generator(asset_info[file]['label_file'])

        #asset_info[file]['cmap_file'] = path.stem + '.cmap'
        #asset_info[file]['cmap_var'] = common.file_variable_generator(asset_info[file]['cmap_file'])

        asset_info[file]['dat_file'] = path.stem + '.dat'
        asset_info[file]['dat_var'] = common.file_variable_generator(asset_info[file]['dat_file'])

        asset_info[file]['asset_rel_path'] = '.'

        asset_info[file]['os_scenegraph_var'] = datainfo['dir'] + '_' + \
            datainfo['tree_dir'].replace('.', '_') + '_' + taxa
        asset_info[file]['os_identifier_var'] = datainfo['dir'] + '_' + \
            datainfo['tree_dir'].replace('.', '_') + '_' + taxa

        # Convert taxa to title case
        asset_info[file]['gui_name'] = taxa.title()
        asset_info[file]['gui_path'] = '/' + datainfo['sub_project'] + '/' + datainfo['tree_dir'].replace('_', ' ').title()



        # Open the file to write to
        outfile = datainfo['dir'] + '_' + taxa + '.asset'
        outpath = Path.cwd() / datainfo['dir'] / datainfo['tree_dir'] / outfile
        with open(outpath, 'wt') as asset:

            # Switch stdout to the file
            sys.stdout = asset

            print('-- ' + datainfo['project'] + ' / ' + datainfo['data_group_title'])
            print("-- This file is auto-generated in the " + self.make_asset_for_taxa.__name__ + "() function inside " + Path(__file__).name)
            print('-- Author: Brian Abbott <abbott@amnh.org>')
            print()


            print('local ' + asset_info[file]['dat_var'] + ' = asset.resource("' + asset_info[file]['asset_rel_path'] + '/' + asset_info[file]['dat_file'] + '")')

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
                print('        DataMapping = { Name="name"},')
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

    def make_asset_leaves_interpolated(self, datainfo):
        '''
        Generate the asset file for the tree.
        
        Input: 
            dict(datainfo)

        Output:
            datainfo['dir']_interpolated.asset
        '''

        # We shift the stdout to our filehandle so that we don't have to keep putting
        # the filehandle in every print statement.
        # Save the original stdout so we can switch back later
        original_stdout = sys.stdout

        # Define the main dict that will hold all the info needed per file
        # This is a nested dict with the format:
        #      { path: { root:  , filevar:  , os_variable:  , os_identifier:  , name:  } }
        asset_info = {}

        path = Path.cwd() / datainfo['dir'] / datainfo['tree_dir']
        file = path.name

        # Set the nested dict
        asset_info[file] = {}

        asset_info[file]['csv_file'] = datainfo['dir'] + '_interpolated.csv'
        asset_info[file]['csv_var'] = common.file_variable_generator(asset_info[file]['csv_file'])

        #asset_info[file]['label_file'] = path.stem + '.label'
        #asset_info[file]['label_var'] = common.file_variable_generator(asset_info[file]['label_file'])

        #asset_info[file]['cmap_file'] = path.stem + '.cmap'
        #asset_info[file]['cmap_var'] = common.file_variable_generator(asset_info[file]['cmap_file'])

        asset_info[file]['asset_rel_path'] = '.'

        asset_info[file]['os_scenegraph_var'] = datainfo['dir'] + '_' + datainfo['tree_dir'] + '_interpolated'
        asset_info[file]['os_identifier_var'] = datainfo['dir'] + '_' + datainfo['tree_dir'] + '_interpolated'

        asset_info[file]['gui_name'] = 'Interpolated Leaves'
        asset_info[file]['gui_path'] = '/' + datainfo['sub_project'] + '/' + datainfo['tree_dir'].replace('_', ' ').title()

        # Open the file to write to
        outfile = datainfo['dir'] + '_interpolated.asset'
        outpath = Path.cwd() / datainfo['dir'] / datainfo['tree_dir'] / outfile
        with open(outpath, 'wt') as asset:

            # Switch stdout to the file
            sys.stdout = asset

            print('-- ' + datainfo['project'] + ' / ' + datainfo['data_group_title'])
            print("-- This file is auto-generated in the " + self.make_asset_branches.__name__ + "() function inside " + Path(__file__).name)
            print('-- Author: Brian Abbott <abbott@amnh.org>')
            print()

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
                print('        Type = "RenderableInterpolatedPoints",')
                print('         Coloring = {')
                print('            FixedColor = { 0.8, 0.8, 0.8 }')
                print('        },')
                print('        Opacity = 1.0,')
                print('        SizeSettings = { ScaleFactor = scale_factor, ScaleExponent = scale_exponent },')
                print('        File = ' + asset_info[file]['csv_var'] + ',')
                print('        NumberOfObjects = ' + str(self.num_leaves) + ',')
                #print('        DrawLabels = false,')
                #print('        LabelFile = ' + asset_info[file]['label_var'] + ',')
                #print('        TextColor = { 1.0, 1.0, 1.0 },')
                #print('        TextSize = text_size,')
                #print('        TextMinMaxSize = { text_min_size, text_max_size },')
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

    def process_newick(self, datainfo):
        '''
        Process the newick file. This file contains the tree structure in newick format.

        Input:
            dict(datainfo)

        Output:
            .newick
        '''

        common.print_subhead_status('Processing tree data - newick')

        inpath = Path.cwd() / common.DATA_DIRECTORY / datainfo['dir'] / common.TREE_DIRECTORY / datainfo['newick_file']
        common.test_input_file(inpath)

        tree = Phylo.read(inpath, 'newick')

        # Perform a depth-first traversal of the tree and print the name of each node
        # as we traverse the tree.
        for clade in tree.find_clades(order='postorder'):
            print(clade.name)
    

