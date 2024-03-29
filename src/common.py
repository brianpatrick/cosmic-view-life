# Cosmic View of Life on Earth
#
# Author: Brian Abbott <abbott@amnh.org>
# Created: September 2022
"""
A module with constants and utility functions. Most of these functions deal with file I/O and parsing data. Some check for the existence of paths, and others print messages to stdout. Any function that will be used by many modules will be in the ``common`` module.
"""

import re
import csv
import sys
import math
import pandas as pd
from pathlib import Path
#import str



# Constants
# =============================================================================
DATA_DIRECTORY = 'catalogs_raw'                     # Universal directory for catalog (raw data) files
PROCESSED_DATA_DIRECTORY = 'catalogs_processed'     # Processed data files (interim csv, dat, or txt files)
VOCAB_DIRECTORY = 'vocabulary'                      # The vocabulary (common name to taxon) catalog

REGIONS_DIRECTORY = 'regions'                       # Human origins regions speck files

LOG_DIRECTORY = 'logs'                              # Directory for log files

CONSENSUS_DIRECTORY = 'consensus_species'       # Directory for the consensus species data/assets
SEQUENCE_DIRECTORY = 'sequences'
#LINEAGE_DIRECTORY = 'lineage'           # Directory for lineage files
BRANCHES_DIRECTORY = 'lineage_branch'         # Directory for lineage branches files
CLADE_DIRECTORY = 'clades'              # directory for the clade-isolated files
TAXON_DIRECTORY = 'taxon'               # Directory for taxon/species data files
TAKANORI_DIRECTORY = 'takanori_trials'
TREE_DIRECTORY = 'tree'
MORPH_DIRECTORY = 'morph'

COLOR_DIRECTORY = 'color_tables'        # Directory for color tables and data



# =============================================================================
# OpenSpace settings
# scale factor and scale exponent deserve some explanation. These are
# parameters *of* the renderable (as of this writing, RenderablePointCloud, though it
# used to be RenderableCosmicPoints) and are used to scale the physical size of the 
# object, NOT its position in space. Scaling of the location in space is applied
# *to* the renderable as a scale transform.
# This used to be SCALE_FACTOR = '105.0' and HUMAN_SCALE_FACTOR = '95.0'
POINT_SCALE_FACTOR = '1.25'
POINT_SCALE_EXPONENT = '4.0'
HUMAN_POINT_SCALE_FACTOR = '1.25'
HUMAN_POINT_SCALE_EXPONENT = '4.0'

TEXT_SIZE = '2.75'
TEXT_MIN_SIZE = '15'
TEXT_MAX_SIZE = '30'




# This is the factor by which I multiply the x,y,z positions from the raw data files before writing them to the speck files.
# Basically, the positions from Wandrille's data are unit vectors, and they need to be more on the order of 0 to 5 million
# (meters) to be visible in OpenSpace. This factor is applied to the x,y,z positions in the data files before they are written
# to the speck files. This is a global factor that is applied to all data files (except the human origins data, which is scaled
# differently). This 5 million (or so) is basically gleaned from the examples dataset, specifically points.asset in
# the point cloud examples.
#POSITION_SCALE_FACTOR = 5000.0
POSITION_SCALE_FACTOR = 10000000.0
HUMAN_POSITION_SCALE_FACTOR = 100000.0

# These are applied to the primate tree of life branches and points
TRANSFORM_TREE_Z = 133.5        # This moves the points and lines down in the z coord
SCALE_TREE_Z = 75.0             # This scales the z coordinate for the lines to expand it and give it depth.

# The gray color (0-1) which we color the zero lineage points
GRAY_COLOR = 0.4


# Color tables
CHOSEN_COLOR_TABLE = ('Lemon Yellow', 'Sea Green', 'Periwinkle', 'Wisteria', 'Carnation Pink', 'Sepia', 'Blue-Gray', 'Orange', 'Fern', 'Blue-Green', 'Violet-Blue', 'Orchid', 'Mahogany', 'Shadow', 'Maize', 'Asparagus', 'Sky Blue', 'Purple Heart', 'Magenta', 'Burnt Sienna', 'Silver', 'Scarlet', 'Yellow-Green', 'Aquamarine', 'Indigo', 'Fuchsia', 'Salmon', 'Peach')


# Output formatting
PADDING = '  '

# Paths
# =============================================================================
# Use this path for all codes in ./src. This is the base path of the project directory.
#local_path = Path.cwd()
#BASE_DIR = str(local_path).removesuffix('/src')
#BASE_PATH = Path(BASE_DIR)
#BASE_PATH = Path.cwd()
#BASE_DIR = Path.cwd()



# Functions
# =============================================================================



# ---------------------------------------------------------------------------
def out_file_message(path):
    """
    Print message to stdout upon file creation.

    :param path: Path of the new file that was written.
    :type path: pathlib.PosixPath
    """
    # Get a relative path from the project root directory
    relative_filepath = path.relative_to(Path.cwd())

    # Get the file extension to determine the file type
    file_extension = Path(path).suffix

    if file_extension == '.asset':
        filetype = 'Asset'
    elif file_extension == '.speck':
        filetype = 'Data'
    elif file_extension == '.label':
        filetype = 'Label'
    elif file_extension == '.cmap':
        filetype = 'Color Map'
    elif file_extension == '.log':
        filetype = 'Log'
    elif file_extension == '.csv' or file_extension == '.dat':
        filetype = 'processed data'
    
    
    # Print the message to stdout
    print('{0} {1}'.format((PADDING + '  Generated ' + filetype + ' file' + ' ').ljust(40, '.'), relative_filepath))





# ---------------------------------------------------------------------------
def print_head_status(message):
    """
    Message to stdout for status, a function for section heads.

    Heads are section-level notices, e.g., for the primates, or the birds.

    :param message: A message to report to stdout
    :type message: str
    """    
    print()
    print('Processing ' + message + '...')
    print('=' * 80)
    


# ---------------------------------------------------------------------------
def print_subhead_status(message):
    """
    Message to stdout for status in subsections.

    Subsections are codes within a section, like the primate consensus species, or the sequence data.

    :param message: A message to report to stdout
    :type message: str
    """    
    print()
    print(PADDING + message + ':')

    # Print an underline that's the length of the message, plus one for the colon.
    message_length = len(message)
    print(PADDING + '-' * (message_length + 1))






# ---------------------------------------------------------------------------
def header(datainfo, function_name='', script_name=''):
    """
    Write header lines to an output file.

    :param datainfo: Metadata about the dataset.
    :type datainfo: dict of {str : list}
    :param function_name: The name of the function that generated the file, defaults to ''
    :type function_name: str, optional
    :param script_name: AName of the script (.py filename) that generated the file, defaults to ''
    :type script_name: str, optional
    """

    institution = '''# Cosmic View of Life on Earth
# American Museum of Natural History
# https://www.haydenplanetarium.org/
# 
# Use of these data is subject to the terms of the License.
'''


    if function_name and script_name:
        generated_by = '#\n# This file is auto-generated by the ' + function_name + '() function inside ' + script_name + '.\n#\n'

    elif not function_name and script_name:
        generated_by = '#\n# This file is auto-generated by ' + script_name + '.\n#\n'

    else:
        generated_by = '#\n'


    data_title = '# ' + datainfo['data_group_title'] + ' version ' + datainfo['version'] + '\n'
    reference = '# Reference: ' + datainfo['reference'] + '\n'
    authors = '# By: ' + datainfo['author'] + '\n'
    data_description = '#\n# ' + datainfo['data_group_desc'] + '\n#\n#'


    header_lines = institution + generated_by + data_title + reference + authors + data_description
    
    return header_lines





# -----------------------------------------------------------------------------
def read_color_table(color_table_file):
    """
    Read in the chosen color table, return as a dict.

    :param color_table_file: Filename of a color table file (.dat).
    :type color_table_file: str
    :return: A dictionary of color values and names.
    :rtype: dict
    """    

    # Open the chosen colors table
    color_table_path = Path.cwd() / PROCESSED_DATA_DIRECTORY / COLOR_DIRECTORY / 'crayola' / color_table_file
    with open(color_table_path, 'rt') as color_file:

        # Read the lines in the color table
        lines = color_file.readlines()

        # Set a dictionary to store the color table with {Name:rgb} format
        color_table = {}

        # Loop through the lines of the color table
        for line in lines:

            # Strip off the end new lines
            line.rstrip()

            # Split the line by #, making the data and name fields
            line_fields_init = line.split(' # ')
            data = line_fields_init[0]
            name = line_fields_init[1].rstrip()
            
            # Strip off the alpha value--we don't need that for OpenSpace color values
            rgb = data.rstrip(' 1.000000')

            # Save the rgb string to the "nameth" color in the color table
            color_table[name] = rgb

            # Split the data field by spaces to pluck the R, G, B, A values
            # line_fields = data.split(' ')
            # r = line_fields[0]
            # g = line_fields[1]
            # b = line_fields[2]
            # a = line_fields[3]
            
            # Save the info in our color_table dict
            #color_table[name] = {'rgb': rgb}


    return color_table





# -----------------------------------------------------------------------------
def find_color(color_table_file, color_name):
    """
    Color lookup.

    Given a color name, mine the main color table for its RGB values.

    :param color_table_file: Filename of a color table file (.dat).
    :type color_table_file: str
    :param color_name: A color name, e.g. 'blue'.
    :type color_name: str
    :return: A character string of R,G,B color values.
    :rtype: str
    """
 
    # Read in the main color table
    color_table = read_color_table(color_table_file)

    # Cycle through the main color_table to pluck the RGB values
    # for the color_name passed to the function.
    for name, rgb in color_table.items():

        # When the color names match, return the rgb string
        if(name == color_name):
            break
    
    return rgb






# -----------------------------------------------------------------------------
def color2dict(source_color_file, input_color_list):
    """
    This function returns colors that are ready to be used in OpenSpace's ``Color`` command.

    Given a color file to mine colors from, and a list of colors to return,
    return a dict with the {color_name: rgb_string} that's useful for 
    OpenSpace's ``Color`` command in an asset file.

    :param source_color_file: filename for a color table (.dat)
    :type source_color_file: str
    :param input_color_list: _description_
    :type input_color_list: tuple
    :return: Return a dictionary of ``color_name: rgb_string``
    :rtype: dict
    """

    final_color_table = {}

    # Read in the main color table
    color_table = read_color_table(source_color_file)

    # Cycle through the given color table file to pluck the RGB values
    # for the color_name passed to the function.
    for color in input_color_list:

        for name, rgb in color_table.items():

            if(name == color):
                rgb = rgb.replace(' ', ', ')
                final_color_table[name] = rgb

    return final_color_table





# -----------------------------------------------------------------------------
def parse_color_file(color_file_path, total_colors):
    """
    Read a cmap file and return a dataframe of colors.

    :param color_file_path: Filename for a color table (.dat)
    :type color_file_path: str
    :param total_colors: A DataFrame with columns 'color_index', 'rgb', and 'color_name'.
    :type total_colors: pathlib.PosixPath
    """    

    #color_map_file = color_file
    #color_file_path = Path.cwd() / PROCESSED_DATA_DIRECTORY / COLOR_DIRECTORY / color_map_file
    test_path(color_file_path)

    with open(color_file_path, 'rt') as color_file:

        # Read the lines in the color map file
        color_list = [line.strip() for line in color_file]

        # Set the color list to only include lines that begin n.n, like 0.7
        # This will exclude the commented header lines, and the total number of colors, which is an int
        color_list = [line for line in color_list if re.match('[0-9].[0-9]', line)]



    # Process the lines to parse the fields
    color_values = []
    color_names = []
    for color_line in color_list:

        # Split the line on the # so we have the rgba field and the names field
        color_line_parts = color_line.split(' # ')

        # Process the RGB field
        color_rgb = color_line_parts[0]

        # Remove the alpha value of 1.0, we don't need that
        remove_str = ' 1.000000'
        if color_rgb.endswith(remove_str):
            rgb = color_rgb[:-(len(remove_str))]

        # Separate the values with commas
        #rgb = rgb.replace(' ', ', ')


        color_values.append(rgb)
        color_names.append(color_line_parts[1])

    # expand to at least the total_colors size
    sized_color_values = color_values * math.ceil(total_colors / len(color_values))

    # trim off the modulus
    sized_color_values = sized_color_values[:total_colors]

    sized_color_names = color_names * math.ceil(total_colors / len(color_names))
    sized_color_names = sized_color_names[:total_colors]

    sized_color_index = []
    for i, value in enumerate(sized_color_names, start=1):
        sized_color_index.append(i)
    
    
    df = pd.DataFrame(list(zip(sized_color_index, sized_color_values, sized_color_names)), columns =['color_index', 'rgb', 'color_name'])


    return(df)






# -----------------------------------------------------------------------------
def parse_speck(inpath, data_filter):
    """
    Parse a speck file.

    Take a speck file and parse the contents into header lines, datavar lines, and data lines.

    :param inpath: Path object of the speck file.
    :type inpath: pathlib.PosixPath
    :param data_filter: A parameter on which we filter the data, choosing lines that contain ``data_filter``. 
    :type data_filter: str
    :return: Three strings from the speck file: one for the header lines, one for the datavar lines, and one for the data lines.
    :rtype: tuple of str
    """
    
    # Open the passed file path
    with open(inpath, 'rt') as infile:

        # Define some strings. We don't care about the header lines because we reprint them
        header_lines = str()
        datavar_lines = str()
        data_lines = str()


        # Cycle through the speck file, line by line, until we're out of lines
        while True:

            # Read the line from the speck file
            line = infile.readline()

            # Break once we're out of lines
            if not line:
                break

            # If we have a line that begins with a number or a minus number, 
            # then it's a data line and we add it to the data_lines string
            if re.match(r'^[0-9]', line) or re.match(r'^-[0-9]', line):

                # Test if there is a criterion passed to the function, 
                # i.e. only choose lines that contain data_filter string
                # If we pass the value "None" then we want all lines from the speck
                if data_filter is None:
                    data_lines += line
                
                # if we pass a value, then we want only the lines it appears in
                elif data_filter in line:
                    data_lines += line

                # else, we're hosed with no data lines, should handle all this with exceptions, probably.
                else:
                    continue


            # Save the datavar lines
            elif re.match(r'^datavar', line):
                datavar_lines += line

            # If the line doesn't begin with a number or minus number, 
            # then it's a header line.
            else:
                header_lines += line

    return header_lines, datavar_lines, data_lines






# -----------------------------------------------------------------------------
def parse_lineage_csv(datainfo):
    """
    Parse the lineage csv file and return a tuple.

    :param datainfo: Metadata about the dataset.
    :type datainfo: dict of {str : list}
    :return: Returns the matching lineage codes.
    :rtype: tuple of tuples
    """    

    # Open the lineage_codes.csv and look up the code number for the clade
    file_name = 'lineage_codes.csv'
    lineage_codes_path = Path.cwd() / PROCESSED_DATA_DIRECTORY / datainfo['dir'] / datainfo['catalog_directory'] / file_name
    with open(lineage_codes_path, 'rt') as lineage_codes_file:
        
        # Read the csv file, and store the rows in a list
        cin = csv.reader(lineage_codes_file)
        lineage_key = [tuple(row) for row in cin]

    return tuple(lineage_key)






# -----------------------------------------------------------------------------
def test_input_file(path):
    """
    Test for the existence of an input file, exit if it's not there.

    :param path: A python path object to the file in question.
    :type path: path object
    :raises FileNotFoundError: Raised if the file does not exist.
    """
    if not path.is_file():
        raise FileNotFoundError('input file does not exist:\n\t' + str(path) + '\n' + 'Exiting.')





# -----------------------------------------------------------------------------
def test_path(path):
    """
    Test if a directory (path) exists, with user option to create any part of it that does not exist.

    :param path: A python path object to the file in question.
    :type path: path object
    """
    # Get a relative path from the project root directory
    relative_filepath = str(path.relative_to(Path.cwd()))

    if not Path.exists(path):
        permission_create_dir = input('\n' + PADDING + 'Create directory: ' + relative_filepath + '? (y/n/q): ')
        
        if permission_create_dir == 'y':
            Path(path).mkdir(parents=True)
            print(PADDING + '  Created directory: ' + relative_filepath)
        elif permission_create_dir == 'n':
            sys.exit('\n' + PADDING + ' -- Cannot write output file. Rerun and create the directory. --\n\tExiting.\n')
        elif permission_create_dir == 'q':
            sys.exit('\n' + PADDING + ' -- You\'ve chosen to quit. --\n'  + PADDING + 'Exiting.\n')
        else:
            sys.exit('\n' + PADDING + ' -- Not a valid choice. Choose \'y\' to create the necessary directory. --\n' + PADDING + 'Exiting.\n')
    # else:   # debugging purposes
    #     print('Path exists: ' + str(path))





# -----------------------------------------------------------------------------
def file_variable_generator(filename):
    """
    Generate an openspace variable name for the asset scenegraph variable.

    :param filename: Name of the file as a char string to be used in constructing a OpenSpace variable name.
    :type filename: str
    :return: Returns a constructed variable name.
    :rtype: str
    """    
    name_parts = filename.split('.')
    file_variable_name = name_parts[1] + '_' + name_parts[0]

    return file_variable_name





# -----------------------------------------------------------------------------
def pre_process_takanori_consensus(datainfo):
    """
    This function basically rearranges the incoming raw file into a format we need.

    :param datainfo: Metadata about the dataset.
    :type datainfo: dict of {str : list}
    """    

    # Open the consensus file to transform
    file_name = datainfo['consensus_file']
    consensus_file_path = Path.cwd() / DATA_DIRECTORY / datainfo['dir'] / datainfo['catalog_directory'] / file_name
    with open(consensus_file_path, 'rt') as consensus_file:

        # Read in the CSV file
        # 'Taxon' header is not present in the CSV, so remove all the headers, and add them manually
        df = pd.read_csv(consensus_file, header=0, names=['line_num', 'x', 'y', 'z', 'class', 'class_name', 'color', 'genus', 'taxon', 'seqid'])

    
    out_filename = 'consensus_preprocessed_' + datainfo['consensus_file']
    out_path = Path.cwd() / DATA_DIRECTORY / datainfo['dir'] / datainfo['catalog_directory'] / out_filename


    # Rearrange the columns
    df_new = df[['taxon', 'x', 'y', 'z']]


    df_new.to_csv(out_path, index=False)

    return(out_filename)



# 
# -----------------------------------------------------------------------------
def pre_process_takanori_seq(datainfo):
    """
    Preprocess the sequence file to match what the sequence processing code expects.

    :param datainfo: Metadata about the dataset.
    :type datainfo: dict of {str : list}
    """    
    
    # Open the seq file to transform
    file_name = datainfo['sequence_file']
    seq_file_path = Path.cwd() / DATA_DIRECTORY / datainfo['dir'] / datainfo['catalog_directory'] / file_name
    with open(seq_file_path, 'rt') as seq_file:

        # Read in the CSV file
        # 'Taxon' header is not present in the CSV, so remove all the headers, and add them manually
        df = pd.read_csv(seq_file, header=0, names=['line_num', 'x', 'y', 'z', 'class', 'class_name', 'color', 'genus', 'taxon', 'seqid'])

    
    out_filename = 'sequence_preprocessed_' + datainfo['sequence_file']
    out_path = Path.cwd() / DATA_DIRECTORY / datainfo['dir'] / datainfo['catalog_directory'] / out_filename


    # Rearrange the columns
    df_new = df[['seqid', 'x', 'y', 'z']]


    df_new.to_csv(out_path, index=False)

    return(out_filename)
