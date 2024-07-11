#!/bin/env python3

'''
make_tree.py

This script processes newick files to create asset and data files to visualize
trees with models in OpenSpace. It's separate from the other scripts in this directory
as those are designed to process timetree data, whereas this script doesn't follow
the same datapath pipeline.

For nodes that use a model, a separate file specified on the command line contains
the list of models to use for a given node. More than one model may be used for a
given node, for example the insect body as one model and the tracheae as another.

Some of the code here was borrowed from tree.py.

'''

import ete3
import argparse
from Bio import Phylo
from pathlib import Path
from src import common
import pandas as pd

parser = argparse.ArgumentParser(description='Process a newick file to create asset '
                                 'and data files for OpenSpace.')

# Gotta have an input file.
parser.add_argument('-i', '--input', dest="input_newick_file", 
                    help='The newick file to process.', required=True)

# Models file. This is a csv file with the columns: name, model1, model2, model3, etc.
# See the model reader function below for more details on the model file. Note
# that the models file is optional, and not every node must have a model.
parser.add_argument('-m', '--models', dest='models_file', type=str,
                    help='The csv file with the models for the nodes.')

# Output directory for speck and asset files.
parser.add_argument('-o', '--output_path', dest='out_path', type=str, default='trees',
                     help='Output directory for the speck and asset files.')

# Name for this tree.
parser.add_argument('-n', '--name', dest='tree_name', type=str, default='tree',
                     help='Name for this tree.')

# Add floating point arguments for scaling the tree.
parser.add_argument('--branch_scaling_factor', type=float, default=400.0, 
                    help='Scale the branches by this factor.')
parser.add_argument('--taxon_scaling_factor', type=float, default=10.0, 
                    help='Scale the taxa by this factor.')

def main():
    args = parser.parse_args()
    make_tree_files_for_OS(input_newick_file=args.input_newick_file,
                           branch_scaling_factor=args.branch_scaling_factor,
                           taxon_scaling_factor=args.taxon_scaling_factor,
                           tree_name=args.tree_name,
                           output_path=args.out_path)


def make_tree_files_for_OS(input_newick_file, 
                           branch_scaling_factor=400.0, 
                           taxon_scaling_factor=10.0,
                           tree_name='tree',
                           output_path = '.',
                           point_scale_factor = 1.25,
                           point_scale_exponent=3.2):
    '''
    Process the newick file. This file contains the tree structure in newick format.

    This function does processing of both branches and nodes. The outputs are csv
    files for the nodes and leaves, and a speck file for the branches. Nodes and
    leaves are RenderablePointClouds, while branches are RenderableConstellationLines.
    This function also creates the asset file. This is a separate operation in the
    'main' code but is integrated here.

    Positions of the nodes and lines in space are calculated using modified/adapted
    tree drawing functions from Biopython's Phylo code.

    Trees often need to be scaled depending on branch lengths and number of
    taxa in the tree. Some trees have no branch lengths, some are scaled by
    coalescent units, and some are nucleotide substitutions over time. The
    data_info branch_scaling_factor and taxon_scaling_factor are used to scale
    the tree.

    Input:

    Output:
        speck file for branches
        csv files for nodes and leaves
        
    '''
    x_node_positions = []
    y_node_positions = []

    phylo_tree = Phylo.read(input_newick_file, 'newick')

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
    nodes.loc[:, 'x'] = nodes['x'].apply(lambda x: x * branch_scaling_factor)
    leaves.loc[:, 'x'] = leaves['x'].apply(lambda x: x * branch_scaling_factor)
    branch_lines_df.loc[:, 'x0'] = branch_lines_df['x0'].apply(lambda x: x * branch_scaling_factor)
    branch_lines_df.loc[:, 'x1'] = branch_lines_df['x1'].apply(lambda x: x * branch_scaling_factor)
    nodes.loc[:, 'y'] = nodes['y'].apply(lambda x: x * taxon_scaling_factor)
    leaves.loc[:, 'y'] = leaves['y'].apply(lambda x: x * taxon_scaling_factor)
    branch_lines_df.loc[:, 'y0'] = branch_lines_df['y0'].apply(lambda x: x * taxon_scaling_factor)
    branch_lines_df.loc[:, 'y1'] = branch_lines_df['y1'].apply(lambda x: x * taxon_scaling_factor)

    # Convert the path to an actual Path object. Path is actually pretty handy (pathlib)
    # if you're careful about how you use it.
    output_path = Path(output_path)
    # Make the output directory if it doesn't exist.
    output_path.mkdir(parents=True, exist_ok=True)

    # CSV files don't get headers. (Should they? Can they?)
    nodes_outfile = output_path / (tree_name + '_internal.csv')
    leaves_outfile = output_path / (tree_name + '_leaves.csv')
    nodes.to_csv(nodes_outfile, index=False, lineterminator='\n')
    leaves.to_csv(leaves_outfile, index=False, lineterminator='\n')

    speck_out_filename = tree_name + '_branches.speck'
    speck_out_fullpath = output_path / speck_out_filename
    dat_out_filename = tree_name + '_branches.dat'
    dat_out_fullpath = output_path / dat_out_filename


    with open(speck_out_fullpath, 'wt') as speck, open(dat_out_fullpath, 'wt') as dat:
        '''
        datainfo = {}
        datainfo['author'] = 'Hollister Herhold and Brian Abbott (American Museum of Natural History, New York), Wandrille Duchemin (University of Basel & SIB Swiss Institute of Bioinformatics), Robin Ridell (Univ Linköping), Märta Nilsson (Univ Linköping)'
        datainfo['data_group_title'] = datainfo['sub_project'] + ': Tree, ' + datainfo['tree_dir']
        datainfo['data_group_desc'] = 'Data points for the tree - branches.'

        header = common.header(datainfo, script_name=Path(__file__).name)
        print(header, file=speck)
        '''
        for _, row in branch_lines_df.iterrows():
            print('mesh -c 1 {', file=speck)
            print(f"  id {row['name']}", file=speck)
            print('  2', file=speck)
            print(f"  {row['x0']:.8f} {row['y0']:.8f} {row['z0']:.8f}", file=speck)
            print(f"  {row['x1']:.8f} {row['y1']:.8f} {row['z1']:.8f}", file=speck)
            print('}', file=speck)

            print(f"{row['name']} {row['name']}", file=dat)

    # Next - write asset file.
    asset_out_filename = tree_name + '.asset'
    with open(outpath, 'wt') as asset:

        # Switch stdout to the file
        sys.stdout = asset

        



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

        print('local scale_factor = '   + str(point_scale_factor))
        print('local scale_exponent = ' + str(point_scale_exponent))
        print('local text_size = '      + common.TEXT_SIZE)
        print('local text_min_size = '  + common.TEXT_MIN_SIZE)
        print('local text_max_size = '  + common.TEXT_MAX_SIZE)
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



if __name__ == '__main__':
    main()
    