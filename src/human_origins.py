# Cosmic View of Life on Earth
#
# Author: Brian Abbott <abbott@amnh.org>
# Created: September 2022
"""
Process Homo Sapien DNA data with origin information, assign integer codes to use in OpenSpace, and generate OpenSpace data and asset files.
"""

import re
import sys
import pandas as pd
from pathlib import Path

from src import common


def seq_populations(datainfo):
    """
    Process the human DNA data with origin information.

    :param datainfo: Metadata about the dataset.
    :type datainfo: dict of {str : list}

    
    The Homo Sapien DNA data are accompanied by metadata regarding their origin. These include continent, and also region information. We process these and generate the resulting data files for OpenSpace.


    Continent and Region Codes
    ===============================================================================

    The origin metadata for continents and regions are literal names in the raw data (e.g., 'Europe', 'South-east Asia', etc.). We convert these names into an integer so we can leverage it within OpenSpace. First, we give each data sample a continent code, as follows:

    ========== =====
    Continent  Code
    ========== =====
    Africa       1
    Europe       2
    Asia         3
    America      4
    Oceania      5
    ========== =====

    Next, we assign a regional code within each continent. Each region code begins with the continent code, so all regions of Africa begin with a 1. The region codes are as follows:

    ================= ====
    Region            Code
    ================= ====
    Central Africa     10
    South Africa       11
    West Africa        12
    North Africa       13
    Europe             20
    Western Asia       30
    Northeast Asia     31
    Central Asia       32
    South Asia         33
    East Asia          34
    Southeast Asia     35
    North America      40
    Central America    41
    South America      42
    Oceania            50
    ================= ====

    A key for these codes is exported to the file  ``processed_catalogs/human_origins/region_population_code_key.dat``.



    Output files:
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    :file:`human_origins/human_origins.speck`
        The OpenSpace-ready data file.
    
    :file:`human_origins/human_origins.label`
        The OpenSpace-ready label file.

    :file:`human_origins/continents.cmap`
        The OpenSpace color map file, one color for each continent.
    
    :file:`human_origins/regions/[{region_code}]_[{region_name}].speck`
        Data files for each region in individual speck files.

    :file:`human_origins/regions/regions.cmap`
        A color map file that contains one color for each region.
    """
    
    common.print_subhead_status('Processing ' + datainfo['sub_project'].lower() + ' sequence data')


    datainfo['data_group_title'] = datainfo['sub_project'] + ': Human DNA origins'
    datainfo['data_group_desc'] = 'DNA data for Homo Sapiens plotted by origin information.'


    # Read the sequence file and process into a dataframe
    # ---------------------------------------------------------------------------
    inpath = Path.cwd() / common.DATA_DIRECTORY / datainfo['dir'] / datainfo['catalog_directory'] / datainfo['sequence_file']
    common.test_input_file(inpath)

    df = pd.read_csv(inpath)



    # Get rid of the "East Asia - tentative" region, and just call it "East Asia"
    df.loc[df['region'] == 'East Asia - tentative', 'region'] = 'East Asia'

    # Similarly, rename North-East Asia to Northeast Asia, and for South.
    df.loc[df['region'] == 'North-East Asia', 'region'] = 'Northeast Asia'
    df.loc[df['region'] == 'South-East Asia', 'region'] = 'Southeast Asia'
    

    # Process the regions and assign a integer code to each region and for each continent
    # ---------------------------------------------------------------------------
    # Set up unique list of regions
    region_list = list(df['region'].unique())


    # Set up an integer code for each continient
    # First, set up a generic dictionary to house the continents. This is mainly
    # for the .dat printout we do at the end.
    continent_codes = {'Africa': 1, 'Europe': 2, 'Asia': 3, 'Americas': 4, 'Oceania': 5}


    # To match the continent codes to the main df (sequence) we need to assign a code to each region,
    # which is what this dictionary does.
    regional_continent_codes = {}

    for region in region_list:
        if re.search('Africa', region):
            regional_continent_codes.update({region: 1})
        elif re.search('Europe', region):
            regional_continent_codes.update({region: 2})
        elif re.search('Asia', region):
            regional_continent_codes.update({region: 3})
        elif re.search('America', region):
            regional_continent_codes.update({region: 4})
        elif re.search('Oceania', region):
            regional_continent_codes.update({region: 5})
        else:
            print('Unrecognized continent among region names.')


    # Add the integer value of the continent to a new column in the df
    # by mapping the dictionary defined above to the "region" column in the dataframe.
    df['continent_code'] = df['region'].map(regional_continent_codes)


        

    # Define a dictionary for the regions and their codes format {region: region_code}
    region_codes = {}
    
    # Manually assign the codes. This is sloppy, but we do not want consecutive codes,
    # rather, we want to assign codes that signify each continent, so Africa is 1x, 
    # Europe is 2x, Asia is 3x, and so on.
    for region in region_list:
        if region == 'Central Africa':
            region_codes.update({region: 10})
        elif region == 'South Africa':
            region_codes.update({region: 11})
        elif region == 'West Africa':
            region_codes.update({region: 12})
        elif region == 'North Africa':
            region_codes.update({region: 13})
        elif region == 'Europe':
            region_codes.update({region: 20})
        elif region == 'Western Asia':
            region_codes.update({region: 30})
        elif region == 'Northeast Asia':
            region_codes.update({region: 31})
        elif region == 'Central Asia':
            region_codes.update({region: 32})
        elif region == 'South Asia':
            region_codes.update({region: 33})
        elif region == 'East Asia':
            region_codes.update({region: 34})
        elif region == 'Southeast Asia':
            region_codes.update({region: 35})
        elif region == 'North America':
            region_codes.update({region: 40})
        elif region == 'Central America':
            region_codes.update({region: 41})
        elif region == 'South America':
            region_codes.update({region: 42})
        elif region == 'Oceania':
            region_codes.update({region: 50})
        else:
            print('Unrecognized region name')
    

    # Sort the dict by region code
    region_codes = dict(sorted(region_codes.items(), key = lambda x: x[1]))




    # Add the integer value of the region to a new column in the df
    # by mapping the dictionary defined above to the "region" column in the dataframe.
    df['region_code'] = df['region'].map(region_codes)

    


    # Process the populations and assign a integer code to each
    # ---------------------------------------------------------------------------
    # A dictionary for the pop codes, format {population_name: population_code}
    population_codes = {}

    # Group the dataframe by region code and population
    grp = df.groupby(['region_code', 'population'])

    # Set up a loop to assign the codes to each population name
    # Region codes begin at 10, so we'll enter the loop with that value
    region_code = 10

    # Start our pop_counter to 1
    pop_counter = 1

    # Loop through the group df. Each key is a tuple of region code (key[0]) and pop name (key[1])
    for key, value in grp:

        # If the region code does not equal that of the current iteration, 
        # then reset the pop_counter counter back to 1. This means we're on 
        # a new region and want to start counting our populations from 1 again.
        if region_code != key[0]:
            pop_counter = 1
        

        # Construct the population_code value. This is a combo of the region code and the pop_counter
        population_code = str(key[0]) + f"{pop_counter:02}"

        # Write the values to the populations dictionary
        population_codes.update({key[1]: population_code})

        # Set values for the next iteration
        region_code = key[0]
        pop_counter += 1

    
    # Add the integer value of the population to a new column in the main df
    # by mapping the dictionary defined above to the "population" column.
    df['population_code'] = df['population'].map(population_codes)

    
    # Find the average position in x,y,z
    x_avg = df['x'].mean()
    y_avg = df['y'].mean()
    z_avg = df['z'].mean()


    # Normalize the positions to the average
    df['x'] = df['x'].subtract(x_avg)
    df['y'] = df['y'].subtract(y_avg)
    df['z'] = df['z'].subtract(z_avg)


    # Rescale the position data
    df['x'] = df['x'].multiply(common.HUMAN_POSITION_SCALE_FACTOR)
    df['y'] = df['y'].multiply(common.HUMAN_POSITION_SCALE_FACTOR)
    df['z'] = df['z'].multiply(common.HUMAN_POSITION_SCALE_FACTOR)
    


    # Build a label format for the speck file
    sep = ' | '
    df['speck_name'] = df['seqId'] + sep + df['region'] + sep + df['population']

    # Sort the df by region code, this makes things easier down the line.
    df.sort_values(by=['region_code'])





    # Print the region codes and population codes to a separate file for reference.
    # ---------------------------------------------------------------------------
    # This is the root path for all output files in this script,
    # so only need to set and check it once.
    outpath = Path.cwd() / common.PROCESSED_DATA_DIRECTORY / datainfo['dir']
    common.test_path(outpath)

    outfile_codes_dat = 'region_population_code_key.dat'
    outpath_codes_dat = outpath / outfile_codes_dat

    with open(outpath_codes_dat, 'wt') as dat_codes:

        print('Generated from ' + Path(__file__).name + '.\n', file=dat_codes)

        # Print the continent codes
        print('Continent codes:', file=dat_codes)

        for continent_name, continent_code in continent_codes.items():
            print(f"    {continent_code} = {continent_name}", file=dat_codes)



        # Print the codes info to the file.
        print('\n\nRegion codes:', file=dat_codes)

        # Run thru the region codes dict
        for region_name, region_code in region_codes.items():
            print(f"    {region_code} = {region_name}", file=dat_codes)


        # Print the population codes
        print('\n\nPopulation codes:', file=dat_codes)

        # Run thru the pop codes dict
        for pop_name, pop_code in population_codes.items():
            print(f"    {pop_code} = {pop_name}", file=dat_codes)


    # Report to stdout
    common.out_file_message(outpath_codes_dat)



    # Print all the data to one speck file
    # ---------------------------------------------------------------------------
    # Set up the columns to print to datavars
    cols_to_print = ['continent_code', 'region_code', 'population_code']


    outpath = Path.cwd() / datainfo['dir']
    #print(outpath)
    common.test_path(outpath)

    outfile_speck = datainfo['dir'] + '.speck'
    outpath_speck = outpath / outfile_speck

    with open(outpath_speck, 'wt') as speck:

        header = common.header(datainfo, script_name=Path(__file__).name)
        print(header, file=speck)

        # set a counter for the datavar number, and cycle through the
        # columns to print list and print the datavar lines
        datavar_counter = 0
        for col in cols_to_print:
            print('datavar ' + str(datavar_counter) + ' ' + col, file=speck)
            datavar_counter += 1
        
        # Print the rows to the speck file
        for col, row in df.iterrows():
            print(f"{row['x']:.8f} {row['y']:.8f} {row['z']:.8f} {row['continent_code']} {row['region_code']} {row['population_code']} # {row['speck_name']}", file=speck)

    # Report to stdout
    common.out_file_message(outpath_speck)




    # Print a speck file for each region
    # ---------------------------------------------------------------------------

    # Cycle through the dictionary of regions
    for region_name, region_code in region_codes.items():
        
        # Make a variable/filename-ready version of the region name
        region_name_var = region_name.lower().replace(' ', '_').replace('-', '_')

        outpath = Path.cwd() / datainfo['dir'] / common.REGIONS_DIRECTORY
        common.test_path(outpath)

        outfile_speck = str(region_code) + '_' + region_name_var + '.speck'
        outpath_speck = outpath / outfile_speck

        with open(outpath_speck, 'wt') as speck:

            header = common.header(datainfo, script_name=Path(__file__).name)
            print(header, file=speck)

            # set a counter for the datavar number, and cycle through the
            # columns to print list and print the datavar lines
            datavar_counter = 0
            for col in cols_to_print:
                print('datavar ' + str(datavar_counter) + ' ' + col, file=speck)
                datavar_counter += 1
            
            # Print the rows to the speck file, but only print rows if the region name
            # in the dataframe matches that of the loop we're in.
            ################# HH             row = df.loc[df[lineage_code_col]==code].iloc[0]

            for col, row in df.iterrows():
                if row['region'] == region_name:
                    print(f"{row['x']:.8f} {row['y']:.8f} {row['z']:.8f} {row['continent_code']} {row['region_code']} {row['population_code']} # {row['speck_name']}", file=speck)

        # Report to stdout
        common.out_file_message(outpath_speck)


        
        




    # Build and Print the labels
    # ---------------------------------------------------------------------------

    # First, we must build some labels for a label file. This will be from the 
    # average x,y,z for each region
    # Group by region
    region_grouped = df.groupby('region')

    # Take the mean x,y,z of each region
    mean_x = region_grouped['x'].mean()
    mean_y = region_grouped['y'].mean()
    mean_z = region_grouped['z'].mean()

    # Concatinate each of these series into a df
    mean_positions = pd.concat([mean_x, mean_y, mean_z], axis=1)

    # Rename the columns
    mean_positions.columns = ['mean_x', 'mean_y', 'mean_z']

    # Pull the row index (which is the region) and make it a separate column
    mean_positions.reset_index(inplace=True)


    # Open and print the labels to a file
    outpath = Path.cwd() / datainfo['dir']
    common.test_path(outpath)

    outfile_label = datainfo['dir'] + '.label'  
    outpath_label = outpath / outfile_label

    with open(outpath_label, 'wt') as label:

        header = common.header(datainfo, script_name=Path(__file__).name)
        print(header, file=label)

        # Print the label file
        print('textcolor 1', file=label)

        for col, row in mean_positions.iterrows():
            print(f"{row['mean_x']:.8f} {row['mean_y']:.8f} {row['mean_z']:.8f} text {row['region']}", file=label)

    # Report to stdout
    common.out_file_message(outpath_label)






    # Build and print the color map files.
    # ---------------------------------------------------------------------------
    # First, for the continents (codes 1-5: 5 total)
    
    # Define the color table for this file, one color per continent
    color_table = ('Red-Orange', 'Goldenrod', 'Green', 'Magenta', 'Pacific Blue')

    # get a list of the continent names
    continent_list = list(continent_codes.keys())

    # Specify the color table we want to sample from
    color_table_file = 'crayola.dat'


    outpath = Path.cwd() / datainfo['dir']
    common.test_path(outpath)

    outfile_cmap = 'continents.cmap'
    outpath_cmap = outpath / outfile_cmap

    with open(outpath_cmap, 'wt') as cmap:

        header = common.header(datainfo, script_name=Path(__file__).name)
        print(header, file=cmap)

        # Print the number of colors
        print(len(color_table), file=cmap)
        
        # Print the rows to the cmap file
        for continent_name, color_name in zip(continent_list, color_table):

            # Get the RGB from the color table file given the color name
            rgb = common.find_color(color_table_file, color_name)

            # Print to the file
            print(f"{rgb} 1.0 # {color_name} | {continent_name}", file=cmap)

    # Report to stdout
    common.out_file_message(outpath_cmap)




    # Color map file for the regions (codes 10-50: 15 total)
    #  4 regions for Africa: redish tones
    #  1 regions for Europe: yellow
    #  6 regions for Asia: Greenish hues
    #  3 regions for America: magenta/pink hues
    #  1 regions for Oceania: blue
    
    # Define the color table for this file
    color_table = ('Scarlet', 'Maroon', 'Orange-Red', 'Orange', 'Goldenrod', 'Inchworm',  'Asparagus', 'Green', 'Sea Green', 'Shamrock', 'Tropical Rain Forest', 'Magenta',  'Plum', 'Red-Violet', 'Pacific Blue')

    # get a list of the continent names
    region_list = list(region_codes.keys())

    # Specify the color table we want to sample from
    color_table_file = 'crayola.dat'


    outpath = Path.cwd() / datainfo['dir'] / common.REGIONS_DIRECTORY
    common.test_path(outpath)

    outfile_cmap = 'regions.cmap'
    outpath_cmap = outpath / outfile_cmap

    with open(outpath_cmap, 'wt') as cmap:

        header = common.header(datainfo, script_name=Path(__file__).name)
        print(header, file=cmap)

        # Print the number of colors
        print(len(color_table), file=cmap)
        
        # Print the rows to the cmap file
        for region_name, color_name in zip(region_list, color_table):

            # Get the RGB from the color table file given the color name
            rgb = common.find_color(color_table_file, color_name)

            # Print to the file
            print(f"{rgb} 1.0 # {color_name} | {region_name}", file=cmap)

    # Report to stdout
    common.out_file_message(outpath_cmap)







def make_asset_all(datainfo):
    """
    Generate the asset file for the human origins data.

    :param datainfo: Metadata about the dataset.
    :type datainfo: dict of {str : list}
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
    path = Path.cwd() / datainfo['dir']
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

        asset_info[file]['cmap_file'] = 'continents.cmap'
        asset_info[file]['cmap_var'] = common.file_variable_generator(asset_info[file]['cmap_file'])
        
        asset_info[file]['asset_rel_path'] = '.'

        asset_info[file]['os_scenegraph_var'] = datainfo['dir'] + '_' + 'all'
        asset_info[file]['os_identifier_var'] = datainfo['dir'] + '_' + 'all'

        asset_info[file]['gui_name'] = 'All Continents'
        asset_info[file]['gui_path'] = '/' + datainfo['sub_project']



    # Open the file to write to
    outfile = datainfo['dir'] + '.asset'
    outpath = Path.cwd() / datainfo['dir'] / outfile
    with open(outpath, 'wt') as asset:

        # Switch stdout to the file
        sys.stdout = asset


        print('-- ' + datainfo['project'] + ' / ' + datainfo['data_group_title'])
        print("-- This file is auto-generated in the " + make_asset_all.__name__ + "() function inside " + Path(__file__).name)
        print('-- Author: Brian Abbott <abbott@amnh.org>')
        print()


        for file in asset_info:
            print('local ' + asset_info[file]['speck_var'] + ' = asset.resource("' + asset_info[file]['asset_rel_path'] + '/' + asset_info[file]['speck_file'] + '")')

            print('local ' + asset_info[file]['label_var'] + ' = asset.resource("' + asset_info[file]['asset_rel_path'] + '/' + asset_info[file]['label_file'] + '")')

            print('local ' + asset_info[file]['cmap_var'] + ' = asset.resource("' + asset_info[file]['asset_rel_path'] + '/' + asset_info[file]['cmap_file'] + '")')
        


        print('local texture_file = asset.resource("point3A.png")')
        print()


        print('-- Set some parameters for OpenSpace settings')
        print('local point_scale_factor = ' + common.HUMAN_POINT_SCALE_FACTOR)
        print('local point_scale_exponent = ' + common.HUMAN_POINT_SCALE_EXPONENT)
        print('local text_size = ' + common.TEXT_SIZE)
        print('local text_min_size = ' + common.TEXT_MIN_SIZE)
        print('local text_max_size = ' + common.TEXT_MAX_SIZE)
        print()



        for file in asset_info:

            print('local ' + asset_info[file]['os_scenegraph_var'] + ' = {')
            print('    Identifier = "' + asset_info[file]['os_identifier_var'] + '",')
            print('    Renderable = {')
            print('        Type = "RenderablePointCloud",')
            print('        Coloring = {')
            print('            ColorMapping = {')
            print('                File = asset.resource(' + asset_info[file]['cmap_var'] + '),'),
            print('                ParameterOptions = {')
            print('                    { Key = "continent_code", Range = { 1, 5 } },')
            print('                }')
            print('            },')
            #print('                ColorOption = { "continent_code" },')
            #print('                ColorRange = { {1,5} },')
            print('        },')
            #print('        Type = "RenderableCosmicPoints",')
            #print('        Color = { 0.8, 0.8, 0.8 },')
            
            print('        Opacity = 1.0,')
            print('        SizeSettings = { ScaleFactor = point_scale_factor, ScaleExponent = point_scale_exponent },')
            print('        File = ' + asset_info[file]['speck_var'] + ',')
            print('        DrawLabels = false,')
            print('        LabelFile = ' + asset_info[file]['label_var'] + ',')
            print('        TextColor = { 1.0, 1.0, 1.0 },')
            print('        TextSize = text_size,')
            print('        TextMinMaxSize = { text_min_size, text_max_size },')
            print('        --FadeLabelDistances = { 0.0, 0.5 },')
            print('        --FadeLabelWidths = { 0.001, 0.5 },')
            print('        Unit = "Km",')
            print('        Texture = { File = texture_file },')
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
    





def make_asset_regions(datainfo):
    """
    Generate the asset file for the human origin regions data.

    The resulting asset file has an object for each region, so they may be manipulated independently in OpenSpace. There's some logic here to align the color map file with the regions, which involves a lot of pre-processing of the filenames,
    region names, colors, etc.

    :param datainfo: Metadata about the dataset.
    :type datainfo: dict of {str : list}
    """

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
    path = Path.cwd() / datainfo['dir'] / common.REGIONS_DIRECTORY
    files = sorted(path.glob('*.speck'))


    for path in files:
        
        file = path.name

        # Set the nested dict
        asset_info[file] = {}

        asset_info[file]['speck_file'] = path.name
        asset_info[file]['speck_var'] = common.file_variable_generator(asset_info[file]['speck_file'])

        # asset_info[file]['label_file'] = path.stem + '.label'
        # asset_info[file]['label_var'] = common.file_variable_generator(asset_info[file]['label_file'])

        asset_info[file]['cmap_file'] = 'regions.cmap'
        asset_info[file]['cmap_var'] = common.file_variable_generator(asset_info[file]['cmap_file'])
        
        asset_info[file]['asset_rel_path'] = common.REGIONS_DIRECTORY

        asset_info[file]['os_scenegraph_var'] = datainfo['dir'] + '_' + common.REGIONS_DIRECTORY + '_' + path.stem
        asset_info[file]['os_identifier_var'] = datainfo['dir'] + '_' + common.REGIONS_DIRECTORY + '_' + path.stem

        asset_info[file]['gui_name'] = path.stem.replace('_', ' ').title()
        asset_info[file]['gui_path'] = '/' + datainfo['sub_project'] + '/' + common.REGIONS_DIRECTORY.title()






    # Color map for the regions (codes 10-50: 15 total)
    #  4 regions for Africa: redish tones
    #  1 regions for Europe: yellow
    #  6 regions for Asia: Greenish hues
    #  3 regions for America: magenta/pink hues
    #  1 regions for Oceania: blue
    # Define a dict for the color table, then set the main input color file
    color_table = {}
    color_table_file = 'crayola.dat'
    input_color_table = ('Scarlet', 'Maroon', 'Orange-Red', 'Orange', 'Goldenrod', 'Inchworm',  'Asparagus', 'Green', 'Sea Green', 'Shamrock', 'Tropical Rain Forest', 'Magenta',  'Plum', 'Red-Violet', 'Pacific Blue')

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
        sys.exit(f"{make_asset_regions.__name__}() function inside {Path(__file__).name}:\nNot enough colors for all the files. Add colors to the input_color_table.\nQuitting...")





    # Open the file to write to
    outfile = datainfo['dir'] + '_regions.asset'
    outpath = Path.cwd() / datainfo['dir'] / outfile
    with open(outpath, 'wt') as out_asset:

        # Switch stdout to the file
        sys.stdout = out_asset



        print('-- ' + datainfo['project'] + ' / ' + datainfo['data_group_title'])
        print("-- This file is auto-generated in the " + make_asset_regions.__name__ + "() function inside " + Path(__file__).name)
        print('-- Author: Brian Abbott <abbott@amnh.org>')
        print()


        print('-- Set file paths')
        for file in asset_info:
            print('local ' + asset_info[file]['speck_var'] + ' = asset.resource("' + asset_info[file]['asset_rel_path'] + '/' + asset_info[file]['speck_file'] + '")')


        print('local ' + asset_info[file]['cmap_var'] + ' = asset.resource("' + asset_info[file]['asset_rel_path'] + '/' + asset_info[file]['cmap_file'] + '")')
        print()
        print('local texture_file = asset.resource("point3A.png")')
        print()


        print('-- Set some parameters for OpenSpace settings')
        print('local point_scale_factor = ' + common.HUMAN_POINT_SCALE_FACTOR)
        print('local point_scale_exponent = ' + common.HUMAN_POINT_SCALE_EXPONENT)        
        print('local text_size = ' + common.TEXT_SIZE)
        print('local text_min_size = ' + common.TEXT_MIN_SIZE)
        print('local text_max_size = ' + common.TEXT_MAX_SIZE)
        print()


        for file in asset_info:

            print('local ' + asset_info[file]['os_scenegraph_var'] + ' = {')
            print('    Identifier = "' + asset_info[file]['os_identifier_var'] + '",')
            print('    Renderable = {')
            print('        Type = "RenderablePointCloud",')
            print('         Coloring = {')
            print('            FixedColor = { ' + asset_info[file]['rgb'] + ' },\t-- ' + asset_info[file]['color_name'])
            print('        },')
            #print('        Type = "RenderableCosmicPoints",')
            #print('        Color = { ' + asset_info[file]['rgb'] + ' },\t-- ' + asset_info[file]['color_name'])
            print('        Opacity = 1.0,')
            print('        SizeSettings = { ScaleFactor = point_scale_factor, ScaleExponent = point_scale_exponent },')
            print('        File = ' + asset_info[file]['speck_var'] + ',')
            print('        DrawLabels = false,')
            print('        Unit = "Km",')
            print('        Texture = { File = texture_file },')
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
