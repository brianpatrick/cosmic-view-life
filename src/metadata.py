'''
Cosmic View of Life on Earth

Process the taxon metadata. This mainly consists of the lineage information.
We process these columns, but only include certain lineage columns based on 
the parameters in the datainfo dict.

Author: Brian Abbott <abbott@amnh.org>
Created: September 2022
'''

import pandas as pd
import re
from pathlib import Path

from src import common


def process_data(datainfo):
    '''
    Processes the lineage columns and other metadata for a branch of the tree.

    1. Reads the *.taxon.metadata.csv file (primates, birds, ...)
    2. Expands the comma-separated lineage column into multiple columns
    3. Pulls all unique values for each colum, and deletes any None values
    4. For each lineage column, form a dictionary with a corresponding custom, integer code
    5. Write results to a separate reference file, and pass the metadata back to calling function 

    Input:
        dict(datainfo)
        [clade-class].taxons.metadata.csv       # such as, primates.taxons.metadata.csv
    
    Output:
        metadata.csv            # A csv file with the processed metadata
        lineage.dat             # A human-readable list of lineage codes for each lineage level
        lineage.csv             # lines of lineage col names, lineage col integer, number of clades, and clade names
        lineage_codes.csv       # List of lineage codes and their corresponding clade name
        metadata.py.log         # An output log
    '''

    common.print_subhead_status('Processing Metadata (including lineage)')


    datainfo['data_group_title'] = datainfo['sub_project'] + ': Metadata with lineage'
    datainfo['data_group_desc'] = 'Metadata for the ' + datainfo['sub_project'].lower() + ' data, \
        including a key for the lineage integers, needed for OpenSpace. \
        Each unique lineage name is assigned an integer. That integer begins with the \
        lineage column number (e.g., cols 1-25 become integers 10nnn-250nnn, \
        with nnn being the unique number for the lineage name. The first unique name in \
        lineage column 1 is 1001, the first item in the 25th column is 25001.'

    

    inpath = Path.cwd() / common.DATA_DIRECTORY / datainfo['dir'] / datainfo['catalog_directory'] / datainfo['metadata_file']
    common.test_input_file(inpath)
        
    # Read the CSV file
    df = pd.read_csv(inpath, sep=';', header=0, names=['taxon', 'species', 'hybrid', 'subspecies', 'lineage'])

    # Split the comma-separated lineage column in the CSV file into its
    # own dataframe so we can process it separately.
    split_cols = df['lineage'].str.split(',', expand=True)

    # Rename each column to "lineage_i" for columns 1-34.
    # Note, we need to add one to the end of the range.
    split_cols.columns = [f'lineage_{i}' for i in range(1, int(datainfo['lineage_columns'][1])+1)]

    # Save the dataframe into a new dataframe
    metadata = df.join(split_cols)

    # Delete the comma-separated column called "lineage" from the dataframe,
    # it's replaced by the individual columns now.
    del metadata['lineage']

    # Change the hybrid column from "True|False" to "1" or "0"
    metadata['hybrid'] = metadata['hybrid'].replace([True], '1')
    metadata['hybrid'] = metadata['hybrid'].replace([False], '0')


    # Step through each column of the metadata dataframe. We need to assign
    # integers (lineage codes) to each unique entry in each lineage column. 
    # We structure these integers as [col_num][i], where:
    #   [col_num] is the lineage index + 10 (1-34, which becomes 10-340)
    #   [i] value is a running 1-N code of the unique number of entries for that column
    # ---------------------------------------------------------------------------
    
    # lineage is a nested dict, with lineage_X: {lineage_code: lineage_name} format,
    # for example: { lineage_31: { 31009: Homo } }
    lineage = dict()

    # unique_values holds all the unique lineage values temporarily
    unique_values = list()

    # unique_lineage holds all the unique names for each column in metadata file
    unique_lineage = dict()

    # Will add a factor of 100 to each lineage column number, so col 1 is 100, col 10 = 1000,
    # and col 22 = 2200. We use a factor of 100 because some lineage columns have over 100 unique
    # entries. So, when we add the [i] to the [col_num], the 500th unique item in col 22 becomes 22500.
    col_num = 100

    # Step through each column (key) in the metadata dataframe.
    for col in metadata:
        
        # For those columns that match on "lineage_", perform the following
        if re.match('^lineage_', col):
            
            # reset the lineage code for each column
            i = 1

            # Put each unique item in the column into a list
            temp_list = list(metadata[col].unique())
            
            # If any column contains None, remove it from our unique values list
            if None in temp_list:
                temp_list.remove(None)

            # Number of unique values
            unique_values.append(len(temp_list))

            
            # Set the start value for the dict enumeration based on the lineage code,
            # plus the running number code in that col for unique values. 
            # So, lineage_1 column will start with 1001 (100 for lineage 1 column, 
            # and 1 for the first unique item in the list). Similarly, the first
            # unique value in column lineage_30 will be 30001, 30002, and so on.
            start_val = int(str(col_num) + str(i))

            # We're taking each column of unique lineage values,
            # putting them into a dictionary of the form {lineage_code: lineage_value}
            unique_lineage[col] = dict(enumerate(temp_list, start=start_val))

            # Convert the dictionary into a pandas series. This series only holds
            # one column of unique values
            series_name = col + '_code'
            lineage = pd.Series(unique_lineage[col], name=series_name)
            
            
            # Run thru each value in each lineage metadata column (lineage_* cols only)
            row_number = 0
            for value in metadata[col]:

                # If the value in the lineage_* column is None,
                # then set it to zero and go to the next row in metadata
                if value is None:
                    metadata.at[row_number, series_name] = '0'
                    row_number += 1
                    continue


                # If metadata value is not None, then run thru each value in the 
                # unique lineage pandas series.
                for v in lineage:
                    
                    # If the metadata value and the value in the lineage series match,
                    # get the code and save it to metadata in a new column lineage_*_code.
                    if v == value:
                        
                        # Get the index number for the matching values. These index
                        # numbers are the lineage codes we need. (30001, etc.)
                        lineage_code = str(lineage[lineage == v].index[0])

                        # Write the new column and give the row the lineage_code value
                        metadata.at[row_number, series_name] = lineage_code

                        # Iterate the row number to go to the next row in metadata column
                        row_number += 1


            # Iterate the column number. 100 because we need unique values for 
            # each unique entry in each lineage column. See comment above where this is defined.
            col_num += 100




    # Print the metadata info to a separate file for reference in CSV format.
    # Do this because it takes time to process this step of matching lineage codes
    # ---------------------------------------------------------------------------
    
    # This is the root path for all output files in this script,
    # so only need to set and check it once.
    outpath = Path.cwd() / common.PROCESSED_DATA_DIRECTORY / datainfo['dir'] / datainfo['catalog_directory']
    common.test_path(outpath)

    outfile_metadata_csv = 'metadata.csv'
    outpath_metadata_csv = outpath / outfile_metadata_csv

    with open(outpath_metadata_csv, 'wt') as csv_metadata:

        # Print the metadata info to the file. This line will print the column headers too.
        metadata.to_csv(csv_metadata, index=False)


    # Report to stdout
    common.out_file_message(outpath_metadata_csv)




    # Print a lineage key, to have a look-up file for the lineage codes
    # ---------------------------------------------------------------------------
    # We print a human-readable and a CSV version of the lineage code mapping
    outfile_lineage_key_dat = 'lineage.dat'
    outpath_lineage_key_dat = outpath / outfile_lineage_key_dat

    # This file is a straight list of lineage code to lineage name
    outfile_lineage_key_csv = 'lineage_codes.csv'
    outpath_lineage_key_csv = outpath / outfile_lineage_key_csv

    # This file is a list of lineage columns with corresponding lineage integer, number of
    # unique lineage names, and a listing of those namens
    outfile_lineage_csv = 'lineage.csv'
    outpath_lineage_csv = outpath / outfile_lineage_csv

    with open(outpath_lineage_key_dat, 'wt') as dat_lineage_key, \
        open(outpath_lineage_key_csv, 'wt') as csv_lineage_key, \
        open(outpath_lineage_csv, 'wt') as csv_lineage:
        
        # Print some header info at the top of the file
        header = common.header(datainfo)
        print(header, file=dat_lineage_key)

        # Print the lineage items in a custom format
        # num_lineage_values is the counter for the unique_values list, which keeps 
        # track of how many values are in each lineage column.
        num_lineage_values = 0
        for k, v in unique_lineage.items():
            
            # Get the integer from the lineage column name
            lineage_col_number = int(re.search(r'\d+', k).group())

            # Print the lineage column as a subhead
            print(f"{k}: {unique_values[num_lineage_values]} unique members", file=dat_lineage_key)

            # Print the lineage column name, number, and number of unique values in that column
            print(f"{k},{lineage_col_number},{unique_values[num_lineage_values]} | ", file=csv_lineage, end='')

            # Run thru the lineage nested dict and print the key-value pairs
            for key, value in v.items():
                print(f"    {key} = {value}", file=dat_lineage_key)
                print(f"{key},{value}", file=csv_lineage_key)
                print(f"{value},", file=csv_lineage, end='')
            
            # Print a final newline after each lineage column to kick off a new one
            print('\n', file=dat_lineage_key)
            print(file=csv_lineage)

            num_lineage_values += 1


    common.out_file_message(outpath_lineage_key_dat)
    common.out_file_message(outpath_lineage_key_csv)
    common.out_file_message(outpath_lineage_csv)




    # Print some statistics about the metadata into a file
    # ---------------------------------------------------------------------------
    outfile_log = Path(__file__).name + '.log'
    
    log_path = Path.cwd() / common.LOG_DIRECTORY / datainfo['dir'] / datainfo['catalog_directory']
    common.test_path(log_path)
    outpath_log = log_path / outfile_log


    with open(outpath_log, 'wt') as log:

        print('Generated log from ' + Path(__file__).name + ' run with the ' + datainfo['sub_project'] + ' data set.', file=log)
        print('================================================================================', file=log)

        # Some general stats, number of rows and columns
        print('Number of rows: ' + str(len(metadata.index)), file=log)
        print('Number of columns: ' + str(len(metadata.columns)), file=log)
        print(file=log)


        # Set the max_rows so we print all the rows in the df
        pd.set_option("display.max_rows", None)

        # Print all the column names
        print('Columns:', file=log)
        print(pd.DataFrame({"column": metadata.columns, "non-nulls": len(metadata)-metadata.isnull().sum().values, "nulls": metadata.isnull().sum().values, "type": metadata.dtypes.values}), file=log)
        print(file=log)


        # Print the lineage stats

        # Cycle thru the columns in the metadata df
        for col in metadata.columns:

            # If the column ends in "_code", to catch the lineage_*_code columns
            if re.search(r'_code$', col):

                # Print the column name
                print('Column: ' + col, file=log)

                # Print the unique values and their count, sorted by the column, not the highest count
                print(metadata[col].value_counts().sort_index(), file=log)
                print(file=log)


    common.out_file_message(outpath_log)


    return metadata
