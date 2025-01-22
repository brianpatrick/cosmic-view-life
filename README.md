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



<!-- TABLE OF CONTENTS
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>
 -->



<!-- ABOUT THE PROJECT -->
# About The Project

<!-- [![Product Name Screen Shot][product-screenshot]](https://example.com) -->

The goal of this project is to provide tools and pipelines for the display of biological
data using astronomical visualization software. [OpenSpace]() is a powerful visualization
tool with the ability to view point cloud, 3D model, and volume data on scales ranging
from centimeters to megaparsecs. The Cosmic View of Life (CVoL) project provides a
pipeline to create compelling and interactive visualizations in [OpenSpace]() from various
forms of biological data, including CT scans, bioinformatic data, surface scans, molecular
models, morphological data, species occurrences and distribution models, and more.

Much of the documentation below assumes familiarity with OpenSpace - for example, asset,
label, and speck files are discussed in gory detail.


<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED
## Getting Started

This is an example of how you may give instructions on setting up your project locally.
To get a local copy up and running follow these simple example steps.

### Prerequisites

This is an example of how to list things you need to use the software and how to install them.
* npm
  ```sh
  npm install npm@latest -g
  ```

### Installation

1. Get a free API Key at [https://example.com](https://example.com)
2. Clone the repo
   ```sh
   git clone https://github.com/github_username/repo_name.git
   ```
3. Install NPM packages
   ```sh
   npm install
   ```
4. Enter your API in `config.js`
   ```js
   const API_KEY = 'ENTER YOUR API';
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

 -->


<!-- ORGANIZATION -->
# Programs

Well, scripts. But scripts can be programs, too. 

## `csv_to_openspace.py`

Transforms CSV files with points and taxonomy data to point (or star) assets
and labels in OpenSpace.

The program:

    usage: csv_to_openspace.py [-h] -i INPUT_DATASET_CSV_FILE -c CACHE_DIR -a ASSET_DIR [-v]

    Process input CSV files for OpenSpace.

    options:
    -h, --help            show this help message and exit
    -i INPUT_DATASET_CSV_FILE, --input_dataset_csv_file INPUT_DATASET_CSV_FILE
                            Input dataset CSV file.
    -c CACHE_DIR, --cache_dir CACHE_DIR
                            OpenSpace cache directory.
    -a ASSET_DIR, --asset_dir ASSET_DIR
                            Output directory for assets.
    -o OUTPUT_DIR, --output_dir OUTPUT_DUR
                            Directory for local copy of output files.
    -t TEXTURE_DIR, --texture_dir TEXTURE_DIR
                            Directory holding texture files for points.
    -v, --verbose         Verbose output.

The input CSV file tells the program what to do. In each dir (mammals_families_species
and mammals_families_orders_species), take a look at the [...]_dataset.csv file.
Each line tells the program which data csv file to load and what to do with it, 
either turn it into stars or labels. If stars, there are a bunch of parameters
to tweak star appearance, and also an option to set an asset name for fading. (This
is a little complicated, just ask me.)

The cache dir is cleaned out automatically, you need to provide its location
on your setup.

The asset dir is where you want the assets placed when run.

** NEED TO CHANGE THIS TO USE MAKEFILES **

Example run:

Note that the paths below need to be modified for your particular setup.

First `cd` into the data dir, for the example below this would be
`catalogs_raw/Nov_26_relaxed_dataset_english_names`. Then run:

`../../csv_to_openspace.py -i Nov_26_mammals_dataset.csv -c /mnt/e/git/OpenSpace/cache -a /mnt/e/OpenSpace/user/data/assets/Nov_26_mammals_dataset -o ./outfiles -t ../../textures`

Then make sure your profile is set up to load the new assets.

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





### `./data/archive`

Archived datasets used in early trial visualizations. Not guaranteed to work properly as
data formats and processing algorithms have changed quite a bit over the course of the
project, so these will not be described in detail.


## `./integrate_tree_to_XYZ`

This git submodule is Wandrille's code to convert Timetree data (`timetree.org`) into
3-dimensional points. Some of the code in `/src` and `make_tree_with_models.py` benefitted
from access to internal data structures in Wandrille's original project, so it was
modified to allow inclusion as a python `import`. 

# Archived stuff

The following directories and programs are outdated. They're all from early incarnations
of the project and various proofs-of-concept.

## `main.py`:

The (original) main function that all other programs are called from. This script has been
partially subsumed by the previous scripts noted above.

The placement of most of the logic in this file allows for a modular style of processing
by commenting and uncommenting function calls to various parts of the code. The scripts
above tend to use parameter files as inputs to direct the scripts as to what data to
process and where to find it. Much of that code is based on the original code in `main.py`
and the `/src` subdirectory.

## `/actions`:

This folder contains some pre-coded actions for insect plots. It's largely outdated,
since now actions are typically created programatically at runtime.



### /catalogs_raw:

All (well, most, but not all) of the raw data after processing by Wandrille. Note that
some datasets added after June 2024 are in various subdirectories noted above.
  

### /src:

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



<!-- ROADMAP
## Roadmap

- [ ] Feature 1
- [ ] Feature 2
- [ ] Feature 3
    - [ ] Nested Feature

See the [open issues](https://github.com/github_username/repo_name/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>
 -->



<!-- CONTRIBUTING
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>
 -->


<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Brian Abbott - abbott@amnh.org

Project Link: [https://github.com/brianpatrick/cosmic-view-life](https://github.com/brianpatrick/cosmic-view-life)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

This project is a joint venture between the [American Museum of Natural History](https://www.amnh.org) in New York, [University of Basel](https://www.unibas.ch/en.html) in Switzerland, and [Linköping University](https://scivis.github.io) in Sweden. It combines two astronomers, two biologists, and data analysis and visiualization experts.

This project is funded by the Richard Lounsbery Foundation.

### Primary players


- [Brian Abbott](https://brianabbott.net) (American Museum of Natural History) Data visualization, astronomer by trade, and author of these codes.
- [Hollister Herhold](https://sites.google.com/view/hollister-herhold) (American Museum of Natural History) Entomologist, former software engineer.
- [Wandrille Duchemin](https://github.com/WandrilleD) (University of Basel & SIB Swiss Institute of Bioinformatics) Biologist & bioinformatics guru
- [Jackie Faherty](https://www.jackiefaherty.com) (American Museum of Natural History) Astrophyscist with a deep interest in data visualization.
- [Takanori Fujiwara](https://takanori-fujiwara.github.io) (Linköping University) Dimensional reduction expert.
- [David Thaler](https://phe.rockefeller.edu/bio/dthaler) (University of Basel & Rockefeller University, New York) Biologist and big thinker.


### Students

Our graduate students are studying at Sweden's University of Linköping. Each student project is an innovative step forward and results in their master's thesis.

#### Advisors

- [Alexander Bock](https://github.com/alexanderbock) (Linköping University)
- [Emma Broman](https://github.com/WeirdRubberDuck) (Linköping University)

#### 2022

- Emma Segolsson
- Linn Storesund

#### 2023
- Märta Nilsson
- Robin Ridell


<p align="right">(<a href="#readme-top">back to top</a>)</p>