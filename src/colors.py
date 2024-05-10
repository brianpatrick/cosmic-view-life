# Cosmic View of Life on Earth
#
# Author: Brian Abbott <abbott@amnh.org>
# Created: September 2022
"""
The color module processes a list of colors into a usable color table file (:file:`.dat`). This color table file is then sampled to make color map files (:file:`.cmap`) that are OpenSpace-ready.

.. note::
    Theoretically, this module needs to be run only once, assuming you don't alter the ``chosen_colors`` list of preferred colors defined in ``crayola_color_table()``. Once you run it for the first time, the function call ``make_color_tables(datainfo)`` may be commented out of :file:`main.py`.

    

Generating Color Tables
===============================================================================






"""

import pandas as pd
from pathlib import Path
from colormap import hex2rgb

from src import common



# -----------------------------------------------------------------------------
def crayola_color_table(datainfo):
    """
    Generate a color table from a source list of colors based on the crayola crayon colors.

    :param datainfo: Metadata about the dataset.
    :type datainfo: dict of {str : list}
    
    We adopt a main color sample from the `Wikipedia page for crayola crayons <https://en.wikipedia.org/wiki/List_of_Crayola_crayon_colors>`_, where a list of colors and their hex values are scraped and stored in :file:`catalogs_raw/color_tables/crayola/crayola_colors.html`. We reduce the resulting list down to colors that have hex values, and remove a few other undesirable colors.

    .. note::
        Alternative color schemes may be used and can coexist beside the crayola scheme, but would require a new function to process them into a color table that would be sampled later.

    One result of processing the crayola colors is a file called :file:`catalogs_processed/color_tables/crayola/crayola.dat`. This is a master list of colors in red-green-blue-alpha format, along with the name of the color.

    We also produce a second, customized color table called :file:`catalogs_processed/color_tables/crayola/chosen_colors.dat`. This is a subsample of colors from the main list determined by the ``chosen_colors`` list in the ``crayola_color_table()`` function. We take the ``chosen_colors`` list, change the order of colors, and print it to a file. This is the main file used to generate OpenSpace-ready color map files (:file:`.cmap`).

    These chosen colors include:

    | Scarlet, Orange, Maize, Lemon Yellow, 
    | Yellow-Green, Fern, Asparagus, Sea Green,
    | Aquamarine, Blue-Green, Sky Blue, Periwinkle,
    | Indigo, Violet-Blue, Purple Heart, Wisteria,
    | Fuchsia, Orchid, Magenta, Carnation Pink, 
    | Salmon, Mahogany, Burnt Sienna, Sepia, 
    | Peach, Shadow, Silver, Blue-Gray
    """    

    # Read the HTML table saved locally
    #inpath = Path.cwd() / common.DATA_DIRECTORY / common.COLOR_DIRECTORY / datainfo['catalog_directory'] / 'crayola_colors.html'
    inpath = Path.cwd() / common.DATA_DIRECTORY / common.COLOR_DIRECTORY / datainfo['catalog_directory'] / 'crayola_colors.html'
    common.test_input_file(inpath)

    table = pd.read_html(inpath)

    # Define the table
    crayola_colors = table[0]

    # Set a df and rename the Hex column
    colors = crayola_colors[['Name', 'Hexadecimal in their website depiction  [b]']]
    colors = colors.rename(columns = {'Hexadecimal in their website depiction  [b]':'hex'})

    # Drop any rows that do not have a hex color
    colors.drop(colors[colors['hex'].isnull()].index, inplace=True)

    # Convert the colors usung the rgba() function above.
    colors[['red', 'green', 'blue', 'alpha']] = colors.apply(lambda x: rgba(x['hex']), axis=1, result_type='expand')

    # Compute a colorindex value so we can sort colors if we like
    #colors['index'] = (colors['red'] + colors['green'] + colors['blue']) / 3.0

    # Open the cmap file and write the list of colors
    outfile = 'crayola.dat'
    outpath = Path.cwd() / common.PROCESSED_DATA_DIRECTORY / common.COLOR_DIRECTORY / datainfo['catalog_directory']
    common.test_path(outpath)

    outpath = outpath / outfile
    with open(outpath, 'wt') as color_table:
        for _, row in colors.iterrows():
            print(f"{row['red']:.6f} {row['green']:.6f} {row['blue']:.6f} {row['alpha']:.6f} # {row['Name']}", file=color_table)



    # Set up a select list of colors to mine for color maps
    # This gets rid of colors that are too close in hue, etc.
    chosen_colors = ['Scarlet', 'Orange', \
        'Maize', 'Lemon Yellow', 'Yellow-Green', \
        'Fern', 'Asparagus', 'Sea Green', \
        'Aquamarine', 'Blue-Green', 'Sky Blue', 'Periwinkle', 'Indigo', \
        'Violet-Blue', 'Purple Heart', 'Wisteria', 'Fuchsia', 'Orchid', \
        'Magenta', 'Carnation Pink', 'Salmon', \
        'Mahogany', 'Burnt Sienna', 'Sepia', 'Peach', 'Shadow', \
        'Silver', 'Blue-Gray']


    # Sort the colors to alternate colors so similar colors aren't beside one another.
    # We step through every 4th color in the chosen_colors list, adding the subsequent
    # subsets to the new sorted list.
    chosen_colors_sorted = chosen_colors[3::4]
    chosen_colors_sorted.extend(chosen_colors[1::4])
    chosen_colors_sorted.extend(chosen_colors[2::4])
    chosen_colors_sorted.extend(chosen_colors[0::4])



    outfile_chosen = 'chosen_colors.dat'
    outpath_chosen = Path.cwd() / common.PROCESSED_DATA_DIRECTORY / common.COLOR_DIRECTORY / datainfo['catalog_directory']
    common.test_path(outpath_chosen)

    outpath_chosen = outpath_chosen / outfile_chosen
    with open(outpath_chosen, 'wt') as chosen_color_table:
        
        # Cycly thru the color names in the chosen_colors list
        for color in chosen_colors_sorted:

            # Cycle thru the full color table
            for col, row in colors.iterrows():

                # If we have a matching chosen color in the full color table, 
                # print to the chosen color table file
                if row['Name'] == color:
                    print(f"{row['red']:.6f} {row['green']:.6f} {row['blue']:.6f} {row['alpha']:.6f} # {row['Name']}", file=chosen_color_table)
    

    common.out_file_message(outpath_chosen)
    print()





def rgba(hex):
    """
    Convert a hex color to an RGB, then normalize between 0-1.

    :param hex: A hexidecimal color value
    :type hex: str
    :return: A pandas series of red, green, blue, and alpha.
    :rtype: Series
    """
    rgb = hex2rgb(hex)
    red = rgb[0] / 255
    green = rgb[1] / 255
    blue = rgb[2] / 255
    alpha = 1.0

    return pd.Series([red, green, blue, alpha])


def read_cmap_into_df(cmap_path):
    """
    Read a cmap file into a pandas dataframe. The cmap file is formatted for
    use by OpenSpace, but we need a useable dataframe representation of it
    here to add color map info to various structures, dataframes, trees, etc.

    cmap files are formatted with R G B A floating point values, followed by a
    comment prefixed with #. The comment is the name of the color follwed by 
    ' - ' and a taxon associated with that color (for example, family name).

    The dataframe contains the following:
    1. The RGBA values. These may or may not be used internally.
    2. The taxon name. This is the name of the taxon associated with the color.
    3. An index corresponding to the color in the cmap file. These are
       in the same order as in the cmap file and are used in constructing
       the csv file that contains the XYZ coordinates for each taxon node in
       a tree (for example).

    :param cmap_path: The path to the cmap file.
    :type cmap_path: Path
    :return: A pandas dataframe of the cmap file.
    :rtype: DataFrame
    """

    # Read the cmap file into a dataframe. Unfortunately the file is a little too
    # complicated to use read_csv, so we will read it in an process it a line at
    # a time.

    # Open the file, and define a list to hold the data one line at a time.
    with open(cmap_path, 'rt') as cmap_file:
        cmap_lines = cmap_file.readlines()

    # Skip the first line and process each line in the file.
    cmap_data = []
    for line in cmap_lines[1:]:
        # Split the line into the color and the taxon name
        color, taxon = line.split('#')
        # Split the color into the RGBA values
        rgba = color.split()
        # Extract the taxon name
        taxon = taxon.strip()
        # Separate out the taxon name from the taxon and color. It is separated by ' - '.
        taxon = taxon.split(' - ')[1]
        # Append the data to the cmap_data list
        cmap_data.append([float(rgba[0]), float(rgba[1]), float(rgba[2]), float(rgba[3]), taxon])

    # Create a dataframe from the cmap_data list
    cmap_df = pd.DataFrame(cmap_data, columns=['red', 'green', 'blue', 'alpha', 'taxon'])

    # Finally, add index numbers starting with 1 to the dataframe.
    cmap_df['index'] = cmap_df.index + 1
        
    return cmap_df