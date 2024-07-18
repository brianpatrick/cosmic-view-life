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
import json

parser = argparse.ArgumentParser(description='Process a newick file to create asset '
                                 'and data files for OpenSpace.')

# There are two ways to input parameters. The first way is to use a parameter
# file. This is a JSON file that contains all the parameters for the script. The
# second way is to specify them individually. The parameter file is specified with
# the -p flag. If the parameter file is specified, all other parameters are ignored.
# If the parameter file is not specified, the script will look for individual
# parameters. If the parameter file is specified, the script will ignore any
# individual parameters.
parser.add_argument('-p', '--param_file', dest='param_file', type=str,
                    help='The parameter file for the script.')

# Input file.
parser.add_argument('-i', '--input', dest="input_newick_file", 
                    help='The newick file to process.')

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

    # If a parameter file is specified, read it in and use it to set the arguments.
    if args.param_file:
        print("*** Reading parameter file {} ***".format(args.param_file))
        with open(args.param_file, 'rt') as json_file:
            args = json.load(json_file)
    else:
        # Just use the specified arguments.
        args = vars(args)

    # Print out the arguments.
    print("make_tree.\n -= Arguments =-")
    print(f"Input newick file:      {args['input_newick_file']}")
    print(f"Models file:            {args['models_file']}")
    print(f"Output path:            {args['out_path']}")
    print(f"Tree name:              {args['tree_name']}")
    print(f"Branch scaling factor:  {args['branch_scaling_factor']}")
    print(f"Taxon scaling factor:   {args['taxon_scaling_factor']}")

    make_tree_files_for_OS(input_newick_file=args['input_newick_file'],
                           models_filename=args['models_file'],
                           branch_scaling_factor=args['branch_scaling_factor'],
                           taxon_scaling_factor=args['taxon_scaling_factor'],
                           tree_name=args['tree_name'],
                           output_path=args['out_path'])


def make_tree_files_for_OS(input_newick_file,
                           models_filename, 
                           branch_scaling_factor, 
                           taxon_scaling_factor,
                           tree_name,
                           output_path):
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

    #
    # Write out the nodes and leaves CSV files.
    #

    # CSV files don't get headers. (Should they? Can they?)
    nodes_outfile = output_path / (tree_name + '_internal.csv')
    leaves_outfile = output_path / (tree_name + '_leaves.csv')
    nodes.to_csv(nodes_outfile, index=False, lineterminator='\n')
    leaves.to_csv(leaves_outfile, index=False, lineterminator='\n')

    speck_out_filename = tree_name + '_branches.speck'
    speck_out_fullpath = output_path / speck_out_filename
    dat_out_filename = tree_name + '_branches.dat'
    dat_out_fullpath = output_path / dat_out_filename

    #
    # Write out the branch speck and dat files.
    #
    print(" -= Output files =-")
    print(f"Branch speck file:      {speck_out_fullpath}")
    print(f"Branch dat file:        {dat_out_fullpath}")
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

    #
    # Asset files.
    #
    def print_common_local_vars(asset):
        print(f"local scale_factor = {common.POINT_SCALE_FACTOR}", file=asset)
        print(f"local scale_exponent = {common.POINT_SCALE_EXPONENT}", file=asset)
        print(f"local text_size = {common.TEXT_SIZE}", file=asset)
        print(f"local text_min_size = {common.TEXT_MIN_SIZE}", file=asset)
        print(f"local text_max_size = {common.TEXT_MAX_SIZE}", file=asset)

    # Nodes asset file.
    nodes_asset_filename = tree_name + '_internal.asset'
    nodes_asset_outpath = output_path / nodes_asset_filename

    print(f"Nodes asset file:       {nodes_asset_outpath}")
    with open(nodes_asset_outpath, 'wt') as asset:
        print(f"local dat_{tree_name}_internal = asset.resource(\"./{dat_out_filename}\")", file=asset)
        print(f"local csv_{tree_name}_internal = asset.resource(\"./{tree_name}_internal.csv\")", file=asset)
        print_common_local_vars(asset)
        print(f"local {tree_name}_internal = {{", file=asset)
        print(f"    Identifier = \"{tree_name}_internal\",", file=asset)
        print(f"    Renderable = {{", file=asset)
        print(f"        UseCaching = false,", file=asset)
        print(f"        Type = \"RenderablePointCloud\",", file=asset)
        print(f"        Coloring = {{", file=asset)
        print(f"            FixedColor = {{ 0.8, 0.8, 0.8 }}", file=asset)
        print(f"        }},", file=asset)
        print(f"        Opacity = 1.0,", file=asset)
        print(f"        SizeSettings = {{ ScaleFactor = scale_factor, ScaleExponent = scale_exponent }},", file=asset)
        print(f"        File = csv_{tree_name}_internal,", file=asset)
        print(f"        DataMapping = {{ Name=\"name\"}},", file=asset)
        print(f"        Labels = {{ Enabled = false, Size = text_size  }},", file=asset)
        print(f"        Unit = \"Km\",", file=asset)
        print(f"        BillboardMinMaxSize = {{ 0.0, 25.0 }},", file=asset)
        print(f"        EnablePixelSizeControl = true,", file=asset)
        print(f"        EnableLabelFading = false,", file=asset)
        print(f"        Enabled = true", file=asset)
        print(f"    }},", file=asset)
        print(f"    GUI = {{", file=asset)
        print(f"        Name = \"Internal\",", file=asset)
        print(f"        Path = \"/Insects/{tree_name}\"", file=asset)
        print(f"    }}", file=asset)
        print(f"}}", file=asset)
        print(f"asset.onInitialize(function()", file=asset)
        print(f"    openspace.addSceneGraphNode({tree_name}_internal)", file=asset)
        print(f"end)", file=asset)
        print(f"asset.onDeinitialize(function()", file=asset)
        print(f"    openspace.removeSceneGraphNode({tree_name}_internal)", file=asset)
        print(f"end)", file=asset)
        print(f"asset.export({tree_name}_internal)", file=asset)
    asset.close()
    
    # Leaves asset file.
    leaves_asset_filename = tree_name + '_leaves.asset'
    leaves_asset_outpath = output_path / leaves_asset_filename
    print(f"Leaves asset file:      {leaves_asset_outpath}")
    with open(leaves_asset_outpath, 'wt') as asset:
        print(f"local dat_{tree_name}_leaves = asset.resource(\"./{dat_out_filename}\")", file=asset)
        print(f"local csv_{tree_name}_leaves = asset.resource(\"./{tree_name}_leaves.csv\")", file=asset)
        print_common_local_vars(asset)
        print(f"local {tree_name}_leaves = {{", file=asset)
        print(f"    Identifier = \"{tree_name}_leaves\",", file=asset)
        print(f"    Renderable = {{", file=asset)
        print(f"        UseCaching = false,", file=asset)
        print(f"        Type = \"RenderablePointCloud\",", file=asset)
        print(f"        Coloring = {{", file=asset)
        print(f"            FixedColor = {{ 0.8, 0.8, 0.8 }}", file=asset)
        print(f"        }},", file=asset)
        print(f"        Opacity = 1.0,", file=asset)
        print(f"        SizeSettings = {{ ScaleFactor = scale_factor, ScaleExponent = scale_exponent }},", file=asset)
        print(f"        File = csv_{tree_name}_leaves,", file=asset)
        print(f"        DataMapping = {{ Name=\"name\"}},", file=asset)
        print(f"        Labels = {{ Enabled = false, Size = text_size  }},", file=asset)
        print(f"        Unit = \"Km\",", file=asset)
        print(f"        BillboardMinMaxSize = {{ 0.0, 25.0 }},", file=asset)
        print(f"        EnablePixelSizeControl = true,", file=asset)
        print(f"        EnableLabelFading = false,", file=asset)
        print(f"        Enabled = true", file=asset)
        print(f"    }},", file=asset)
        print(f"    GUI = {{", file=asset)
        print(f"        Name = \"Leaves\",", file=asset)
        print(f"        Path = \"/Insects/{tree_name}\"", file=asset)
        print(f"    }}", file=asset)
        print(f"}}", file=asset)
        print(f"asset.onInitialize(function()", file=asset)
        print(f"    openspace.addSceneGraphNode({tree_name}_leaves)", file=asset)
        print(f"end)", file=asset)
        print(f"asset.onDeinitialize(function()", file=asset)
        print(f"    openspace.removeSceneGraphNode({tree_name}_leaves)", file=asset)
        print(f"end)", file=asset)
        print(f"asset.export({tree_name}_leaves)", file=asset)
    asset.close()

    # Branches asset file.
    branches_asset_filename = tree_name + '_branches.asset'
    branches_asset_outpath = output_path / branches_asset_filename
    print(f"Branches asset file:    {branches_asset_outpath}")
    with open(branches_asset_outpath, 'wt') as asset:
        print(f"local dat_{tree_name}_branches = asset.resource(\"./{dat_out_filename}\")", file=asset)
        print(f"local speck_{tree_name}_branches = asset.resource(\"./{speck_out_filename}\")", file=asset)
        print(f"local {tree_name}_branches = {{", file=asset)
        print(f"    Identifier = \"{tree_name}_branches\",", file=asset)
        print(f"    Renderable = {{", file=asset)
        print(f"        UseCache = false,", file=asset)
        print(f"        Type = \"RenderableConstellationLines\",", file=asset)
        print(f"        Colors = {{ {{ 0.6, 0.4, 0.4 }}, {{ 0.8, 0.0, 0.0 }}, {{ 0.0, 0.3, 0.8 }} }},",
               file=asset)
        print(f"        Opacity = 0.7,", file=asset)
        print(f"        NamesFile = dat_{tree_name}_branches,", file=asset)
        print(f"        File = speck_{tree_name}_branches,", file=asset)
        print(f"        Unit = \"Km\",", file=asset)
        print(f"        Enabled = true", file=asset)
        print(f"    }},", file=asset)
        print(f"    GUI = {{", file=asset)
        print(f"        Name = \"Branches\",", file=asset)
        print(f"        Path = \"/Insects/{tree_name}\"", file=asset)
        print(f"    }}", file=asset)
        print(f"}}", file=asset)
        print(f"asset.onInitialize(function()", file=asset)
        print(f"    openspace.addSceneGraphNode({tree_name}_branches)", file=asset)
        print(f"end)", file=asset)
        print(f"asset.onDeinitialize(function()", file=asset)
        print(f"    openspace.removeSceneGraphNode({tree_name}_branches)", file=asset)
        print(f"end)", file=asset)
        print(f"asset.export({tree_name}_branches)", file=asset)
    asset.close()



    # Models asset file.
    # First, read the models file into a dictionary. Each line has a key, which is
    # the name of the node, a model file, and a scale value. Each node may have more
    # than one model.
    models = {}
    if models_filename:
        with open(models_filename, 'rt') as models_file:
            for line in models_file:
                # Ignore any lines starting with # as a comment.
                if not line.startswith('#'):
                    parts = line.strip().split(',')
                    model_name = parts[0]
                    model_url = parts[1].strip()
                    model_scale = float(parts[2].strip())
                    
                    if model_name in models:
                        models[model_name].append((model_url, model_scale))
                    else:
                        models[model_name] = [(model_url, model_scale)]

    # Return the x, y, and z position of a leaf given the name of the leaf.
    def get_leaf_position(leaf_name):
        for _, row in leaves.iterrows():
            if row['name'] == leaf_name:
                return row['x'], row['y'], row['z']
        return None

    # Write out the asset file. One asset file for all models.
    asset_filename = tree_name + '_models.asset'
    asset_outpath = output_path / asset_filename
    print(f"Asset file:             {asset_outpath}")
    with open(asset_outpath, 'wt') as asset:
        print(f"local sun = asset.require(\"scene/solarsystem/sun/transforms\")", file=asset)

        # Make a list scene graph node names. We will need this later for the
        # code that initializes and adds assets to OpenSpace.
        scene_graph_nodes = []

        # Run through the list of leaves, checking for a model.
        for _, row in leaves.iterrows():
            # print(row['name'])
            if row['name'] in models:
                scene_graph_nodes.append(row['name'])
                print(f"Model found for {row['name']}: {models[row['name']]}")
                for model in models[row['name']]:
                    model_url = model[0]
                    model_scale = model[1]
                    # Get the position of the leaf.
                    x, y, z = get_leaf_position(row['name'])
                    print(f"Position: {x}, {y}, {z}")

                    # Grab the filename. This is the last part of the URL. Remove any quotes
                    # from the filename.
                    model_filename = model_url.split('/')[-1]
                    model_filename = model_filename.replace('"', '')
                    # Remove any %20s from the filename.
                    model_filename = model_filename.replace('%20', '_')
                    # Remove any spaces.
                    model_filename = model_filename.replace(' ', '_')

                    # We need some kind of identifier inside the asset file. Let's construct
                    # this from the filename by just removing the extension.
                    model_identifier = model_filename.split('.')[0]
                    
                    print(f"local syncData_{row['name']} = asset.resource({{", file=asset)
                    print(f"    Name = \"{model_identifier}\",", file=asset)
                    print(f"    Type = \"UrlSynchronization\",", file=asset)
                    print(f"    Identifier = \"{model_identifier}\",", file=asset)
                    print(f"    Url = {model_url},", file=asset)
                    print(f"    Filename = \"{model_filename}\"", file=asset)
                    print(f"}})", file=asset)

                    print(f"local {row['name']} = {{", file=asset)
                    print(f"    Identifier = \"{row['name']}\",", file=asset)
                    print(f"    Transform = {{", file=asset)
                    print(f"        Translation = {{", file=asset)
                    print(f"            Type = \"StaticTranslation\",", file=asset)
                    print(f"            Position = {{ {x * 1000}, {y * 1000}, {z * 1000} }}", file=asset)
                    print(f"        }}", file=asset)
                    print(f"    }},", file=asset)
                    print(f"    Renderable = {{", file=asset)
                    print(f"        UseCaching = false,", file=asset)
                    print(f"        Type = \"RenderableModel\",", file=asset)
                    print(f"        Coloring = {{", file=asset)
                    print(f"            FixedColor = {{ 0.8, 0.8, 0.8 }}", file=asset)
                    print(f"        }},", file=asset)
                    print(f"        Opacity = 1.0,", file=asset)
                    print(f"        GeometryFile = syncData_{row['name']} .. \"{model_filename}\",", file=asset)
                    print(f"        ModelScale = {model_scale},", file=asset)
                    print(f"        Enabled = true,", file=asset)
                    print(f"        LightSources = {{", file=asset)
                    print(f"            sun.LightSource", file=asset)
                    print(f"        }}", file=asset)
                    print(f"    }},", file=asset)
                    print(f"    GUI = {{", file=asset)
                    print(f"        Name = \"{row['name']}\",", file=asset)
                    print(f"        Path = \"/Leaves\",", file=asset)
                    print(f"    }}", file=asset)
                    print(f"}}", file=asset)

        print(f"asset.onInitialize(function()", file=asset)
        for node in scene_graph_nodes:
            print(f"    openspace.addSceneGraphNode({node})", file=asset)
        print(f"end)", file=asset)
        print(f"asset.onDeinitialize(function()", file=asset)
        for node in scene_graph_nodes:
            print(f"    openspace.removeSceneGraphNode({node})", file=asset)
        print(f"end)", file=asset)
        for node in scene_graph_nodes:
            print(f"asset.export({node})", file=asset)
            
        asset.close()

if __name__ == '__main__':
    main()
    