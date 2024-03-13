# Cosmic View of Life on Earth

# Author: Brian Abbott <abbott@amnh.org>
# Created: September 2022
"""
The ``sequence_lineage`` module takes the sequence dataframe and outputs one label file for each of the lineage columns chosen (as determined by ``datainfo['lineage_columns']``), and one color map file for each lineage column.
"""

import sys
import re
import pandas as pd
from pathlib import Path

from src import common


def process_data(datainfo, consensus, sequence):
    """
    Process the DNA sequence lineage data.

    :param datainfo: Metadata about the dataset.
    :type datainfo: dict of {str : list}
    :param consensus: The consensus species data, used here to mine their coordinates and labels.
    :type consensus: DataFrame
    :param sequence: The sequence data table.
    :type sequence: DataFrame

    Process the sequence data labels and colors. We combine the sequence data and the consensus data
    (which has the common labels) to output one label file for each lineage column within the :file:`sequence.speck` file. The resulting files are generated using utility functions listed below.

    That range usually begins at the "Class" level (Aves, Primates, etc.) which is the last column 
    that all data points share--their common ancestor.
    """

    common.print_subhead_status('Processing DNA sequence lineage data')


    # Print the label files
    # ---------------------------------------------------------------------------
    # Build the label files for each lineage column.
    # For this, we need the coordinates of the consensus species for each line in the main df.
    # Merge the seq and consensus dataframes. We match on taxon, so many rows with the same taxon will 
    # have different x,y,z positions, but will have the same consensus x,y,z.
    lineage_labels = pd.merge(sequence, consensus, on='taxon', how='left').drop('dummy', axis=1)

    # Rename some of the columns
    lineage_labels = lineage_labels.rename(columns = {'x_x':'x', 'y_x':'y', 'z_x':'z', 'x_y':'x_consensus', 'y_y':'y_consensus', 'z_y':'z_consensus', 'speck_name_y':'speck_name'})

    # Remove the speck_name columns
    lineage_labels.drop(['speck_name_x'], axis='columns', inplace=True)

    # Make a list of the df column names
    colnames = list(lineage_labels)

    # Step through the column names and pick out the "lineage_NN" columns to pass to the function
    for col_name in colnames:

        # If we match a column that starts with 'lineage_' and ends with a number
        #if match(r'^(lineage_).*([0-9])$', col_name):
        if re.match(r'^(lineage_)([0-9]+)$', col_name):
            
            # Collect the digits from the col_name so we have an integer
            num = int(re.search(r'\d+', col_name).group())
            
            # Start making lineage label files and lineage color map files
            # for the class lineage column, defined in main()
            if num >= int(datainfo['lineage_columns'][0]):
                print_lineage_label_file(datainfo, col_name, lineage_labels)
                print_lineage_cmap_file(datainfo, col_name, lineage_labels)






def print_lineage_label_file(datainfo, column, df):
    """
    Print the label file for select lineage column.

    :param datainfo: Metadata about the dataset.
    :type datainfo: dict of {str : list}
    :param column: The name of a lineage column. 
    :type column: str
    :param df: A table of unique lineage labels (str) and codes (int).
    :type df: DataFrame

    Function prints a label file for a lineage column from the data. Delivers one label file given the column name and dataframe where that column is located.

    Output files:
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    :file:`primates/{version}/sequences/lineage_{lineage_column_number}.label`
        The OpenSpace-ready file for the labels for each lineage column.
    """

    # Set the data file metadata for the headers
    datainfo['data_group_title'] = datainfo['sub_project'] + ': Lineage labels'
    datainfo['data_group_desc'] = 'Lineage labels for the ' + datainfo['sub_project'].lower() + ' DNA data for column ' + column


    # Open the label file for writing
    outpath = Path.cwd() / datainfo['dir'] / datainfo['catalog_directory'] / common.SEQUENCE_DIRECTORY
    common.test_path(outpath)

    outfile = column + '.label'
    outpath = outpath / outfile

    with open(outpath, 'wt') as label:

        header = common.header(datainfo, function_name=print_lineage_label_file.__name__, script_name=Path(__file__).name)
        print(header, file=label)

        # Print the text color command
        print('textcolor 1', file=label)

        # Get a list of unique lineage codes for the lineage number.
        # Do not include 0 (zero) values in the list.
        lineage_code_col = column + '_code'
        unique_lineage_codes = list(df.loc[df[lineage_code_col] != '0', lineage_code_col].unique())

        # Sort the lineage codes
        unique_lineage_codes.sort()
        
        # Cycle through the unique list of lineage codes
        for code in unique_lineage_codes:

            # for each unique code, cycle thru the mashed up df to pluck out the consensus x,y,z and labels.
            # Break once we've found the matching consensus position corresponding to the lineage value.
            for _, row in df.iterrows():
                if row[lineage_code_col] == code:
                    print(f"{row['x_consensus']:.8f} {row['y_consensus']:.8f} {row['z_consensus']:.8f} text {row[column]} # {row[lineage_code_col]}", file=label)
                    break

    # Report to stdout
    common.out_file_message(outpath)





def print_lineage_cmap_file(datainfo, column, df):
    """
    Function prints a color map file for a given lineage column in the data.

    :param datainfo: Metadata about the dataset.
    :type datainfo: dict of {str : list}
    :param column: The name of a lineage column. 
    :type column: str
    :param df: A table of unique lineage labels (str) and codes (int).
    :type df: DataFrame

    Output files:
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    :file:`primates/{version}/sequences/lineage_{lineage_column_number}.cmap`
        The OpenSpace-ready file for the color map for each lineage column/level. Each file has as many colors as there are unique lineage codes.
    """

    # Set the data file metadata for the headers
    datainfo['data_group_title'] = datainfo['sub_project'] + ': Color map for ' + column + ' codes'
    datainfo['data_group_desc'] = 'Color map for the ' + datainfo['sub_project'].lower() + ' DNA data for column ' + column


    # Read in the chosen color table
    inpath = Path.cwd() / common.PROCESSED_DATA_DIRECTORY / common.COLOR_DIRECTORY / 'crayola' / 'chosen_colors.dat'
    common.test_input_file(inpath)

    with open(inpath, 'rt') as color_table:
        colorlist =  [line.rstrip() for line in color_table]
        num_colors = len(colorlist)



    # Open the cmap file to write to
    outpath = Path.cwd() / datainfo['dir'] / datainfo['catalog_directory'] / common.SEQUENCE_DIRECTORY
    common.test_path(outpath)

    outfile = column + '.cmap'
    outpath = outpath / outfile

    with open(outpath, 'wt') as cmap:

        header = common.header(datainfo, function_name=print_lineage_cmap_file.__name__, script_name=Path(__file__).name)
        print(header, file=cmap)


        # Get a list of unique lineage codes for the lineage number.
        # Do not include 0 (zero) values in the list.
        lineage_code_col = column + '_code'
        #unique_lineage_codes = list(df.loc[df[lineage_code_col] != '0', lineage_code_col].unique())
        unique_lineage_codes = list(df[lineage_code_col].unique())

        # Text for a zero in the list of unique lineage values
        # A zero represents no value for that lineage column
        # We nedd to remove these, but we also want to know when there is a zero for that column
        # so that we can print the zero color (gray) to the color map file.
        zero_flag = 0
        for code in unique_lineage_codes:
            if code == '0':
                zero_flag = 1


        # Remove the zero from the list of unique values
        unique_lineage_codes = [i for i in unique_lineage_codes if i != '0']

        # Sort the lineage codes
        unique_lineage_codes.sort()


        # Get the number of unique lineage codes per column to print the number of colors in the cmap file
        if zero_flag == 1:
            num_unique_codes = len(unique_lineage_codes) + 1
        else:
            num_unique_codes = len(unique_lineage_codes)
        
        # Print the integer number of colors in the color map file
        print(num_unique_codes, file=cmap)

        # Print the initial "out of bounds" color
        #print("1.0 1.0 1.0 1.0 # White (out-of-bounds)", file=cmap)

        # Set the gray color for the zero-valued lineage points
        gray_color = ((str(common.GRAY_COLOR) + ' ') * 3) +  '1.0 # Gray | Used for zero value lineage codes'
        print(gray_color, file=cmap)

        # If we have a zero in the lineage codes, print the gray color to represent them
        if zero_flag == 1:
            print(gray_color, file=cmap)


        # This index allows for the reset of the color table number, and to cycle through them
        # rather than map out the colors over an excess of unique lineage values. So, 
        # we have the same number of colors as we do unique lineage values, even though
        # we will repeat colors if the number of values exceed the number of colors.
        list_color_index = 0


        # Cycle through the unique list of lineage codes
        for code in unique_lineage_codes:
            
            # Print the list_color_index row of the colorlist
            print(colorlist[list_color_index], file=cmap, end='')

            # Increase the index value
            list_color_index += 1

            # If the index equals the number of colors, then we need to reset
            # back to the beginning of the colorlist
            if list_color_index == num_colors:
                list_color_index = 0


            # For each code in the lineage codes, cycle through the main df to pull out
            # the lineage code and lineage code's name to tack on the end of the color line
            for _, row in df.iterrows():
                if row[lineage_code_col] == code:
                    print(f" | {row[column]} | {row[lineage_code_col]}", file=cmap)
                    break


    # Report to stdout
    common.out_file_message(outpath)





def make_asset(datainfo):
    """
    Print the lineage asset file. 
    
    :param datainfo: Metadata about the dataset.
    :type datainfo: dict of {str : list}
    
    This function prints a series of OpenSpace data objects within one asset file, one object for each lineage column.

    Output files:
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    :file:`primates/{version}/sequence_lineage.asset`
        The OpenSpace asset file for the lineage levels, one data object per lineage level.
    """

    datainfo['data_group_title'] = datainfo['sub_project'] + ': Labels and color maps for the lineage metadata'
    # datainfo['data_group_desc'] = 'Color map for the ' + datainfo['sub_project'].lower() + ' DNA data for column ' + column



    # Open the lineage CSV file to read the lineage column number and 
    # number of unque lineage values for that column.
    infile = 'lineage.csv'
    inpath = Path.cwd() / common.PROCESSED_DATA_DIRECTORY / datainfo['dir'] / datainfo['catalog_directory'] / infile

    # The CSV data are in the x,x,x | x,x,x,...
    # First, split on | and save as two columns.
    lineage_init = pd.read_csv(inpath, header=None, sep='|')
    lineage_init.columns = ['data', 'names']

    # Next, split the data column by comma and save the column number and unique values columns
    lineage = lineage_init['data'].str.split(',', expand=True)
    lineage.columns = ['col_name', 'col_num', 'num_lineage_values']
    lineage.drop('col_name', axis=1, inplace=True)
    
    # We want to drop the rows we aren't using, leaving only the lineage column data we want.
    # Use the datainfo[lineage_columns] lower limit to set the row we shoudl start, but subtract
    # one because the row numbers begin at 0 while the lineage column integers begin at 1.
    for row in lineage.index:
        if row < datainfo['lineage_columns'][0] - 1:
            lineage.drop(row, inplace=True)


    
    # Cycle through the lineage df so that we can get the beginning and end lineage codes
    # for the number of unique lineage values. This is all so we can set the right color map
    # parameters in the ColorRange variable.
    col_int = []
    low_color = []
    high_color = []
    for _, row in lineage.iterrows():
            
        # We need number to match the codes, which are in the form 27001, etc.
        # So, first append the string to make the base.
        col_int.append(row['col_num'])
        color_range_base = str(row['col_num']) + '000'

        # Next, set the low range, which is always 1, so just add 1 to 27000
        low_color_range = int(color_range_base) + 1
        low_color.append(low_color_range)

        # For the upper range, it will be the number of unique values, so 27040,
        # for 40 unique values. So, simply add the number of unique values to the base.
        high_color_range = int(color_range_base) + int(row['num_lineage_values'])
        high_color.append(high_color_range)




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
    path = Path.cwd() / datainfo['dir'] / datainfo['catalog_directory'] / common.SEQUENCE_DIRECTORY
    files = sorted(path.glob('*.label'))


    for path, lineage_col_num, low_color_index, high_color_index in zip(files, col_int, low_color, high_color):
        
        file = path.name

        # Set the nested dict
        asset_info[file] = {}

        asset_info[file]['speck_file'] = 'sequences.speck'
        asset_info[file]['speck_var'] = common.file_variable_generator(asset_info[file]['speck_file'])

        asset_info[file]['label_file'] = path.name
        asset_info[file]['label_var'] = common.file_variable_generator(asset_info[file]['label_file'])

        asset_info[file]['cmap_file'] = path.stem + '.cmap'
        asset_info[file]['cmap_var'] = common.file_variable_generator(asset_info[file]['cmap_file'])
        
        asset_info[file]['asset_rel_path'] = common.SEQUENCE_DIRECTORY

        asset_info[file]['os_scenegraph_var'] = datainfo['dir'] + '_' + datainfo['catalog_directory'] + '_' + path.stem
        asset_info[file]['os_identifier_var'] = datainfo['dir'] + '_' + datainfo['catalog_directory'] + '_' + path.stem

        asset_info[file]['gui_name'] = path.stem.replace('_', ' ').title()
        asset_info[file]['gui_path'] = '/' + datainfo['sub_project'] + '/' + datainfo['catalog_directory'] + '/' + common.SEQUENCE_DIRECTORY.title()

        asset_info[file]['color_column'] = 'lineage_' + lineage_col_num + '_code'
        asset_info[file]['color_range'] = str(low_color_index) + ', ' + str(high_color_index)




    # Open the asset file to write to
    outfile = 'sequence_lineage.asset'
    outpath = Path.cwd() / datainfo['dir'] / datainfo['catalog_directory'] / outfile
    with open(outpath, 'wt') as out_asset:

        # Switch stdout to the file
        sys.stdout = out_asset


        print('-- ' + datainfo['project'] + ' / ' + datainfo['data_group_title'])
        print("-- This file is auto-generated in the " + make_asset.__name__ + "() function inside " + Path(__file__).name)
        print('-- Author: Brian Abbott <abbott@amnh.org>')
        print()


        print('local ' + asset_info[file]['speck_var'] + ' = asset.localResource("' + asset_info[file]['asset_rel_path'] + '/' + asset_info[file]['speck_file'] + '")')


        for file in asset_info:
            print('local ' + asset_info[file]['label_var'] + ' = asset.localResource("' + asset_info[file]['asset_rel_path'] + '/' + asset_info[file]['label_file'] + '")')

            print('local ' + asset_info[file]['cmap_var'] + ' = asset.localResource("' + asset_info[file]['asset_rel_path'] + '/' + asset_info[file]['cmap_file'] + '")')

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
            print('        ColorOption = { "' + asset_info[file]['color_column'] + '" },')
            print('        ColorRange = { { ' + asset_info[file]['color_range'] + ' } },')
            print('        Opacity = 1.0,')
            print('        ScaleFactor = scale_factor,')
            print('        File = ' + asset_info[file]['speck_var'] + ',')
            print('        DrawLabels = false,')
            print('        LabelFile = ' + asset_info[file]['label_var'] + ',')
            print('        TextColor = { 1.0, 1.0, 1.0 },')
            print('        TextSize = text_size,')
            print('        TextMinMaxSize = { text_min_size, text_max_size },')
            print('        --FadeLabelDistances = { 0.0, 0.5 },')
            print('        --FadeLabelWidths = { 0.001, 0.5 },')
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



    # Switch the stdout back to normal stdout (screen)
    sys.stdout = original_stdout

    # Report to stdout
    common.out_file_message(outpath)
    print()