<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->
<a name="readme-top"></a>

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/brianpatrick/cosmic-view-life">
    <!-- <img src="images/logo.png" alt="Logo" width="80" height="80"> -->
  </a>

<h1 align="center">Cosmic View of Life on Earth</h3>

  <p align="center">
    Bringing Biology to Life Using Astronomy
    <br />
    <a href="https://github.com/brianpatrick/cosmic-view-life"><strong>Explore the docs »</strong></a>
    <br />
    <a href="https://github.com/brianpatrick/cosmic-view-life/issues">Report Bug</a>
    ·
    <a href="https://github.com/brianpatrick/cosmic-view-life/issues">Request Feature</a>
  </p>
</div>


<!-- ABOUT THE PROJECT -->
# About The Project

<!-- [![Product Name Screen Shot][product-screenshot]](https://example.com) -->

The goal of this project is to provide tools and pipelines for the display of biological
data using astronomical visualization software. [OpenSpace]() is a powerful visualization
tool with the ability to view point cloud, 3D model, and volume data on scales ranging
from centimeters to megaparsecs. (Along with stars, planets, nebulae, galaxies, and all
that fancy astronomy stuff.)

The Cosmic View of Life (CVoL) project provides a pipeline to create compelling and
interactive visualizations in [OpenSpace]() from various forms of biological data,
including CT scans, bioinformatic data, surface scans, molecular models, morphological
data, species occurrences and distribution models, and more.

Much of the documentation below assumes fairly strong familiarity with OpenSpace - for
example, asset, label, and speck files are discussed in gory detail. If you do not know
how to set up OpenSpace to read asset files from a specified path using the right
environment variables, for example, you will likely be quite lost looking at this
codebase.

You should also know Python, Conda, and how to manage environments, including creating
environments from YAML files.

In short, *this* is how the sausage is made.


<p align="right">(<a href="#readme-top">back to top</a>)</p>

# `Makefile` and your development environment

This project uses make. Many of the scripts have more than a few parameters and using a
Makefile makes it a bit easier to build datasets. This also implies running this in a
Linux/UNIX environment. You *may* be able to get this running on Windows using cygwin or
something similar, but this has not been tested. Some scripts also use packages that are
known (as of this writing, Feb 2025) not to run on Windows (the ETE toolkit, in
particular). This codebase was developed using Windows Subsystem for Linux (WSL). Running
on a dedicated Linux install would likely work just fine.

This project uses Python and requires many packages. Conda is highly recommended for
setting up your environment, and the `cosmic-view-life.yml` file can be used to install
required packages. If you are generating 3D models of proteins from PDB identifiers, you
should use `cosmic-proteins.yml`.

The `Makefile` requires a `Makefile.config` include file that contains the following
important variables:

    OPENSPACE_CACHE := /mnt/e/git/OpenSpace-sonification/cache
    OPENSPACE_ASSET_DIR := /mnt/e/OpenSpace/user/data/assets

`OPENSPACE_CACHE` is the cache directory for your OpenSpace runtime setup. The `Makefile`
is set up to clean out the cache of development files to make sure the next run of
OpenSpace is using updated files.

`OPENSPACE_ASSET_DIR` is where you keep your asset files and is typically set with
an environment variable for your given setup.

This will likely go out of date very quickly, but as of the time of this writing (21 Feb
2025), rules have been set up for the following targets:

 - `jan_30_2025_recentered` contains the eukaryotes sphere along with bird and mammal
   data. A wolf protein is also done, along with a wolf skull.
 - `takanori_protein_universe` plots many (well, most?) of the points in the Protein
   Universe paper. This dataset contains the default plot from the paper along with 4 from
   Takanori- two 2D projections along with two 3D projections.

## Pymol

A quick note on the Pymol package. If your dataset does not include displaying protein
models in 3D from PDB, you will not need Pymol. If you *do* need Pymol, it's assumed you
know how to install it. (Using the `cosmic-proteins` YAML file to set up an environment
should be sufficient.)

# Programs

Well, scripts. But scripts can be programs, too. 

## `csv_to_openspace.py`

Transforms CSV files with points and taxonomy data to point (or star) assets
and labels in OpenSpace.

Options/usage is as follows:


    usage: csv_to_openspace.py [-h] -i INPUT_DATASET_JSON_FILE -a ASSET_DIR [-o OUTPUT_DIR] [-t TEXTURE_DIR] [-v]

    Process input CSV files for OpenSpace.

    options:
      -h, --help            show this help message and exit
      -i INPUT_DATASET_JSON_FILE, --input_dataset_json_file INPUT_DATASET_JSON_FILE
                            Input dataset JSON file.
      -a ASSET_DIR, --asset_dir ASSET_DIR
                            OpenSpace directory for assets.
      -o OUTPUT_DIR, --output_dir OUTPUT_DIR
                            Directory for local copy of output files.
      -t TEXTURE_DIR, --texture_dir TEXTURE_DIR
                            Directory holding texture files for points.
      -v, --verbose         Verbose output.

### Input JSON file

`csv_to_openspace.py` is directed what to do using a JSON file that details each input
file and what to do with it. The simplest JSON file looks something like this:

    {
        "Description": "Recentered data for Jan 30 2025",
        "gui_top_level": "CVoL Jan 30 2025",
        
        "datasets": [
            {
                "csv_file": "eukaryotes_classes.csv",
                "type": "points",
                "data_scale_factor": 100000,
                "default_texture": "point3a.png",
                "point_scale_factor": 29.9,
                "point_scale_exponent": 4.6,
                "max_size": 0.1,
                "color_by_columns": ["phylum", "class"],
                "colormap": "colormaps.Misc.Flag",
                "interaction_sphere": 1,
                "gui_info": {
                    "path": "Eukaryotes/Points",
                    "name": "Classes",
                    "hidden": false
                }
            },
        ]
    }

`type` can be one of the following:
  - `points` for individual data points
  - `labels` for point labels. Labels do not need to be associated with a point.
  - `group_labels` for labeling a group of points semi-automatically.
  - `models` for placing 3D models at point locations.
  - `pdb` for placing 3D protein models from the Protein Data Bank at point locations.

Many of the parameters specified have direct analogs to OpenSpace parameters for different
renderables, such as `RenderablePointCloud`, `RenderableConstellationLines`, and
`RenderableModel`.



## `clean_openspace_cache.py`



## `make_tree_with_models.py` 

This python script (and the associated files in `tree_input_files` takes a Newick format
input file and a list of models in CSV format to create a 3D phylogenetic tree with models
at leaves and nodes.

## `plot_insect_points.py`

This is a proof-of-concept script to process some updated data from Wandrille. Its logic
was ported to the much more flexible `csv_to_openspace.py` script.

# Directories

The repository contains the following directories:

## `./data`

Input data from various sources can be found in `./data`.

### `./data/Jan_30_2025_recentered`

### `./data/Odonata`

### `./data/Takanori_Protein_Universe`


### `./data/points_around_earth`

OpenSpace is geared towards astronomical visualizations, but is able to display a
high-resolution globe of the earth with all kinds of data overlaid, such as distribution
maps, sea surface temperatures, elevations, and so on. A key visualization mode of CVoL is
to depict species as points over the globe as a "star field of life". A "nested" model is
used, whereby larger points representing higher level groups such as "green plants",
"protists", "insects", "chordates" is initially shown. Flying up to a group such as
"mammals" results in a field of points around this "parent point", where points represent
(for example) individual species and are grouped taxonomically. 

(TODO: Need to make an example that can be run, sudh as mammals or something.)





## `./catalogs_raw`

Datasets used in early visualizations. Not guaranteed to work properly as data formats and
processing algorithms have changed quite a bit over the course of the project, so these
will not be described in detail.


## `./integrate_tree_to_XYZ`

This git submodule is Wandrille's code to convert Timetree data (`timetree.org`) into
3-dimensional points. Some of the code in `/src` and `make_tree_with_models.py` benefitted
from access to internal data structures in Wandrille's original project, so it was
modified to allow inclusion as a python `import`. 

# Archived stuff

The following directories and programs are outdated. They're all from early incarnations
of the project and various proofs-of-concept.

## `catalogs_raw/`

As mentioned above, most of the data in this directory is not used. You may be able to run
`main.py`, an earlier script, to make something of these, but this display model is not
currently used.

## `main.py`:

The (original) main function that all other programs are called from. This script has been
partially subsumed by the previous scripts noted above.

The placement of most of the logic in this file allows for a modular style of processing
by commenting and uncommenting function calls to various parts of the code. The scripts
above tend to use parameter files as inputs to direct the scripts as to what data to
process and where to find it. Much of that code is based on the original code in `main.py`
and the `/src` subdirectory.

## `actions/`:

This folder contains some pre-coded actions for insect plots. It's largely outdated,
since now actions are typically created programatically at runtime.




## src/:

  - **colors.py:** Generates a color map file based on a color table or a list of colors.
  - **common.py:** Some common variables and functions used across these files.
  - **consensus_species.py:** Processes the consensus species data and merges the common names (vocabulary) read in via a function in the main.py file. Produces OpenSpace data and asset files.
  - **human_origins.py:** Process the human origin/migration data and asset file.
  - **metadata.py:** Process the taxon metadata for a given class (primates, for example), which mainly consists of the lineage information.
  - **sequence_lineage.py:** Process label and color map files by lineage and makes asset file.
  - **sequence.py:** Generates main dataset of DNA sequence data, which can have many data per species. Also generates the OpenSpace asset file.
  - **slice_by_clade.py:** Pull DNA samples from the main speck file given an input clade (e.g. Homo) and print data and asset files.
  - **slice_by_lineage.py:** Generate a file with various columns for color mapping to trace on taxon lineage from species level back to the class level
  - **slice_by_taxon.py:** Pull DNA samples from the main speck file given an input taxon (e.g. Homo Sapiens) and print data and asset files.
  - **takanori_trials.py:** Process Takanori's trials and merge with other metadata to produce OpenSpace data and asset files.



### Animal Orders (/primates, /birds, etc.):

All the resulting output files from the python scripts, including speck, label, color map files, and asset files.

Upon running the python scripts, they will ask you to create these directories and their subdirectories if they don't exist.
  

### /catalogs_processed:

Contains (mostly) csv files that are refined from the raw data and useful for processing the final data formats.


### /logs:

Text files with some statistical information on some of the runs. 
  
<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Usage

```python3 main.py```

Control of what runs is via comments in the main.py file. With all the function calls uncommented, the entire project will generate from scratch given the raw data are present.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- LICENSE -->
# License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
# Contact

Brian Abbott - abbott@amnh.org

Project Link: [https://github.com/brianpatrick/cosmic-view-life](https://github.com/brianpatrick/cosmic-view-life)

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- ACKNOWLEDGMENTS -->
# Acknowledgments

This project is a joint venture between the [American Museum of Natural History](https://www.amnh.org) in New York, [University of Basel](https://www.unibas.ch/en.html) in Switzerland, and [Linköping University](https://scivis.github.io) in Sweden. It combines researchers from astronomy, biology, and data visualization in a cross-disciplinary team.

This project is funded by the Richard Lounsbery Foundation.

## Primary players


- [Brian Abbott](https://brianabbott.net) (American Museum of Natural History) Data visualization, astronomer by trade, and author of these codes.
- [Hollister Herhold](https://sites.google.com/view/hollister-herhold) (American Museum of Natural History) Entomologist, evolutionary biologist, former software engineer.
- [Wandrille Duchemin](https://github.com/WandrilleD) (University of Basel & SIB Swiss Institute of Bioinformatics) Biologist & bioinformatics guru
- [Jackie Faherty](https://www.jackiefaherty.com) (American Museum of Natural History) Astrophyscist with a deep interest in data visualization.
- [Takanori Fujiwara](https://takanori-fujiwara.github.io) (Linköping University) Dimensional reduction expert.
- [Will Harcourt-smith](https://www.gc.cuny.edu/people/william-harcourt-smith) (AMNH, CUNY) Anthropologist with interests (among other things) in 3D morphometrics.
- [David Thaler](https://phe.rockefeller.edu/bio/dthaler) (University of Basel & Rockefeller University, New York) Biologist and big thinker.


## Students

Our graduate students are studying at Sweden's University of Linköping. Each student project is an innovative step forward and results in their master's thesis.

### Advisors

- [Alexander Bock](https://github.com/alexanderbock) (Linköping University)
- [Emma Broman](https://github.com/WeirdRubberDuck) (Linköping University)

### 2022

- Emma Segolsson
- Linn Storesund

### 2023
- Märta Nilsson
- Robin Ridell


<p align="right">(<a href="#readme-top">back to top</a>)</p>