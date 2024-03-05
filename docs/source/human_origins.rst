*******************************************************************************
Human Origins Data
*******************************************************************************

Control of these functions and data is via the ``origins(datainfo)`` function call in ``main.py``. Comment out this function call to bypass processing the human origins data.



Continent and Region Codes
===============================================================================

The raw data from Wandrille has the DNA sequence data, along with origin metadata. The functions in  ``human_origins.py`` first read those data, then converts the origin name into an integer so we can leverage it within OpenSpace. First, we give each data sample a continent code, as follows:

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

These codes are exported to the ``region_population_code_key.dat`` file in the ``processed_catalogs`` directory.



Output Data
===============================================================================

The main dataset is printed to the ``human_origins.speck`` and accompanying ``human_origins.label`` file. In addition, we print ``speck`` files for each region so they may be toggled separately within OpenSpace.

Finally, we generate a color map file for the continent codes and for the regional codes, choosing from our main color table that mine using a ``find_color`` function in ``common.py`` to pull the colors from the color table file.