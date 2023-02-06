<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->
<a name="readme-top"></a>





<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/brianpatrick/cosmic-view-life">
    <!-- <img src="images/logo.png" alt="Logo" width="80" height="80"> -->
  </a>

<h3 align="center">Cosmic View of Life on Earth</h3>

  <p align="center">
    A project to create a 3-D tree of life based on DNA samples from the BOLD database.
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
## About The Project

<!-- [![Product Name Screen Shot][product-screenshot]](https://example.com) -->

This project endeavors to create a 3-D tree of life based on DNA samples from the BOLD database. Based on these samples, we dimensionally reduce each DNA sample down to three. We then plot these data in [OpenSpace]() to examine the relationship between species and their lineage.
<br />
This project is in its nacient stages. Thus far, we have exampined the primates, and are beginning to examing other divisions of life, including birds.

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
## Organization

The repository is organized into by following directory structure:


### /main.py:

The main function that all other programs are called from. This allows for a modular style of processing by commenting and uncommenting function calls to various parts of the code.


### /catalogs_raw:

All the raw data after processing by Wandrille 
  

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