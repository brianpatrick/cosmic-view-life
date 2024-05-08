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
import matplotlib as mpl

from integrate_tree_to_XYZ import integrate_tree_to_XYZ as itt
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
        Process the tree leaves csv file. 

        The output csv file has the x, y, z, name, and color columns. The color
        column is an index into the color map file, used to group the leaves into
        categories and is generally based on taxonomic groups (also called parent
        lineages), though they can also beused for other categories.

        Input:
            dict(datainfo)

        Output:
            .csv
        '''

        # instead of loading the processed CSV file, we'll load the raw data file (set
        # in the datainfo dictionary) and process it here. 
        common.print_subhead_status('Processing tree data, leaves - ' + datainfo['tree_dir'])

        datainfo['data_group_title'] = datainfo['sub_project'] + ': Tree, ' + datainfo['tree_dir']
        datainfo['data_group_desc'] = 'Data points for the tree - leaves.'

        tree_file_path = Path.cwd() / common.DATA_DIRECTORY / datainfo['dir'] / datainfo['tree_dir'] / datainfo['newick_file']
        coords_file_path = Path.cwd() / common.DATA_DIRECTORY / datainfo['dir'] / datainfo['tree_dir'] / datainfo['coordinates_file']
        common.test_input_file(tree_file_path)
        common.test_input_file(coords_file_path)

        # By default, use the provided Z coordinates. If the tree is spherical, the Z
        # coordinates are projected to lie on a sphere.
        use_provided_z = True
        spherical_tree = False

        if (datainfo['tree_type'] == 'tabletop'):
            use_provided_z = False
            spherical_tree = False
        elif (datainfo['tree_type'] == 'spherical'):
            use_provided_z = False
            spherical_tree = True
        elif (datainfo['tree_type'] == '3D'):
            use_provided_z = True
            spherical_tree = False
        else:
            print("ERROR: Tree type not recognized. Please set the tree type to 'tabletop', 'spherical', or '3D'.")
            sys.exit(1)

        # Use Wandrille's projection to get the XYZ coordinates for the leaves, depending
        # on the projection (spherical or not). Default behavior is to not use
        # spherical projection.
        tree, missing_leaves = itt.integrate_tree_to_XYZ(inputFile = coords_file_path,
                                                         inputTree = tree_file_path,
                                                         use_z_from_file=use_provided_z,
                                                         spherical_layout=spherical_tree)

        leaves = itt.get_leaves_dataframe(tree, missing_leaves)

        # Rearrange the columns
        leaves = leaves[['x', 'y', 'z', 'name']]

        # Add underscores to the taxon names
        leaves['name'] = leaves['name'].str.replace(' ', '_')

        # Move the z values down
        #leaves.loc[:, 'z'] = leaves['z'].apply(lambda x: x - datainfo['transform_tree_z'] * 2.15)
        #leaves.loc[:, 'z'] = leaves['z'].apply(lambda x: x - datainfo['transform_tree_z'])
        #print(leaves)
        leaves.loc[:, 'z'] = leaves['z'].apply(lambda x: x * datainfo['scale_tree_z'])
        leaves.loc[:, 'z'] = leaves['z'].apply(lambda x: x - datainfo['transform_tree_z'])

        # Z translate specific to leaves. Hacky.
        leaves.loc[:, 'z'] = leaves['z'].apply(lambda x: x - datainfo['translate_leaves_z'])
        print("*** METADATA FILE = " + str(datainfo['metadata_file']) + " ***")
        # If the metadata is set, use it to group the leaves into categories by color.
        if ('metadata_file' in datainfo.keys()) and (datainfo['metadata_file'] != None):
            # The CSV file has x, y, z, name, and a color index column. Colors are used to group
            # the leaves into different categories. Let's load in the metadata file and make
            # a dictionary out of it. The format is "taxon", "parent-lineage". Some examples of
            # this might be taxon=family (Syrphidae, for example) and parent-lineage=order 
            # (Diptera, for this example).
            inpath = Path.cwd() / common.DATA_DIRECTORY / datainfo['dir'] / datainfo['tree_dir'] / datainfo['metadata_file']
            common.test_input_file(inpath)

            # The Metadata file is in the format of taxon, parent-lineage. We want a dictionary
            # where we can look up the parent lineage for every taxon. The name of the taxon
            # (family, genus, or species) and parent-lineage (order, family, etc.) are in the
            # header of the csv file.
            metadata = pd.read_csv(inpath)

            # The first row holds the taxon name and parent-lineage name. We want to use the
            # taxon name as the index, and the parent-lineage as the value. 
            taxon_name = metadata.columns[0]
            parent_lineage = metadata.columns[1]

            taxon = metadata[taxon_name].tolist()
            metadata = metadata.set_index(taxon_name).to_dict()[parent_lineage]

            # Next we need to know how many unique parent lineages we have, and make a
            # mapping from each unique lineage to a unique integer, starting with 1. This
            # will be used to color the leaves.
            parent_lineages = set(metadata.values())
            parent_lineage_colors = {lineage: i + 1 for i, lineage in enumerate(parent_lineages)}

            # Now we need to run through the leaves and assign a color index to each one
            # based on the parent lineage. We'll add a new column to the leaves dataframe
            # called 'color'. For each leaf:
            for i, row in leaves.iterrows():
                # Get the parent lineage of the leaf. Some taxa may not have a parent
                # lineage or may not be in the metadata file. In this case, we'll just
                # assign the taxon name as the lineage. Zoraptera is one of these taxa.
                lineage = ''
                taxon = row['name']
                if taxon not in metadata.keys():
                    lineage = taxon
                else:
                    lineage = metadata[row['name']]
                # Assign the color based on the parent lineage
                leaves.at[i, 'color'] = parent_lineage_colors[lineage]

            # The color column is now a float, but we need it to be an integer. Convert it.
            leaves['color'] = leaves['color'].astype(int)

            # Finally, write out a color map file. This file will be used by OpenSpace to
            # color the leaves based on the color column. The first row is the number of
            # colors, followed by the colors themselves. The colors are in the format of
            # r, g, b, a. The colors are in the order of the parent lineages.
            # NOTE that the filename here must be the same as the one in make_asset_nodes().
            outpath = Path.cwd() / datainfo['dir'] / datainfo['tree_dir']
            common.test_path(outpath)
            cmap_filename = datainfo['tree_dir'] + '.cmap'
            cmap_path = outpath / cmap_filename
            
            # This is a hardcoded viridis colormap. I'm partial to this particular
            # colormap because it's colorblind friendly.
            cmap = mpl.cm.viridis
            norm = mpl.colors.Normalize(vmin=0, vmax=len(parent_lineages))

            # Color map files are a very simple format. The first line is the number
            # of colors in the file, followed by one line for each color. The color
            # is in the format of r, g, b, a followed by a comment prefaced by a '#'
            # with the color name. The color map file contains the number of colors in
            # the parent lineage.
            # Write out the color map file to cmap_path.
            with open(cmap_path, 'wt') as cmap_file:
                print(len(parent_lineages), file=cmap_file)
                for i in range(len(parent_lineages)):
                    c = cmap(norm(i))
                    print(f"{c[0]:.8f} {c[1]:.8f} {c[2]:.8f} 1.0 # {i}", file=cmap_file)

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

        common.print_subhead_status('Processing tree, internal/clades - ' + datainfo['tree_dir'])

        datainfo['data_group_title'] = datainfo['sub_project'] + ': Tree, ' + datainfo['tree_dir']
        datainfo['data_group_desc'] = 'Data points for the tree - internal nodes (clades).'

        tree_file_path = Path.cwd() / common.DATA_DIRECTORY / datainfo['dir'] / datainfo['tree_dir'] / datainfo['newick_file']
        coords_file_path = Path.cwd() / common.DATA_DIRECTORY / datainfo['dir'] / datainfo['tree_dir'] / datainfo['coordinates_file']
        common.test_input_file(tree_file_path)
        common.test_input_file(coords_file_path)

        # By default, use the provided Z coordinates. If the tree is spherical, the Z
        # coordinates are projected to lie on a sphere.
        use_provided_z = True
        spherical_tree = False

        if (datainfo['tree_type'] == 'tabletop'):
            use_provided_z = False
            spherical_tree = False
        elif (datainfo['tree_type'] == 'spherical'):
            use_provided_z = False
            spherical_tree = True
        elif (datainfo['tree_type'] == '3D'):
            use_provided_z = True
            spherical_tree = False

        # Use Wandrille's projection to get the XYZ coordinates for the leaves, depending
        # on the projection (spherical or not). Default behavior is to not use
        # spherical projection.
        tree, missing_leaves = itt.integrate_tree_to_XYZ(inputFile = coords_file_path,
                                                         inputTree = tree_file_path,
                                                         use_z_from_file=use_provided_z,
                                                         spherical_layout=spherical_tree)

        nodes = itt.get_internal_nodes_dataframe(tree)

        # Discard the internal nodes that start with 'internal' and have no name.
        nodes = nodes[nodes['name'].str.contains('internal') == False]

        # Rearrange the columns
        nodes = nodes[['x', 'y', 'z', 'name']]

        # Add underscores to the taxon names
        nodes['name'] = nodes['name'].str.replace(' ', '_')

        # Move the z values down
        #nodes.loc[:, 'z'] = nodes['z'].apply(lambda x: x - datainfo['transform_tree_z'])
        nodes.loc[:, 'z'] = nodes['z'].apply(lambda x: x * datainfo['scale_tree_z'])
        nodes.loc[:, 'z'] = nodes['z'].apply(lambda x: x - datainfo['transform_tree_z'])
        

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
        #leaves.loc[:, 'z'] = leaves['z'].apply(lambda x: x - datainfo['transform_tree_z'] * 2.15)
        leaves.loc[:, 'z'] = leaves['z'].apply(lambda x: x * datainfo['scale_tree_z'])
        leaves.loc[:, 'z'] = leaves['z'].apply(lambda x: x - datainfo['transform_tree_z'])

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

        # instead of loading the processed CSV file, we'll load the raw data file (set
        # in the datainfo dictionary) and process it here. 
        common.print_subhead_status('Processing tree data, branches - ' + datainfo['tree_dir'])

        datainfo['data_group_title'] = datainfo['sub_project'] + ': Tree, ' + datainfo['tree_dir']
        datainfo['data_group_desc'] = 'Data points for the tree - branches.'

        tree_file_path = Path.cwd() / common.DATA_DIRECTORY / datainfo['dir'] / datainfo['tree_dir'] / datainfo['newick_file']
        coords_file_path = Path.cwd() / common.DATA_DIRECTORY / datainfo['dir'] / datainfo['tree_dir'] / datainfo['coordinates_file']
        common.test_input_file(tree_file_path)
        common.test_input_file(coords_file_path)

        # By default, use the provided Z coordinates. If the tree is spherical, the Z
        # coordinates are projected to lie on a sphere.
        use_provided_z = True
        spherical_tree = False

        if (datainfo['tree_type'] == 'tabletop'):
            use_provided_z = False
            spherical_tree = False
        elif (datainfo['tree_type'] == 'spherical'):
            use_provided_z = False
            spherical_tree = True
        elif (datainfo['tree_type'] == '3D'):
            use_provided_z = True
            spherical_tree = False

        # Use Wandrille's projection to get the XYZ coordinates for the leaves, depending
        # on the projection (spherical or not). Default behavior is to not use
        # spherical projection.
        tree, missing_leaves = itt.integrate_tree_to_XYZ(inputFile = coords_file_path,
                                                         inputTree = tree_file_path,
                                                         use_z_from_file=use_provided_z,
                                                         spherical_layout=spherical_tree)

        branch_lines = itt.get_branches_dataframe(tree)

        # Transform the 'z' axis
        #branch_lines.loc[:, 'z0'] = branch_lines['z0'].apply(lambda x: x - datainfo['transform_tree_z'])
        #branch_lines.loc[:, 'z1'] = branch_lines['z1'].apply(lambda x: x - datainfo['transform_tree_z'])
        branch_lines.loc[:, 'z0'] = branch_lines['z0'].apply(lambda x: x * datainfo['scale_tree_z'])
        branch_lines.loc[:, 'z1'] = branch_lines['z1'].apply(lambda x: x * datainfo['scale_tree_z'])
        branch_lines.loc[:, 'z0'] = branch_lines['z0'].apply(lambda x: x - datainfo['transform_tree_z'])
        branch_lines.loc[:, 'z1'] = branch_lines['z1'].apply(lambda x: x - datainfo['transform_tree_z'])


        # remove the 'branch_' from the beginning for each name
        branch_lines['name'] = branch_lines.name.str.replace('branch_' , '')

        # Add underscores for spaces
        branch_lines['name'] = branch_lines.name.str.replace(' ' , '_')


        # Write data to files
        outpath = Path.cwd() / datainfo['dir'] / datainfo['tree_dir']
        common.test_path(outpath)

        # These speck and dat filenames must be generated in the same way as in
        # make_asset_branches() so that the asset file can find them.
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

        asset_info[file]['os_scenegraph_var'] = datainfo['dir'] + '_' + \
            datainfo['tree_dir'].replace('.', '_') + '_branches'
        asset_info[file]['os_identifier_var'] = datainfo['dir'] + '_' + \
            datainfo['tree_dir'].replace('.', '_') + '_branches'

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


    def make_asset_nodes(self, datainfo, taxa):
        '''

        Generate the asset file for the tree nodes. Nodes can be either internal nodes
        or leaves. This function is called twice, once for the internal nodes and once
        for the leaves.

        This function generates nodes for several kinds of trees, and some of these
        cases are hardcoded a bit here.

        Insect trees can be:
            1. Order level tree. The leaves are orders, and internal nodes are
                superorders, etc.
            2. Family level tree. The leaves are families, and internal nodes are
                orders (primarily).
            3. Genus level tree. The leaves are genera, and internal nodes are
                families (primarily).
            4. Species level tree. The leaves are species, and internal nodes are
                also probably families.
        
        As there are hundreds of families and only 30 orders, the color mapping is
        done at the order level. This means that the colors for the orders are the
        same for the internal nodes and the leaves. 

        
        Input: 
            dict(datainfo)
            str(taxa): 'internal' or 'leaves'

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

        asset_info[file]['cmap_file'] = path.stem + '.cmap'
        asset_info[file]['cmap_var'] = common.file_variable_generator(asset_info[file]['cmap_file'])

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
            print("-- This file is auto-generated in the " + self.make_asset_nodes.__name__ + "() function inside " + Path(__file__).name)
            print('-- Author: Brian Abbott <abbott@amnh.org>')
            print()


            print('local ' + asset_info[file]['dat_var'] + ' = asset.resource("' + asset_info[file]['asset_rel_path'] + '/' + asset_info[file]['dat_file'] + '")')

            # Not every asset has a color map file. Make the path to it given the data
            # from the asset_info dict and check to see if it's there.
            ## HH This hardcoded path finding is kinda dangerous...
            full_cmap_file_path = Path.cwd() / datainfo['dir'] / datainfo['tree_dir'] / asset_info[file]['asset_rel_path'] / asset_info[file]['cmap_file']
            cmap_filename = asset_info[file]['cmap_file']
            use_colormap = False
            if Path(full_cmap_file_path).exists():
                print(f'local {asset_info[file]['cmap_var']} = asset.resource("./{cmap_filename}")')
                use_colormap = True

            for file in asset_info:
                print('local ' + asset_info[file]['csv_var'] + ' = asset.resource("' + asset_info[file]['asset_rel_path'] + '/' + asset_info[file]['csv_file'] + '")')

            print('-- Set some parameters for OpenSpace settings')
            # if datainfo has point_scale_factor or scale exponent parameters set, use
            # those, otherwise use the defaults defined in common.py.
            scale_factor = common.POINT_SCALE_FACTOR
            if 'point_scale_factor' in datainfo:
                scale_factor = datainfo['point_scale_factor']
            else: 
                scale_factor = common.POINT_SCALE_FACTOR
            if 'scale_exponent' in datainfo:
               scale_exponent = datainfo['scale_exponent']
            else:
                scale_exponent = common.POINT_SCALE_EXPONENT
            print('local scale_factor = ' + str(scale_factor))
            print('local scale_exponent = ' + str(scale_exponent))
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
                #print('            FixedColor = { 0.8, 0.8, 0.8 }')
                if (taxa == 'internal') or (use_colormap == False):
                    # Gotta fix this. The colors for the orders for the internal nodes and
                    # the leaves need to be the same, so we need to make this mapping once
                    # and then re-use it.
                    print('            FixedColor = { 0.8, 0.8, 0.8 }')
                else:
                    print('            ColorMapping = { ')
                    print('                File = ' + asset_info[file]['cmap_var'] + ',')
                    print('                ParameterOptions = { { Key = "color" } }')
                    print('            }')
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

        inpath = Path.cwd() / common.DATA_DIRECTORY / datainfo['dir'] / datainfo['tree_dir'] / datainfo['newick_file']
        common.test_input_file(inpath)

        tree = Phylo.read(inpath, 'newick')

        Phylo.draw_ascii(tree)
        
    

