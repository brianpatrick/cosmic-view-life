'''
Cosmic View of Life on Earth

Process Takanori's UMAP trial files.

We do this by passing the main seq df, which has the original data, reading in the 
.speck file so that we have the datavar lines, and then looping over all the original csv files
and making a new speck file for each of them. These new speck files have the x,y,z
replaced by Takanori's x,y,z values from his csv files.

Author: Brian Abbott <abbott@amnh.org>
Created: October 2022
'''

import sys
import pandas as pd
from pathlib import Path

import common


def process_data(datainfo, seq):
    '''
    Take a df and sub in the x,y,z values given another csv file. Not as generic as this
    function name would imply, but subbing the x,y,zs is what this does.

    Input:
        dict(datainfo)
        DataFrame(seq)
        *.speck             (sequence data file)
    
    Output:
        *.speck             (each speck file has the original file stem of the takanori raw csv file)
    '''

    common.print_subhead_status('Processing Takanori UMAP trials')
    
    datainfo['catalog_directory'] = 'takanori_version_1__2022_09_28'



    # Parse the speck file just to capture the datavar lines
    # Parse the speck file and return the header, datavar, and data lines as strings
    #in_speck_file = datainfo['dir'] + '.speck'
    in_speck_file = 'sequences.speck'
    seq_speck_path = Path.cwd() / datainfo['dir'] / 'MDS_v1' / common.SEQUENCE_DIRECTORY / in_speck_file
    common.test_input_file(seq_speck_path)

    (_, datavar_lines, _) = common.parse_speck(seq_speck_path, None)



    # Read the sequence file and process into a dataframe
    # ---------------------------------------------------------------------------
    inpath = Path.cwd() / common.DATA_DIRECTORY / datainfo['dir'] / datainfo['catalog_directory']

    # Get a listing of the csv files in the path
    files = inpath.glob('*.csv')

    # Cycle through the files in the directory
    for file in files:
        
        # Define a filename, file root, and set the path
        file = file.name
        fileroot = file.replace('.csv', '')
        path = inpath / file
        
        # set the datainfo name for each file
        datainfo['data_group_title'] = datainfo['sub_project'] + ': Takanori trial file ' + file
        datainfo['data_group_desc'] = 'DNA sample data for Takinori file ' + file + '. Each point represents one DNA sample.'

        # Read the csv file into a df
        takanori_df = pd.read_csv(path)

        # Merge the main seq df and the takanori df on the sequence ID
        df = pd.merge(seq, takanori_df, left_on='seq_id', right_on='seqid')

        # Drop the redundant columns
        df.drop(['x_x', 'y_x', 'z_x', 'taxon_y', 'Unnamed: 0'], axis=1, inplace=True)

        # Rename these columns, the *_y columns are the takanori x,y,z values.
        df.rename(columns = {'x_y':'x', 'y_y':'y', 'z_y':'z', 'taxon_x': 'taxon'}, inplace = True)


        # Rescale the position data
        df['x'] = df['x'].multiply(common.POSITION_SCALE_FACTOR / 10.0)
        df['y'] = df['y'].multiply(common.POSITION_SCALE_FACTOR / 10.0)
        df['z'] = df['z'].multiply(common.POSITION_SCALE_FACTOR / 10.0)




        # Print the data
        # ---------------------------------------------------------------------------
        outpath = Path.cwd() / datainfo['dir'] / common.TAKANORI_DIRECTORY
        common.test_path(outpath)

        outfile = fileroot + '.speck'
        outpath = outpath / outfile

        with open(outpath, 'wt') as speck:

            header = common.header(datainfo, None, Path(__file__).name)
            print(header, file=speck)

            # print the datavar lines
            print(datavar_lines, file=speck)

            # Print the data lines.
            for index, row in df.iterrows():
                print(f"{row['x']} {row['y']} {row['z']} {row['taxon_code']} {row['hybrid']} {row['synonymousDiff']} {row['NonSynonymousDiff']} {row['lineage_24_code']} {row['lineage_25_code']} {row['lineage_26_code']} {row['lineage_27_code']} {row['lineage_28_code']} {row['lineage_29_code']} {row['lineage_30_code']} {row['lineage_31_code']} # {row['speck_name']}", file=speck)


        # Report to stdout
        common.out_file_message(outpath)






def make_asset(datainfo):
    '''
    Generate the asset file for the takanori trial files.

    Input:
        dict(datainfo)
        A list of .speck files in the 'takanori' directory
        A color table file
        An input color table
    
    Output:
        takanori.asset
    '''

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
    path = Path.cwd() / datainfo['dir'] / common.TAKANORI_DIRECTORY
    files = sorted(path.glob('*.speck'))
    

    for path in files:
        
        file = path.name

        # Set the nested dict
        asset_info[file] = {}

        asset_info[file]['speck_file'] = path.name
        asset_info[file]['speck_var'] = common.file_variable_generator(asset_info[file]['speck_file'].replace('&', 'N'))

        # asset_info[file]['label_file'] = path.stem + '.label'
        # asset_info[file]['label_var'] = common.file_variable_generator(asset_info[file]['label_file'])

        # Hard-coding these because we want the same color map for all the different scenegraphs.
        asset_info[file]['cmap_file'] = '../MDS_v1/sequences/lineage_30.cmap'
        asset_info[file]['cmap_var'] = 'cmap_lineage_30'
        
        asset_info[file]['asset_rel_path'] = common.TAKANORI_DIRECTORY

        asset_info[file]['os_scenegraph_var'] = datainfo['dir'] + '_' + path.stem.replace('&', 'N')
        asset_info[file]['os_identifier_var'] = datainfo['dir'] + '_' + path.stem.replace('&', 'N')

        asset_info[file]['gui_name'] = path.stem.replace('_', ' ').title()
        asset_info[file]['gui_path'] = '/' + datainfo['sub_project'] + '/' + common.TAKANORI_DIRECTORY.replace('_', ' ').title()


    # Define a dict for the color table, then set the main input color file
    color_table = {}
    color_table_file = 'crayola.dat'
    input_color_table = ('Red', 'Orange', 'Yellow', 'Inchworm', 'Green', 'Sea Green', 'Turquoise Blue', 'Cerulean', 'Navy Blue',  'Purple Heart', 'Pink Flamingo', 'Magenta', 'Beaver', 'Peach', 'Gray')

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
    outfile = common.TAKANORI_DIRECTORY + '.asset'
    outpath = Path.cwd() / datainfo['dir'] / common.TAKANORI_DIRECTORY / outfile
    with open(outpath, 'wt') as asset:

        # Switch stdout to the file
        sys.stdout = asset


        print('-- ' + datainfo['project'] + ' / Primates: Takanori trial files')
        print("-- This file is auto-generated in the " + make_asset.__name__ + "() function inside " + Path(__file__).name)
        print('-- Author: Brian Abbott <abbott@amnh.org>')
        print()


        for file in asset_info:
            #print('local ' + asset_info[file]['speck_var'] + ' = asset.localResource("' + asset_info[file]['asset_rel_path'] + '/' + asset_info[file]['speck_file'] + '")')
            print('local ' + asset_info[file]['speck_var'] + ' = asset.localResource("' + asset_info[file]['speck_file'] + '")')

            #print('local ' + asset_info[file]['label_var'] + ' = asset.localResource("' + asset_info[file]['asset_rel_path'] + '/' + asset_info[file]['label_file'] + '")')


        print('local ' + asset_info[file]['cmap_var'] + ' = asset.localResource("' + asset_info[file]['cmap_file'] + '")')


        print('local texture_file = asset.localResource("point3A.png")')
        print()




        print('-- Set some parameters for OpenSpace settings')
        print('local scale_factor = ' + common.SCALE_FACTOR)
        print('local text_size = ' + common.TEXT_SIZE)
        print('local text_min_size = ' + common.TEXT_MIN_SIZE)
        print('local text_max_size = ' + common.TEXT_MAX_SIZE)
        print()



        for file in asset_info:

            print('local ' + asset_info[file]['os_scenegraph_var'] + ' = {')
            print('    Identifier = "' + asset_info[file]['os_identifier_var'] + '",')
            print('    Renderable = {')
            print('        Type = "RenderableCosmicPoints",')
            print('        Color = { 0.8, 0.8, 0.8 },')
            print('        ColorMap = ' + asset_info[file]['cmap_var'] + ',')
            print('        ColorOption = { "lineage_30_code" },')
            print('        ColorRange = { {30001, 30025} },')
            print('        Opacity = 1.0,')
            print('        ScaleFactor = scale_factor,')
            print('        File = ' + asset_info[file]['speck_var'] + ',')
            print('        DrawLabels = false,')
            print('        Unit = "Km",')
            print('        Texture = texture_file,')
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
    