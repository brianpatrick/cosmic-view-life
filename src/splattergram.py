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


class splattergram:

    def __init__(self):
        pass

    def process_data(self, datainfo):

        common.print_subhead_status('Processing splattergram')

        datainfo['data_group_title'] = datainfo['sub_project'] + ': Splattergram'
        datainfo['data_group_desc'] = 'Splattergram ' + datainfo['sub_project'].lower() + ' data, which includes one data point per species.'

        in_file_path = Path.cwd() / common.DATA_DIRECTORY / datainfo['dir'] / datainfo['csv_file']
        common.test_input_file(in_file_path)

        # Read in the CSV file
        # 'Taxon' header is not present in the CSV, so remove all the headers, and add them manually
        df = pd.read_csv(in_file_path, header=0, names=['taxon', 'x', 'y', 'z'])

        # Rearrange the columns
        df = df[['x', 'y', 'z', 'taxon']]

        # If datainfo has a scale_factor, use it to scale the data. Otherwise, use the default.
        if 'scale_factor' in datainfo:
            scale_factor = datainfo['scale_factor']
        else:
            scale_factor = common.POSITION_SCALE_FACTOR

        # Rescale the position data
        df['x'] = df['x'].multiply(scale_factor)
        df['y'] = df['y'].multiply(scale_factor)
        df['z'] = df['z'].multiply(scale_factor)


        # Print the data in a single CSV file.
        # ---------------------------------------------------------------------------
        out_file_stem = 'splattergram'
        outpath = Path.cwd() / datainfo['dir'] 
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

        return df

    def make_random_points_on_sphere(self, datainfo):
        # This function is not used in this module, but is included here for reference.
        # It generates random points on a sphere.

        import numpy as np

        # Number of points to generate
        n = 207164

        # Generate random points on a sphere
        # https://stackoverflow.com/questions/33976911/generate-a-random-sample-of-points-distributed-on-the-surface-of-a-unit-sphere
        np.random.seed(0)
        pts = np.random.normal(size=(n, 3))
        pts /= np.linalg.norm(pts, axis=1)[:, None]

        # Scale the points
        pts = pts * common.EARTH_RADIUS_IN_KM

        # Change pts to a dataframe.
        df = pd.DataFrame(pts, columns=['x', 'y', 'z'])

        # Add a taxon column that is just the index.
        df['taxon'] = 'taxon' + df.index.astype(str)

        # Print the data in a single CSV file.
        # ---------------------------------------------------------------------------
        out_file_stem = 'random_points_on_sphere'
        outpath = Path.cwd() / datainfo['dir'] 
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

        return df




    def make_asset(self, datainfo):

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
                print('    Parent = "Earth",')
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
