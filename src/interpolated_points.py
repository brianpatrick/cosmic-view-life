'''
Cosmic View of Life on Earth

Interpolated points code.

This code is part of the Cosmic View of Life on Earth project at the American Museum of Natural History.

Interpolated points are data points that move between two locations in 3D space. This
file contains code that translates provided csv files containing the two end locations
(start, finish) and generates the CSV and asset files for use in OpenSpace.

Author: Brian Abbott <abbott@amnh.org>, Hollister Herhold <hherhold@amnh.org>

Created: June 2024
'''

from src import common
import pandas as pd
from pathlib import Path
import sys

class interpolated_points:

    def __init__(self):
        self.interpolated_points_csv_full_path = Path()
        self.num_objects = 0

    def process_interpolated_points(self, datainfo, check_duplicates=True):
        '''
        Process  interpolated points. These are points that move between two locations
        in 3D space.

        This function takes the start and end points, verifies that they are in
        a one-to-one mapping, or creates one if necessary, and generates
        a csv file containing the start points followed by the end points in
        the correct order. The asset file is created in make_asset_interpolated().
        '''

        common.print_subhead_status('Processing interpolated points')

        start_file_path = Path.cwd() / common.DATA_DIRECTORY / datainfo['dir'] / datainfo['start_points']
        end_file_path = Path.cwd() / common.DATA_DIRECTORY / datainfo['dir'] / datainfo['end_points']
        common.test_input_file(start_file_path)
        common.test_input_file(end_file_path)

        # Read in the CSV files. # is the comment character and the first line is the
        # header containing the column names.
        start_points_df = pd.read_csv(start_file_path, comment='#')
        end_points_df = pd.read_csv(end_file_path, comment='#')

        # Some datasets come in already clean with no need to check for duplicates or
        # renaming of columns.
        if check_duplicates:
            # Some CSV files use 'taxon' instead of 'name'. Rename 'taxon' to 'name' if
            # 'name' does not exist.
            if 'name' not in start_points_df.columns:
                start_points_df = start_points_df.rename(columns={'taxon': 'name'})
            if 'name' not in end_points_df.columns:
                end_points_df = end_points_df.rename(columns={'taxon': 'name'})

            # Duplicated points in either dataframe are not allowed. Filter them based on
            # the 'name' column.
            start_points_df = start_points_df.drop_duplicates(subset='name')
            end_points_df = end_points_df.drop_duplicates(subset='name')

            # The list of names in each dataframe must be identical. If they are not, we
            # need to drop the names that are not in both dataframes.
            start_names = start_points_df['name'].tolist()
            end_names = end_points_df['name'].tolist()

            # Find the names that are in one dataframe but not the other
            start_not_end = [name for name in start_names if name not in end_names]
            end_not_start = [name for name in end_names if name not in start_names]

            # Drop the names that are not in both dataframes
            start_points_df = start_points_df[~start_points_df['name'].isin(start_not_end)]
            end_points_df = end_points_df[~end_points_df['name'].isin(end_not_start)]

            # Check that the start and end points have the same number of points
            if len(start_points_df) != len(end_points_df):
                common.print_error('The number of points in the start and end files must be the same.')
                sys.exit(1)

            # Before writing the data to a file, we need to sort the dataframes by the name
            # column. This is because the data may not be in the same order in both dataframes.
            start_points_df = start_points_df.sort_values(by='name')
            end_points_df = end_points_df.sort_values(by='name')

        # Save the number of points for use in making the asset file.
        self.num_objects = len(start_points_df)


        # Finally, we need to make a dataframe that contains the start points followed by
        # the end points. This is the data that will be written to the csv file.
        interpolated_points_df = pd.concat([start_points_df, end_points_df], ignore_index=True)

        # We also need to add a new column at the beginning of the dataframe that contains
        # the time value. This is the value that will be used to interpolate between the
        # start and end points. For this example, start is 0 and end is 1. If a time
        # column already exists, do nothing.
        if 'time' not in interpolated_points_df.columns:
            interpolated_points_df.insert(0, 'time', [0] * len(start_points_df) + [1] * len(end_points_df))

        # If datainfo has a scale_factor, use it to scale the data. Otherwise,
        # do nothing - the default is no scaling.
        if 'scale_factor' in datainfo:
            interpolated_points_df['x'] = interpolated_points_df['x'].multiply(datainfo['scale_factor'])
            interpolated_points_df['y'] = interpolated_points_df['y'].multiply(datainfo['scale_factor'])
            interpolated_points_df['z'] = interpolated_points_df['z'].multiply(datainfo['scale_factor'])

        # Write the data to a csv file, and put it where we're told.
        outfile = datainfo['dir'] + '_interpolated.csv'
        if ('save_path' not in datainfo) or (datainfo['save_path'] == None):
            datainfo['save_path'] = Path.cwd() / datainfo['dir']
        self.interpolated_points_csv_full_path = datainfo['save_path'] / outfile
        interpolated_points_df.to_csv(self.interpolated_points_csv_full_path, index=False)

        print('Interpolated points written to ' + str(self.interpolated_points_csv_full_path))


    def make_asset_interpolated_points(self, datainfo):
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

        # Set the nested dict
        file = self.interpolated_points_csv_full_path.name
        asset_info[file] = {}

        asset_info[file]['csv_file'] = self.interpolated_points_csv_full_path.name
        asset_info[file]['csv_var'] = common.file_variable_generator(asset_info[file]['csv_file'])

        #asset_info[file]['label_file'] = path.name + '.label'
        #asset_info[file]['label_var'] = common.file_variable_generator(asset_info[file]['label_file'])

        #asset_info[file]['cmap_file'] = path.name + '.cmap'
        #asset_info[file]['cmap_var'] = common.file_variable_generator(asset_info[file]['cmap_file'])

        asset_info[file]['asset_rel_path'] = '.'

        asset_info[file]['os_scenegraph_var'] = datainfo['dir'] + '_' + datainfo['tree_dir'] + '_interpolated'
        asset_info[file]['os_identifier_var'] = datainfo['dir'] + '_' + datainfo['tree_dir'] + '_interpolated'

        asset_info[file]['gui_name'] = 'Interpolated Points'
        asset_info[file]['gui_path'] = '/' + datainfo['sub_project'] + '/' + datainfo['tree_dir'].replace('_', ' ').title()

        # Open the file to write to
        outfile = datainfo['dir'] + '_interpolated.asset'
        outpath = Path.cwd() / datainfo['dir'] / datainfo['tree_dir'] / outfile
        with open(outpath, 'wt') as asset_file:

            # Switch stdout to the file
            sys.stdout = asset_file

            print('-- ' + datainfo['project'] + ' / ' + datainfo['data_group_title'])
            print("-- This file is auto-generated in the " + self.make_asset_interpolated_points.__name__ + "() function inside " + Path(__file__).name)
            print('-- Authors: Brian Abbott <abbott@amnh.org>, Hollister Herhold <hherhold@amnh.org>')
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
                print('        NumberOfObjects = ' + str(self.num_objects) + ',')
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

