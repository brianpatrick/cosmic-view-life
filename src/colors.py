# 

# Author: Brian Abbott <abbott@amnh.org>
# Created: September 2022
"""
The color module processes a list of colors into a usable color table file (:file:`.dat`). This color table file is then sampled to make color map files (:file:`.cmap`) that are OpenSpace-ready.


Generating Color Tables
===============================================================================

We adopt a main color sample from the `Wikipedia page for crayola crayons <https://en.wikipedia.org/wiki/List_of_Crayola_crayon_colors>`_, where a list of colors and their hex values are scraped and stored in :file:`catalogs_raw/color_tables/crayola`.

This process, theoretically, needs to be run only once, assuming you don't alter the ``chosen_colors`` list of preferred colors. Once you run it for the first time, the function call ``make_color_tables(datainfo)`` may be commented out of :file:`main.py`.

Other color schemes may be used and can coexist beside the crayola scheme, but would require a new function to process them into a color table that would be sampled.



Main Color Palette
-------------------------------------------------------------------------------

The main list of colors is scraped from the standard colors table on Wikipedia's List of Crayola crayon colors. This provides the basis of available colors, but note we only include colors with hexidecimal values.

The colors.py converts the hex number to an red, green, blue, and alpha values, then creates a main color table called :file:`crayola.dat` in the `catalogs_processed/color_tables/crayola/` directory.

Next, we supply a list of preferred colors, called `chosen_colors`, that will pull colors from the main list and create a color map file that may be accessed to make OpenSpace-ready color map files in subsequent codes. These chosen colors include:

| Scarlet, Orange, Maize, Lemon Yellow, 
| Yellow-Green, Fern, Asparagus, Sea Green,
| Aquamarine, Blue-Green, Sky Blue, Periwinkle,
| Indigo, Violet-Blue, Purple Heart, Wisteria,
| Fuchsia, Orchid, Magenta, Carnation Pink, 
| Salmon, Mahogany, Burnt Sienna, Sepia, 
| Peach, Shadow, Silver, Blue-Gray




"""

import pandas as pd
from pathlib import Path
from colormap import hex2rgb

from src import common



# -----------------------------------------------------------------------------
def crayola_color_table(datainfo):
    """
    Generate a color table from a source table based on the crayola crayon colors.

    Reads a list of colors scraped from a wikipedia page of crayola crayons. 
    https://en.wikipedia.org/wiki/List_of_Crayola_crayon_colors

    Clean up the colors, toss out the rejects, and convert the hex color values into red, green, blue colors. 
    
    Create a custom list of desired colors ``chosen_colors`` and shuffle them in an order that makes sense. 
    
    Finally, write out the list to a ``.dat`` file that will be used to tap colors from across the project.

    :param datainfo: Metadata about the dataset.
    :type datainfo: dict of {str : list}
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

