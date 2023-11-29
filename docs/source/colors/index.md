# Generating Color Maps

There are some tools and color palettes available to generate color maps used for OpenSpace. We adopt a main color sample from the [Wikipedia page for crayola crayons](https://en.wikipedia.org/wiki/List_of_Crayola_crayon_colors), where a list of colors and their hex values are scraped and stored.

This process, theoretically, needs to be run only once, assuming altering the `chosen_colors` is not needed. Once you run it for the first time, the function call `make_color_tables(datainfo)` may be commented out of `main.py`.


## Main Color Palette

The main list of colors is scraped from the standard colors table on Wikipedia's List of Crayola crayon colors. This provides the basis of available colors, but note we only include colors with hexidecimal values.

The colors.py converts the hex number to an red, green, blue, alpha, then creates a main color table called `crayola.dat` in the `catalogs_processed/color_tables/crayola/` directory.

Next, we supply a list of preferred colors, called `chosen_colors`, that will pull colors from the main list and create a color map file that may be accessed to make OpenSpace-ready color map files in subsequent codes.



:::{toctree} :caption: Running the Code :name: sec-running :maxdepth: 2 :hidden: :titlesonly:

general/releases/index general/academics :::

:::{toctree} :caption: Primates :name: sec-primates :maxdepth: 2 :hidden: :titlesonly:

getting-started/introduction/index getting-started/profiles/index :::