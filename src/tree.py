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
import pandas as pd
from pathlib import Path
from Bio import Phylo
from ete3 import Tree
import math
import matplotlib as mpl
import shutil
from integrate_tree_to_XYZ import integrate_tree_to_XYZ as itt
from src import common, colors
import re

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
        self.tree = None
        self.missing_leaves = None

    def process_nodes(self, datainfo, node_type):
        '''
        Process tree nodes csv file. Nodes can be either internal or leaves. 

        The output csv file has the x, y, z, name, and color columns. The color
        column is an index into the color map file, used to group nodes into
        categories and is generally based on taxonomic groups (also called parent
        lineages), though they can also beused for other categories.

        Input:
            dict(datainfo)

        Output:
            .csv
        '''

        # instead of loading the processed CSV file, we'll load the raw data file (set
        # in the datainfo dictionary) and process it here. 
        common.print_subhead_status(f'Processing tree data, {node_type} - ' + datainfo['tree_dir'])

        datainfo['data_group_title'] = datainfo['sub_project'] + ': Tree, ' + datainfo['tree_dir']
        datainfo['data_group_desc'] = f'Data points for the tree - {node_type}.'

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
        if self.tree is None:
            self.tree, self.missing_leaves = itt.integrate_tree_to_XYZ(inputFile = coords_file_path,
                                                                      inputTree = tree_file_path,
                                                                      use_z_from_file=use_provided_z,
                                                                      spherical_layout=spherical_tree)
            
        if ('dump_debug_tree' in datainfo.keys()) and (datainfo['dump_debug_tree'] == True):
            (itt.get_branches_dataframe(self.tree)).to_csv(f"{datainfo['tree_dir']}_debugHH_tree_branches.csv")

        # Output filenames and paths. Construction of these must match the filenames in
        # make_asset_nodes() so that the asset file can find them.
        outpath = Path.cwd() / datainfo['dir'] / datainfo['tree_dir']
        common.test_path(outpath)
        outfile_csv = outpath.name + '_' + node_type + '.csv'
        outpath_csv = outpath / outfile_csv

        if node_type == 'leaves':
            leaves = itt.get_leaves_dataframe(self.tree, self.missing_leaves)

            # Rearrange the columns
            leaves = leaves[['x', 'y', 'z', 'name']]

            ## HH Why do we need to do this?
            # Add underscores to the taxon names
            #leaves['name'] = leaves['name'].str.replace(' ', '_')

            # Translate and scale the tree so that it's viewable in OpenSpace.
            leaves.loc[:, 'z'] = leaves['z'].apply(lambda x: x * datainfo['scale_tree_z'])
            leaves.loc[:, 'z'] = leaves['z'].apply(lambda x: x - datainfo['transform_tree_z'])

            # Make a new color column in the leaves dataframe.
            leaves['color'] = 0

            # Also make a column that holds the parent lineage of each leaf. This should
            # correspond to the color in a one-to-one mapping that matches the color map
            # file. This column is mostly for debug and checking.
            leaves['clade'] = ''

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

                # Is there a predefined color map set? If so, use that for colors. It 
                # should have labeled lineage info in the comment field that is used
                # to determine color indices for each leaf (or node).

                if (datainfo['os_colormap_file'] != None):
                    inpath = Path.cwd() / common.DATA_DIRECTORY / common.COLOR_DIRECTORY / datainfo['os_colormap_file']
                    common.test_input_file(inpath)

                    colormap_df = colors.read_cmap_into_df(inpath)

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

                        # Look up the color index in the colormap dataframe and
                        # assign the color index to the leaf.
                        color_index = colormap_df[colormap_df['taxon'] == lineage]['index'].iloc[0]
                        leaves.at[i, 'color'] = color_index
                        leaves.at[i, 'clade'] = lineage

                    # The color column is now a float, but we need it to be an integer. Convert it.
                    leaves['color'] = leaves['color'].astype(int)

                    # Finally, we need to copy the colormap file to the tree directory. This file
                    # is used by OpenSpace to color the leaves based on the color column.
                    # The outpath here is constructed as below when the CSV file for the 
                    # leaves is written out.
                    outpath = Path.cwd() / datainfo['dir'] / datainfo['tree_dir']
                    common.test_path(outpath)
                    shutil.copyfile(inpath, outpath / datainfo['os_colormap_file'])

                
                else:
                    # We need to make a colormap from scratch. Start with the number of
                    # colors we need, which is the number of lineages.
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

            with open(outpath_csv, 'w') as csvfile:

                datainfo['author'] = 'Brian Abbott (American Museum of Natural History, New York), Wandrille Duchemin (University of Basel & SIB Swiss Institute of Bioinformatics), Robin Ridell (Univ Linköping), Märta Nilsson (Univ Linköping)'

                header = common.header(datainfo, script_name=Path(__file__).name)
                print(header, file=csvfile)

                leaves.to_csv(csvfile, index=False, lineterminator='\n')
                
            # Report to stdout
            common.out_file_message(outpath_csv)
        else:
            # By default the internal nodes are named with just numbers or placeholders. 
            # For some trees, we want to name internal nodes with the name of monophyletic
            # groups (such as orders for trees that have families as leaves). Check to see
            # if we need to do this.
            # Are the leaf-type or clade-type keys set in the datainfo dictionary? If so,
            # we need to do some work.
            if ('leaf-type' in datainfo.keys()) and ('clade-type' in datainfo.keys()):
                # First grab the metadata file. We need this to look up the parent lineage
                # (clade name).
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
                metadata = metadata.set_index(taxon_name).to_dict()[parent_lineage]

                # The metadata probably (hopefully?) has more information than we need. 
                # We need to deal with only the clades we've seen, not *all* clades. Let's
                # keep track of those we've seen so we can iterate over just these when
                # naming the internal nodes.
                all_clades_seen = set()

                # Start by iterating over all the leaves and naming the clade type for each.
                for leaf in self.tree.get_leaves():
                    clade_name = metadata[leaf.name]
                    leaf.add_features(clade_type=clade_name)

                    all_clades_seen.add(clade_name)

                # Now for each clade that we've seen (which is the parent lineage), we need to
                # find the most recent common ancestor of all the leaves in that clade. This
                # will be the internal node that we want to name with the clade type.
                for clade in all_clades_seen:
                    # Get all the leaves that are in this clade.
                    leaves_in_clade = [leaf for leaf in self.tree.get_leaves() if leaf.clade_type == clade]

                    # Get the most recent common ancestor of all the leaves in the clade.
                    clade_node = self.tree.get_common_ancestor(leaves_in_clade)

                    # Name the node with the clade type.
                    clade_node.name = clade
                # Finally, we need to clear out all the node names set by Wandrille's code.
                # We only want the internal nodes that we've named to have names. 
                # Wandrille's code names the internal nodes with single-quoted numbers.
                for node in self.tree.traverse():
                    if re.match(r"\'\d+\'", node.name):
                        node.name = ""


            nodes = itt.get_internal_nodes_dataframe(self.tree)

            # Rearrange the columns
            nodes = nodes[['x', 'y', 'z', 'name']]

            # Add underscores to the taxon names
            nodes['name'] = nodes['name'].str.replace(' ', '_')

            # Move the z values down
            #nodes.loc[:, 'z'] = nodes['z'].apply(lambda x: x - datainfo['transform_tree_z'])
            nodes.loc[:, 'z'] = nodes['z'].apply(lambda x: x * datainfo['scale_tree_z'])
            nodes.loc[:, 'z'] = nodes['z'].apply(lambda x: x - datainfo['transform_tree_z'])

            with open(outpath_csv, 'w') as csvfile:

                datainfo['author'] = 'Brian Abbott (American Museum of Natural History, New York), Wandrille Duchemin (University of Basel & SIB Swiss Institute of Bioinformatics), Robin Ridell (Univ Linköping), Märta Nilsson (Univ Linköping)'

                header = common.header(datainfo, script_name=Path(__file__).name)
                print(header, file=csvfile)

                nodes.to_csv(csvfile, index=False, lineterminator='\n')
                
            # Report to stdout
            common.out_file_message(outpath_csv)

        # The files created here are also used by other parts of the code. Return them
        # back to the caller by modifying the datainfo dictionary.
        datainfo['nodes_csv_file'] = outpath_csv

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

        omit_last_branch = ('omit_last_branch' in datainfo.keys()) \
            and (datainfo['omit_last_branch'] == True)
        branch_lines = itt.get_branches_dataframe(tree, omit_last_branch)

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
        outfile_speck = outpath.name + '_branches.speck'
        outpath_speck = outpath / outfile_speck
        outfile_dat = outpath.name + '_branches.dat'
        outpath_dat = outpath / outfile_dat

        # The files created here are also used by other parts of the code. Return them
        # back to the caller by modifying the datainfo dictionary.
        datainfo['branches_speck_file'] = outfile_speck
        datainfo['branches_dat_file'] = outfile_dat

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

        asset_info[file]['speck_file'] = path.name + '_branches.speck'
        
        asset_info[file]['speck_var'] = 'speck_' + common.file_variable_generator(asset_info[file]['speck_file'])


        #asset_info[file]['label_file'] = path.name + '.label'
        #asset_info[file]['label_var'] = common.file_variable_generator(asset_info[file]['label_file'])

        #asset_info[file]['cmap_file'] = path.name + '.cmap'
        #asset_info[file]['cmap_var'] = common.file_variable_generator(asset_info[file]['cmap_file'])

        asset_info[file]['dat_file'] = path.name + '_branches.dat'
        asset_info[file]['dat_var'] = 'dat_' + common.file_variable_generator(asset_info[file]['dat_file'])

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
            xxxxxxx_'taxa'.asset
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

        asset_info[file]['csv_file'] = path.name + '_' + taxa + '.csv'
        asset_info[file]['csv_var'] = common.file_variable_generator(asset_info[file]['csv_file'])

        #asset_info[file]['label_file'] = path.name + '.label'
        #asset_info[file]['label_var'] = common.file_variable_generator(asset_info[file]['label_file'])

        # If there is an os_colormap_file defined and not empty, use that as the colormap
        # file. The exception catching here is because there are two possibilties: it may
        # not be set at all, in which case it doesn't exists, or it might be empty.
        try:
            if datainfo['os_colormap_file']:
                asset_info[file]['cmap_file'] = datainfo['os_colormap_file']
            else:
                asset_info[file]['cmap_file'] = path.name + '.cmap'
        except KeyError:
            asset_info[file]['cmap_file'] = path.name + '.cmap'


        asset_info[file]['cmap_var'] = common.file_variable_generator(asset_info[file]['cmap_file'])

        asset_info[file]['dat_file'] = path.name + '.dat'
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
                print(f'local {asset_info[file]["cmap_var"]} = asset.resource("./{cmap_filename}")')
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

    def process_newick(self, datainfo):
        '''
        Process the newick file. This file contains the tree structure in newick format.

        This function does processing of both branches and nodes. The outputs are csv
        files for the nodes and leaves, and a speck file for the branches. Nodes and
        leaves are RenderablePointClouds, while branches are RenderableConstellationLines.

        Positions of the nodes and lines in space are calculated using modified/adapted
        tree drawing functions from Biopython's Phylo code.

        Trees often need to be scaled depending on branch lengths and number of
        taxa in the tree. Some trees have no branch lengths, some are scaled by
        coalescent units, and some are nucleotide substitutions over time. The
        data_info branch_scaling_factor and taxon_scaling_factor are used to scale
        the tree.

        Input:
            dict(datainfo), which points to a newick file

        Output:
            speck file for branches
            csv files for nodes and leaves
            
        '''
        x_node_positions = []
        y_node_positions = []

        common.print_subhead_status('Processing tree data - newick')

        inpath = Path.cwd() / common.DATA_DIRECTORY / datainfo['dir']
        inpath /= Path(datainfo['tree_dir']) / datainfo['newick_file']
        common.test_input_file(inpath)

        phylo_tree = Phylo.read(inpath, 'newick')

        # These two functions were lifted verbatim from Biopython's Phylo code. They are
        # used to calculate the positions of the nodes and leaves in the tree.
        def get_x_positions(tree):
            """
            Create a mapping of each clade to its horizontal position.
            Dict of {clade: x-coord}
            """
            depths = tree.depths()
            # If there are no branch lengths, assume unit branch lengths
            if not max(depths.values()):
                depths = tree.depths(unit_branch_lengths=True)
            return depths

        def get_y_positions(tree):
            """
            Create a mapping of each clade to its vertical position.
            Dict of {clade: y-coord}.
            Coordinates are negative, and integers for tips.
            """
            maxheight = tree.count_terminals()
            # Rows are defined by the tips
            heights = {
                tip: maxheight - i for i, tip in enumerate(reversed(tree.get_terminals()))
            }

            # Internal nodes: place at midpoint of children
            def calc_row(clade):
                for subclade in clade:
                    if subclade not in heights:
                        calc_row(subclade)
                # Closure over heights
                heights[clade] = (
                    heights[clade.clades[0]] + heights[clade.clades[-1]]
                ) / 2.0

            if tree.root.clades:
                calc_row(tree.root)
            return heights
        
        # Dataframe to hold the start and end coordinates of the branch lines. This is
        # used to create the branch lines in the speck file and is ordered [x0, y0, z0,
        # x1, y1, z1, name]. The branch name is the clade for that particular branch and
        # may be empty.
        branch_lines_df = pd.DataFrame(columns=['name', 
                                                'x0', 'y0', 'z0', 
                                                'x1', 'y1', 'z1'])

        # The next two functions are largely from Biopython's Phylo code but are
        # modified - color and line width removed, for example, as well as
        # linecollection stuff used by matplotlib.
        def draw_clade_lines(orientation="horizontal", 
                             y_here=0, x_start=0, x_here=0, y_bot=0, y_top=0):
            if orientation == "horizontal":
                #print(f'(x_start, y_here), (x_here, y_here): {(x_start, y_here), (x_here, y_here)}')
                branch_lines_df.loc[len(branch_lines_df.index)] = \
                    ['dummy', x_start, y_here, 0.0, x_here, y_here, 0.0]
            elif  orientation == "vertical":
                #print(f'(x_here, y_bot), (x_here, y_top): {(x_here, y_bot), (x_here, y_top)}')
                branch_lines_df.loc[len(branch_lines_df.index)] = \
                    ['dummy', x_here, y_bot, 0.0, x_here, y_top, 0.0]

        def draw_clade(clade, x_start):
            """Recursively draw a tree, down from the given clade."""
            x_here = x_node_positions[clade]
            y_here = y_node_positions[clade]

            # Draw a horizontal line from start to here
            draw_clade_lines(orientation="horizontal",
                y_here=y_here,
                x_start=x_start,
                x_here=x_here)

            if clade.clades:
                # Draw a vertical line connecting all children
                y_top = y_node_positions[clade.clades[0]]
                y_bot = y_node_positions[clade.clades[-1]]
                # Only apply widths to horizontal lines, like Archaeopteryx
                draw_clade_lines(orientation="vertical",
                    x_here=x_here,
                    y_bot=y_bot,
                    y_top=y_top,)
                # Draw descendents
                for child in clade:
                    draw_clade(child, x_here)

        # Get the positions of the leaves and internal nodes.
        x_node_positions = get_x_positions(phylo_tree)
        y_node_positions = get_y_positions(phylo_tree)

        # Now make a dataframe of the nodes and leaves. The dataframe will have the
        # columns: name, x, y, z. The z values are all set to 0.0.
        nodes = []
        leaves = []
        for node in phylo_tree.find_clades():
            x = x_node_positions.get(node)
            y = y_node_positions.get(node)
            if node.is_terminal():
                leaves.append([x, y, 0.0, node.name])
            else:
                nodes.append([x, y, 0.0, node.name])
        nodes = pd.DataFrame(nodes, columns=['x', 'y', 'z', 'name'])
        leaves = pd.DataFrame(leaves, columns=['x', 'y', 'z', 'name'])

        # Add color and clade columns.
        # FIXME: This is hardcoded for now. The color mapping is done at the order level
        # for the internal nodes and the leaves. This is because there are hundreds of
        # families and only 30 orders (at least, for insects). The colors for the orders
        # are the same for the internal nodes and the leaves.
        nodes['color'] = '1'
        nodes['clade'] = 'dummy'
        leaves['color'] = '1'
        leaves['clade'] = 'dummy'

        # Now draw the branches. draw_clade populates the branch_lines_df dataframe,
        # so we don't have to make one after the fact. Maybe it would be more 
        # consistent if draw_clade returned a dataframe, but this is fine for now.
        draw_clade(phylo_tree.root, 0)

        # Scale the node and branch positions (if required).
        if 'branch_scaling_factor' in datainfo:
            nodes.loc[:, 'x'] = nodes['x'].apply(lambda x: x * datainfo['branch_scaling_factor'])
            leaves.loc[:, 'x'] = leaves['x'].apply(lambda x: x * datainfo['branch_scaling_factor'])
            branch_lines_df.loc[:, 'x0'] = branch_lines_df['x0'].apply(lambda x: x * datainfo['branch_scaling_factor'])
            branch_lines_df.loc[:, 'x1'] = branch_lines_df['x1'].apply(lambda x: x * datainfo['branch_scaling_factor'])
        if 'taxon_scaling_factor' in datainfo:
            nodes.loc[:, 'y'] = nodes['y'].apply(lambda x: x * datainfo['taxon_scaling_factor'])
            leaves.loc[:, 'y'] = leaves['y'].apply(lambda x: x * datainfo['taxon_scaling_factor'])
            branch_lines_df.loc[:, 'y0'] = branch_lines_df['y0'].apply(lambda x: x * datainfo['taxon_scaling_factor'])
            branch_lines_df.loc[:, 'y1'] = branch_lines_df['y1'].apply(lambda x: x * datainfo['taxon_scaling_factor'])

        # Finally, write everything to files. First the nodes and leaves.
        outpath = Path.cwd() / datainfo['dir'] / datainfo['tree_dir']
        common.test_path(outpath)
        # CSV files don't get headers. (Should they? Can they?)
        nodes_outfile = outpath / (outpath.name + '_internal.csv')
        leaves_outfile = outpath / (outpath.name + '_leaves.csv')
        nodes.to_csv(nodes_outfile, index=False, lineterminator='\n')
        leaves.to_csv(leaves_outfile, index=False, lineterminator='\n')

        # These speck and dat filenames must be generated in the same way as in
        # make_asset_branches() so that the asset file can find them.
        outfile_speck = outpath.name + '_branches.speck'
        outpath_speck = outpath / outfile_speck
        outfile_dat = outpath.name + '_branches.dat'
        outpath_dat = outpath / outfile_dat

        with open(outpath_speck, 'wt') as speck, open(outpath_dat, 'wt') as dat:
            datainfo['author'] = 'Hollister Herhold and Brian Abbott (American Museum of Natural History, New York), Wandrille Duchemin (University of Basel & SIB Swiss Institute of Bioinformatics), Robin Ridell (Univ Linköping), Märta Nilsson (Univ Linköping)'
            datainfo['data_group_title'] = datainfo['sub_project'] + ': Tree, ' + datainfo['tree_dir']
            datainfo['data_group_desc'] = 'Data points for the tree - branches.'

            header = common.header(datainfo, script_name=Path(__file__).name)
            print(header, file=speck)

            for _, row in branch_lines_df.iterrows():
                print('mesh -c 1 {', file=speck)
                print(f"  id {row['name']}", file=speck)
                print('  2', file=speck)
                print(f"  {row['x0']:.8f} {row['y0']:.8f} {row['z0']:.8f}", file=speck)
                print(f"  {row['x1']:.8f} {row['y1']:.8f} {row['z1']:.8f}", file=speck)
                print('}', file=speck)

                print(f"{row['name']} {row['name']}", file=dat)

        common.out_file_message(outpath_speck)
        common.out_file_message(outpath_dat)
        common.out_file_message(nodes_outfile)
        common.out_file_message(leaves_outfile)

