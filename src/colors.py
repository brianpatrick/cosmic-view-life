'''
Generate a color palette of colors to sample from for our color map (.cmap) files.

Reads a list of colors scraped from a wikipedia page of crayola crayons.
https://en.wikipedia.org/wiki/List_of_Crayola_crayon_colors

Convert the hex color values into red, green, blue colors. 
Write the colors out to a master file.

Then, form a list of chosen colors and print a chosen_colors color table which will be
used to sample colors for the color map files.

Author: Brian Abbott <abbott@amnh.org>
Created: September 2022
'''

import pandas as pd
from pathlib import Path
from colormap import hex2rgb

from src import common



def crayola_color_table(datainfo):

    # Read the HTML table saved locally
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
    '''
    Convert a hex color to an RGB, then normalize between 0-1.
    Returns a pandas series of the color values.
    '''
    rgb = hex2rgb(hex)
    red = rgb[0] / 255
    green = rgb[1] / 255
    blue = rgb[2] / 255
    alpha = 1.0

    return pd.Series([red, green, blue, alpha])

