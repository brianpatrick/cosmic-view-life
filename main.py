# Cosmic View of Life on Earth
#
# Author: Brian Abbott <abbott@amnh.org>
# Created: September 2022


import pandas as pd
from pathlib import Path

import argparse


from src import common, colors, human_origins, metadata, consensus_species, sequence, sequence_lineage, slice_by_taxon, slice_by_clade, slice_by_lineage, takanori_trials, tree


def main():
    """
    The main script for processing the Cosmic View of Life on Earth project.
    
    All runs are designed to occur through this ``main()`` function, from which all
    modules and functions are all called. For a particular run, comment out those module
    calls you do not want to process (e.g., you want to process the birds but not the
    primates, then comment out the calls to the primates function).

    Each area of the tree of life is designed to be run through these modules. The
    process, generally, is to generate a color map (which need only be done once), read
    the common name vocabulary, then process the various orders of the animal kingdom.

    For each of those orders (primates, birds, etc.), we define some info about the
    dataset, process the metadata, then the consensus species data, and finally the
    sequence data. We also have modules that generate subsets of data based on lineage or
    taxon, for example.

    
    The ``datainfo`` global metadata dictionary
    ===============================================================================
    The ``datainfo`` dictionary floats through all modules. Its keys (all strings except
    where noted) define global metadata for a section of the animal kingdom. Entries are
    listed here, and should be updated as new terms are added.   

    =========================== ============================================================
    ``datainfo`` Key             Definition
    =========================== ============================================================
    ``project``                 'Cosmic View of Life on Earth' (constant)
    ``sub_project``             'Primates', 'Birds', etc.
    ``reference``               The data reference in "author, affiliation, source" style
    ``author``                  Authors of this project and affiliations
    ``version``                 Version of the data (whole numbers)
    |
    ``dir``                     Directory of the ``sub_project``, e.g., :file:`primates`, :file:`birds`, :file:`human_origins`, etc.
    ``catalog_directory``       Raw data version folder, often things like :file:`Version_1__2022_07_05`
    |
    ``metadata_file``           Name of the raw metadata file
    ``consensus_file``          Name of the consensus species raw data file
    ``sequence_file``           Name of the raw DNA sequence data file
    ``seq2taxon_file``          File that correlates the sequence number and the taxon name
    ``synonomous_file``         Synonomous / non-synonomous data file
    ``lineage_columns``         The range of lineage columns we want to sample for the final data. Format: [``int``, ``int``]
    |
    ``data_group_title``        The name of the subdata group, usually ``datainfo[sub_project]:`` + 'a short title', e.g. "Primates: Consensus species".
    ``data_group_desc``         A longer description of the data group, of order a few sentences.
    =========================== ============================================================


    Top-level functions
    ===============================================================================
    The first part of ``main()`` is a series of calls to the top-level functions. These
    functions set some metadata and call the data processing modules. Examples of these
    top-level functions include ``origins``, ``primates``, and ``birds``, etc. If you only
    want to process new bird data, then comment out the ``primates`` function.

    Each function here calls the main modules that perform the data processing and output
    generation. These involve calling modules that analyze and generate data for the
    consensus species, the DNA sequence data, the lineage information, and calls modules
    that generate subsets of these data. These modules also generate asset files for
    OpenSpace.

    Similarly, you can comment out modules within these top-level functions to process and
    generate only those portions you'd like. For example, the lineage processing can take
    some time, so unless it's needed commenting out these calls

        :code:`sequence_lineage.process_data(datainfo, consensus, seq)`
        :code:`sequence_lineage.make_asset(datainfo)`

    can be a time saver.


    
    Making color tables
    ---------------------------------------------------------------------------
    .. autofunction:: make_color_tables()

    For more information on making color tables and, ultimately, color map files, see
    :ref:`page-colors`.

    
    Processing species vocabulary
    ---------------------------------------------------------------------------
    .. autofunction:: vocabulary()

    
    Processing human origins
    ---------------------------------------------------------------------------
    .. autofunction:: origins()
        :noindex:
    
    See :ref:`page-human-origins` for more information on the human origins data.

    
    Processing biological orders
    ---------------------------------------------------------------------------

    The main biological orders are processed by a series of modules. Be it birds,
    primates, etc., each order has a function inside :file:`main.py` that calls all of the
    following modules. These modules may be commented out, depending on the needs of your
    run.


    ======================================= ================================= ==============================================
    Module                                   Documentation                     Description
    ======================================= ================================= ==============================================
    :file:`metadata.py`                      :ref:`page-metadata`              .. automodule:: metadata
    :file:`consensus_species.py`             :ref:`page-consensus-species`     .. automodule:: consensus_species
    :file:`sequence.py`                      :ref:`page-sequence`              .. automodule:: sequence
    :file:`sequence_lineage.py`              :ref:`page-sequence-lineage`      .. automodule:: sequence_lineage
    :file:`slice_by_clade.py`                :ref:`page-slice-by-clade`        .. automodule:: slice_by_clade
    :file:`slice_by_lineage.py`              :ref:`page-slice-by-lineage`      .. automodule:: slice_by_lineage
    :file:`slice_by_taxon.py`                :ref:`page-slice-by-taxon`        .. automodule:: slice_by_taxon
    :file:`common.py`                        :ref:`page-common`                .. automodule:: common
    ======================================= ================================= ==============================================    
    """

    # Set up command line parameters. There are only a few parameters right now, but this
    # will likely grow.

    parser = argparse.ArgumentParser(description='Cosmic View of Life on Earth')

    # Command line parameter for whether or not to create directories by default.
    parser.add_argument('--create-dirs', action='store_true', help='Create directories by default', default=False)

    # By default, we run everything. These options allow skipping certain sections.
    parser.add_argument('--all', action='store_true', help='Process all data')

    # Add an argument that takes a list of sections to skip. The sections are primates,
    # birds, human-origins, and insects. This is a bit more flexible than the above
    # options, but it's more complex to use.
    parser.add_argument('--skip', nargs='+', help='Skip sections: primates, birds, human-origins, insects')


    # Check to see if the user has passed in any command line parameters.
    args = parser.parse_args()

    # If there are no skip arguments, set it to an empty list. This keeps the checks
    # below from throwing an error.
    if not args.skip:
        args.skip = []

    # Set the global variable to create directories by default. This is used in other
    # modules to determine whether or not to create directories, hence its inclusion
    # in common. 
    common.CREATE_DIRS_BY_DEFAULT = args.create_dirs

    # Define some universal metadata
    datainfo = {}

    datainfo['project'] = 'Cosmic View of Life on Earth'
    datainfo['reference'] = 'Wandrille Duchemin (University of Basel & SIB Swiss Institute of Bioinformatics), Barcode Of Life Database'
    datainfo['author'] = 'Brian Abbott (American Museum of Natural History, New York), Wandrille Duchemin (University of Basel & SIB Swiss Institute of Bioinformatics), Jackie Faherty (American Museum of Natural History, New York), David Thaler (University of Basel, Switzerland & Rockefeller University, New York)'

    # Make the color table
    # (This is commented out because it's run once, but it's here for completeness)
    # -----------------------------------------------------------------------------------
    make_color_tables(datainfo)


    # Open the taxonomy vocabulary file, this correlates the taxon with the common name
    # -----------------------------------------------------------------------------------
    vocab = vocabulary(datainfo)

    #"""
    # Human origin / population DNA data
    # -----------------------------------------------------------------------------------
    if ("human_origins" not in args.skip):
        datainfo['sub_project'] = 'Human Origins'
        datainfo['version'] = '1'

        datainfo['dir'] = datainfo['sub_project'].replace(' ', '_').lower()
        datainfo['catalog_directory'] = 'Version_1__2022_05_22'
        datainfo['sequence_file'] = 'patterson2012_humanPopulations_allSNPs.mMDS.noOutliers.xyz.reProjected.csv'


        origins(datainfo)
    



    # Primates
    # ------------------------------------------------------------------------
    if ('primates' not in args.skip):
        datainfo['dir'] = 'primates'
        datainfo['sub_project'] = 'Primates'

        datainfo['version'] = '1'
        datainfo['catalog_directory'] = 'MDS_v1'
        datainfo['metadata_file'] = 'primates.taxons.metadata.csv'
        datainfo['consensus_file'] = 'primates.cleaned.species.MDS.euclidean.csv'
        datainfo['sequence_file'] = 'primates.cleaned.seq_speciesRef.gowerIntepolatedMDS.euclidean.csv'
        datainfo['seq2taxon_file'] = 'primates.seqId2taxon.csv'
        datainfo['synonomous_file'] = 'primates.syn.nonsyn.distToHumanConsensus.csv'
        datainfo['lineage_columns'] = [24, 31]
        datainfo['tree_dir'] = 'tree'

        datainfo['newick_file'] = 'Primates.curated.timetree.withInternalName.nwk'
        datainfo['coordinates_file'] = 'primates_species.xy.csv'

        datainfo['tree_leaves_file'] = 'primates.leaves.csv'
        datainfo['tree_branches_file'] = 'primates.branches.csv'
        datainfo['tree_internal_file'] = 'primates.internal.csv'

        datainfo['transform_tree_z'] = 0.0 # 133.5
        datainfo['translate_leaves_z'] = 0 #50.0
        datainfo['scale_tree_z'] = 75.0

        primates(datainfo, vocab)

        datainfo['version'] = '1'
        datainfo['catalog_directory'] = 'UMAP_v1'
        datainfo['metadata_file'] = 'primates.taxons.metadata.csv'
        datainfo['consensus_file'] = 'pumap_taxon.csv'
        datainfo['sequence_file'] = 'pumap_taxon_allpoints.csv'
        datainfo['seq2taxon_file'] = 'primates.seqId2taxon.csv'
        datainfo['synonomous_file'] = 'primates.syn.nonsyn.distToHumanConsensus.csv'
        datainfo['lineage_columns'] = [24, 31]

        # Preprocess the consensus file to get the right format
        new_consensus_filename = common.pre_process_takanori_consensus(datainfo)
        datainfo['consensus_file'] = new_consensus_filename

        # Process the sequence data file to fet the right format
        new_seq_filename = common.pre_process_takanori_seq(datainfo)
        datainfo['sequence_file'] = new_seq_filename

        primates(datainfo, vocab)


    # Birds
    # ------------------------------------------------------------------------
    if ('birds' not in args.skip):
        datainfo['dir'] = 'birds'
        datainfo['sub_project'] = 'Birds'

        datainfo['version'] = '1'
        datainfo['catalog_directory'] = 'MDS_v1'
        datainfo['metadata_file'] = 'aves.taxons.metadata.csv'
        datainfo['consensus_file'] = 'aves.cleaned.species.MDS.euclidean.primates_scale.csv'
        datainfo['sequence_file'] = 'aves.cleaned.seq_speciesRef.gowerIntepolatedMDS.euclidean.primates_scale.csv'
        datainfo['seq2taxon_file'] = 'aves.seqId2taxon.csv'
        datainfo['synonomous_file'] = None
        datainfo['lineage_columns'] = [27, 34]
        birds(datainfo, vocab)

        datainfo['version'] = '1'
        datainfo['catalog_directory'] = 'UMAP_v1'
        datainfo['metadata_file'] = 'aves.taxons.metadata.csv'
        datainfo['consensus_file'] = 'aves.cleaned.species.PUMAP.euclidean.primates_scale_ver1.csv'
        datainfo['sequence_file'] = 'aves.cleaned.seq_speciesRef.PUMAP.euclidean.primates_scale_ver1.csv'
        datainfo['seq2taxon_file'] = 'aves.seqId2taxon.csv'
        datainfo['synonomous_file'] = None
        datainfo['lineage_columns'] = [27, 34]
        birds(datainfo, vocab)

        datainfo['version'] = '2'
        datainfo['catalog_directory'] = 'UMAP_v2'
        datainfo['metadata_file'] = 'aves.taxons.metadata.csv'
        datainfo['consensus_file'] = 'aves.cleaned.species.PUMAP.euclidean.primates_scale_ver2.csv'
        datainfo['sequence_file'] = 'aves.cleaned.seq_speciesRef.PUMAP.euclidean.primates_scale_ver2.csv'
        datainfo['seq2taxon_file'] = 'aves.seqId2taxon.csv'
        datainfo['synonomous_file'] = None
        datainfo['lineage_columns'] = [27, 34]
        birds(datainfo, vocab)

        datainfo['version'] = '1'
        datainfo['catalog_directory'] = 'birds_all'
        datainfo['metadata_file'] = 'birds_all.taxons.metadata.csv'
        datainfo['consensus_file'] = 'birds_all.species.3DcMDS.csv'
        datainfo['sequence_file'] = 'birds_all.sequence.3DcMDS.csv'
        datainfo['seq2taxon_file'] = 'birds_all.seqId2taxon.csv'
        datainfo['synonomous_file'] = None
        datainfo['lineage_columns'] = [27, 34]
        birds(datainfo, vocab)

        # The next three datasets are from the 202308 bird dataset. This dataset has 
        # tree data, but no consensus data.
        datainfo['version'] = '1'
        datainfo['catalog_directory'] = '202308_bird_dataset_mMDS.xy_3Dprojection'
        datainfo['metadata_file'] = 'aves.taxons.metadata.csv'
        datainfo['tree_dir'] = '202308_bird_dataset_mMDS.xy_3Dprojection'
        datainfo['tree_leaves_file'] = 'aves_families.divergence_time.mMDS.xy.leaves.csv'
        datainfo['tree_branches_file'] = 'aves_families.divergence_time.mMDS.xy.branches.csv'
        datainfo['tree_internal_file'] = 'aves_families.divergence_time.mMDS.xy.internal.csv'
        datainfo['seq2taxon_file'] = 'aves.seqId2taxon.csv'
        datainfo['lineage_columns'] = [27, 34]
        datainfo['transform_tree_z'] = 0.0 # 75.0
        datainfo['scale_tree_z'] = 1.0
        datainfo['translate_leaves_z'] = 0 #50.0
        birds(datainfo, vocab,
              do_consensus=False, do_sequence=False, do_sequence_lineage=False, 
              do_slice_by_clade=False, do_slice_by_lineage=False, do_slice_by_taxon=False,
              do_tree = True)
        
        datainfo['version'] = '1'
        datainfo['catalog_directory'] = '202308_bird_dataset_mMDS.xyz.sphere_3Dprojection'
        datainfo['metadata_file'] = 'aves.taxons.metadata.csv'
        datainfo['tree_dir'] = '202308_bird_dataset_mMDS.xyz.sphere_3Dprojection'
        datainfo['tree_leaves_file'] = 'aves_families.divergence_time.mMDS.xyz.sphere.leaves.csv'
        datainfo['tree_branches_file'] = 'aves_families.divergence_time.mMDS.xyz.sphere.branches.csv'
        datainfo['tree_internal_file'] = 'aves_families.divergence_time.mMDS.xyz.sphere.internal.csv'
        datainfo['seq2taxon_file'] = 'aves.seqId2taxon.csv'
        datainfo['lineage_columns'] = [27, 34]
        datainfo['transform_tree_z'] = 0.0 #75.0
        datainfo['scale_tree_z'] = 1.0
        datainfo['translate_leaves_z'] = 0 #50.0
        birds(datainfo, vocab,
              do_consensus=False, do_sequence=False, do_sequence_lineage=False, 
              do_slice_by_clade=False, do_slice_by_lineage=False, do_slice_by_taxon=False,
              do_tree = True)

        datainfo['version'] = '1'
        datainfo['catalog_directory'] = '202308_bird_dataset_mMDS.xyz_3Dprojection'
        datainfo['metadata_file'] = 'aves.taxons.metadata.csv'
        datainfo['tree_dir'] = '202308_bird_dataset_mMDS.xyz_3Dprojection'
        datainfo['tree_leaves_file'] = 'aves_families.divergence_time.mMDS.xyz.leaves.csv'
        datainfo['tree_branches_file'] = 'aves_families.divergence_time.mMDS.xyz.branches.csv'
        datainfo['tree_internal_file'] = 'aves_families.divergence_time.mMDS.xyz.internal.csv'
        datainfo['seq2taxon_file'] = 'aves.seqId2taxon.csv'
        datainfo['lineage_columns'] = [27, 34]
        datainfo['transform_tree_z'] = 0.0 # 75.0
        datainfo['scale_tree_z'] = 1.0
        datainfo['translate_leaves_z'] = 0 #50.0
        birds(datainfo, vocab,
              do_consensus=False, do_sequence=False, do_sequence_lineage=False, 
              do_slice_by_clade=False, do_slice_by_lineage=False, do_slice_by_taxon=False,
              do_tree = True)
        


    # Insects
    # ------------------------------------------------------------------------
    # All the datasets below are tree-based, with input data as newick files
    # from timetree.org. The input data here is CSV files that are the result
    # of Wandrille's pipeline, which runs MDS on a distance matrix obtained from
    # the newick files.
    #
    # The insect points here are all color-coded by order, and with the same
    # color scheme. This is a little different than the other datasets, 
    
    if ('insects' not in args.skip):
        datainfo['dir'] = 'insects'
        datainfo['sub_project'] = 'Insects'

        ####################################################
        # Insect order trees. This is fewer points than the family or (hopefully soon
        # to be incorporated) genus level tree.
        ####################################################
        """
        # "Tabletop" 2D tree.
        datainfo['version'] = '1'
        datainfo['catalog_directory'] = 'timetree_insecta_order_mMDS_xy'
        datainfo['tree_dir'] = 'timetree_insecta_order_mMDS_xy'
        datainfo['metadata_file'] = None
        datainfo['tree_leaves_file'] = 'Insecta_order.mMDS.xy.leaves.csv'
        datainfo['tree_branches_file'] = 'Insecta_order.mMDS.xy.branches.csv'
        datainfo['tree_internal_file'] = 'Insecta_order.mMDS.xy.internal.csv'
        datainfo['transform_tree_z'] = 0.0 # 75.0
        datainfo['scale_tree_z'] = 1.0
        datainfo['translate_leaves_z'] = 0 #50.0
        insects(datainfo, vocab, do_tree = True)

        # 3D tree, non-spherical.
        datainfo['version'] = '1'
        datainfo['catalog_directory'] = 'timetree_insecta_order_mMDS_xyz'
        datainfo['tree_dir'] = 'timetree_insecta_order_mMDS_xyz'

        datainfo['newick_file'] = 'Insecta_order.nwk'
        datainfo['coordinates_file'] = 'Insecta_order_mds3.xyz.csv'


        datainfo['tree_leaves_file'] = 'Insecta_order.mMDS3.xyz.leaves.csv'
        datainfo['tree_branches_file'] = 'Insecta_order.mMDS3.xyz.branches.csv'
        datainfo['tree_internal_file'] = 'Insecta_order.mMDS3.xyz.internal.csv'
        datainfo['transform_tree_z'] = 0.0 # 75.0
        datainfo['scale_tree_z'] = 1.0
        datainfo['translate_leaves_z'] = 0 #50.0
        insects(datainfo, vocab, do_tree = True)

        # 3D tree, spherical.
        datainfo['version'] = '1'
        datainfo['catalog_directory'] = 'timetree_insecta_order_mMDS_xyz_spherical'
        datainfo['tree_dir'] = 'timetree_insecta_order_mMDS_xyz_spherical'
        datainfo['tree_leaves_file'] = 'Insecta_order.mMDS3.xyz-spherical.leaves.csv'
        datainfo['tree_branches_file'] = 'Insecta_order.mMDS3.xyz-spherical.branches.csv'
        datainfo['tree_internal_file'] = 'Insecta_order.mMDS3.xyz-spherical.internal.csv'
        datainfo['transform_tree_z'] = 0.0 # 75.0
        datainfo['scale_tree_z'] = 1.0
        datainfo['translate_leaves_z'] = 0 #50.0
        insects(datainfo, vocab, do_tree = True)

        ####################################################
        # Insect family trees. 
        ####################################################

        # "Tabletop" 2D tree.
        datainfo['version'] = '1'
        datainfo['catalog_directory'] = 'timetree_insecta_family_mMDS_xy'
        datainfo['tree_dir'] = 'timetree_insecta_family_mMDS_xy'
        datainfo['metadata_file'] = None
        datainfo['tree_leaves_file'] = 'Insecta_family.mMDS.xy.leaves.csv'
        datainfo['tree_branches_file'] = 'Insecta_family.mMDS.xy.branches.csv'
        datainfo['tree_internal_file'] = 'Insecta_family.mMDS.xy.internal.csv'
        datainfo['transform_tree_z'] = 0.0 # 75.0
        datainfo['scale_tree_z'] = 1.0
        datainfo['translate_leaves_z'] = 0 #50.0
        insects(datainfo, vocab, do_tree = True)
        """
        # 3D tree.
        datainfo['version'] = '1'
        datainfo['catalog_directory'] = 'timetree_insecta_family_mMDS_xyz'
        datainfo['tree_dir'] = 'timetree_insecta_family_mMDS_xyz'
        datainfo['metadata_file'] = 'insecta_family_order_taxonomy.csv'
        
        datainfo['newick_file'] = 'Insecta_family.nwk'
        datainfo['coordinates_file'] = 'Insecta_family_mds3.xyz.csv'

        datainfo['tree_leaves_file'] = 'Insecta_family.mMDS3.xyz.leaves.csv'
        datainfo['tree_branches_file'] = 'Insecta_family.mMDS3.xyz.branches.csv'
        datainfo['tree_internal_file'] = 'Insecta_family.mMDS3.xyz.internal.csv'
        datainfo['transform_tree_z'] = 0.0 # 75.0
        datainfo['scale_tree_z'] = 1.0
        datainfo['translate_leaves_z'] = 0 #50.0
        insects(datainfo, vocab, do_tree = True)
        """
        # 3D tree, spherical.
        datainfo['version'] = '1'
        datainfo['catalog_directory'] = 'timetree_insecta_family_mMDS_xyz_spherical'
        datainfo['tree_dir'] = 'timetree_insecta_family_mMDS_xyz_spherical'
        datainfo['metadata_file'] = 'insecta_family_order_taxonomy.csv'
        datainfo['tree_leaves_file'] = 'Insecta_family.mMDS3.xyz-spherical.leaves.csv'
        datainfo['tree_branches_file'] = 'Insecta_family.mMDS3.xyz-spherical.branches.csv'
        datainfo['tree_internal_file'] = 'Insecta_family.mMDS3.xyz-spherical.internal.csv'
        datainfo['transform_tree_z'] = 0.0 # 75.0
        datainfo['scale_tree_z'] = 1.0
        datainfo['translate_leaves_z'] = 0 #50.0
        insects(datainfo, vocab, do_tree = True)

        
        # The current genus and species trees are from MDS runs that didn't
        # really work.

        ####################################################
        # Insect genus trees.
        ####################################################
        datainfo['version'] = '1'
        datainfo['catalog_directory'] = 'timetree_insecta_genus_mMDS_xyz'
        datainfo['tree_dir'] = 'timetree_insecta_genus_mMDS_xyz'
        datainfo['metadata_file'] = None
        datainfo['tree_leaves_file'] = 'Insecta_genus.mMDS3.xyz.leaves.csv'
        datainfo['tree_branches_file'] = 'Insecta_genus.mMDS3.xyz.branches.csv'
        datainfo['tree_internal_file'] = 'Insecta_genus.mMDS3.xyz.internal.csv'
        datainfo['transform_tree_z'] = 0.0 # 75.0
        datainfo['scale_tree_z'] = 1.0
        datainfo['translate_leaves_z'] = 0 #50.0
        insects(datainfo, vocab, do_tree = True)

        datainfo['version'] = '1'
        datainfo['catalog_directory'] = 'timetree_insecta_genus_mMDS_xyz_spherical'
        datainfo['tree_dir'] = 'timetree_insecta_genus_mMDS_xyz_spherical'
        datainfo['metadata_file'] = None
        datainfo['tree_leaves_file'] = 'Insecta_genus.mMDS3.xyz-spherical.leaves.csv'
        datainfo['tree_branches_file'] = 'Insecta_genus.mMDS3.xyz-spherical.branches.csv'
        datainfo['tree_internal_file'] = 'Insecta_genus.mMDS3.xyz-spherical.internal.csv'
        datainfo['transform_tree_z'] = 0.0 # 75.0
        datainfo['scale_tree_z'] = 1.0
        datainfo['translate_leaves_z'] = 0 #50.0
        insects(datainfo, vocab, do_tree = True)

        ####################################################
        # Insect species trees.
        ####################################################
        datainfo['version'] = '1'
        datainfo['catalog_directory'] = 'timetree_insecta_species_mMDS_xyz'
        datainfo['tree_dir'] = 'timetree_insecta_species_mMDS_xyz'
        datainfo['metadata_file'] = None
        datainfo['tree_leaves_file'] = 'Insecta_species.mMDS3.xyz.leaves.csv'
        datainfo['tree_branches_file'] = 'Insecta_species.mMDS3.xyz.branches.csv'
        datainfo['tree_internal_file'] = 'Insecta_species.mMDS3.xyz.internal.csv'
        datainfo['transform_tree_z'] = 0.0 # 75.0
        datainfo['scale_tree_z'] = 1.0
        datainfo['translate_leaves_z'] = 0 #50.0
        insects(datainfo, vocab, do_tree = True)

        datainfo['version'] = '1'
        datainfo['catalog_directory'] = 'timetree_insecta_species_mMDS_xyz_spherical'
        datainfo['tree_dir'] = 'timetree_insecta_species_mMDS_xyz_spherical'
        datainfo['metadata_file'] = None
        datainfo['tree_leaves_file'] = 'Insecta_species.mMDS3.xyz-spherical.leaves.csv'
        datainfo['tree_branches_file'] = 'Insecta_species.mMDS3.xyz-spherical.branches.csv'
        datainfo['tree_internal_file'] = 'Insecta_species.mMDS3.xyz-spherical.internal.csv'
        datainfo['transform_tree_z'] = 0.0 # 75.0
        datainfo['scale_tree_z'] = 1.0
        datainfo['translate_leaves_z'] = 0 #50.0
        insects(datainfo, vocab, do_tree = True)
        """
        

        """
        datainfo['version'] = '1'
        datainfo['catalog_directory'] = 'Weigmann_et_al_2011'
        datainfo['newick_file'] = 'Wiegmann_et_al.nwk'
        datainfo['tree_dir'] = 'tree'
        insects(datainfo, vocab)
        """



def make_color_tables(datainfo):
    """
    Make a refined color table from a scraped HTML list of colors.

    The result is a ``.dat`` file of chosen colors we can tap for other scripts.

    :param datainfo: Metadata about the dataset.
    :type datainfo: dict of {str : list}
    """

    datainfo['version'] = '1'
    datainfo['catalog_directory'] = 'crayola'

    common.print_head_status('color table')

    colors.crayola_color_table(datainfo)




def vocabulary(datainfo):
    """
    Read the species vocabulary file (common names to taxon key).

    :param datainfo: Metadata about the dataset.
    :type datainfo: dict of {str : list}
    :return: A taxon to common name DataFrame.
    :rtype: DataFrame
    """

    datainfo['version'] = '1'
    datainfo['catalog_directory'] = 'Version_1__2022_07_05'

    infile_vocab_path = Path.cwd() / common.DATA_DIRECTORY / common.VOCAB_DIRECTORY / datainfo['catalog_directory'] / 'Animal_taxonomic_vocabulary_common_names.tsv'
    common.test_input_file(infile_vocab_path)
    vocab = pd.read_csv(infile_vocab_path, sep='\t')

    return vocab





def origins(datainfo):
    """
    Process the human origins data.

    :param datainfo: Metadata about the dataset.
    :type datainfo: dict of {str : list}
    """

    common.print_head_status(datainfo['sub_project'])

    human_origins.seq_populations(datainfo)
    human_origins.make_asset_all(datainfo)
    human_origins.make_asset_regions(datainfo)




def primates(datainfo, vocab, do_tree = False):
    """
    Process the primates data.

    Run these functions for metadata processing, the consensus species,
    and the sequence data. All the speck, label, color map, and asset files are generated.

    :param datainfo: Metadata about the dataset.
    :type datainfo: dict of {str : list}
    :param vocab: A taxon to common name DataFrame.
    :type vocab: DataFrame
    """

    common.print_head_status(datainfo['sub_project'])


    meta_data = metadata.process_data(datainfo)

    # Dump the primate metadata to a file for debug.
    meta_data.to_csv('primates_metadata_debugHH.csv', index=False)

    # HH - The consensus points are a single point for each species. This is most likely
    # the centroid or something like that; I need to look into this more.
    consensus = consensus_species.process_data(datainfo, vocab)
    consensus_species.make_asset(datainfo)


    seq = sequence.process_data(datainfo, meta_data)
    sequence.make_asset(datainfo)

    sequence_lineage.process_data(datainfo, consensus, seq)
    sequence_lineage.make_asset(datainfo)

    # Make a new tree object
    if (do_tree):
        mytree = tree.tree()

        # Process the tree of primates NOTE: need to run the
        # ./catalogs_raw/primates/tree/integrate_tree_to_XYZ.py, see the readme file there.
        # This is a bit hacky in that each part of the tree is handled manually here (leaves,
        # branches, clades), whereas optimally this would all be taken care of in the tree
        # class.

        # Metadata processing is broken for primates and birds for trees.
        datainfo['metadata_file'] = None
        mytree.process_leaves(datainfo)
        mytree.make_asset_nodes(datainfo, 'leaves')
        mytree.process_internal(datainfo)
        mytree.make_asset_nodes(datainfo, 'internal')
        mytree.process_branches(datainfo)
        mytree.make_asset_branches(datainfo)

        # The interpolated points are kinda-sorta associated with the tree, but not really.
        # They are a separate set of points that are interpolated from the leaf points to the
        # data-reduction points. This is to show the relationship between the established
        # evolutionary relationships and the data-reduced points.
        mytree.process_leaves_interpolated(datainfo)
        mytree.make_asset_leaves_interpolated(datainfo)

    


    # common.print_subhead_status('Processing individual clades')
    # slice_by_clade.process_data(datainfo, 'Homo')       # fellow peeps, neanderthal, denisovan
    # slice_by_clade.process_data(datainfo, 'Pan')        # chimps
    # slice_by_clade.process_data(datainfo, 'Gorilla')    # gorillas
    # slice_by_clade.process_data(datainfo, 'Pongo')      # orangutans
    # slice_by_clade.process_data(datainfo, 'Lemur')
    # slice_by_clade.make_asset(datainfo)


    # # common.print_subhead_status('Processing traced lineage branch files')
    # slice_by_lineage.process_data(datainfo, 'Homo sapiens')
    # slice_by_lineage.make_asset(datainfo, 'Homo sapiens')

    # # # slice_by_lineage.process_data(datainfo, 'Lemur catta')
    # # # slice_by_lineage.make_asset(datainfo, 'Lemur catta')


    # # common.print_subhead_status('Processing individual taxon/species files')
    # slice_by_taxon.process_data(datainfo, 'Homo sapiens')
    # slice_by_taxon.process_data(datainfo, 'Macaca')
    # slice_by_taxon.make_asset(datainfo)


    # takanori_trials.process_data(datainfo, seq)
    # takanori_trials.make_asset(datainfo)
   
    print()
    




def birds(datainfo, vocab, 
          do_consensus = True,
          do_sequence  = True,
          do_sequence_lineage = True,
          do_slice_by_clade = True,
          do_slice_by_lineage = True,
          do_slice_by_taxon = True,
          do_tree = False):
    """
    Process the bird data.

    Run three functions for metadata processing, the consensus species,
    and the sequence data. All the speck, label, color map, and asset files are
    generated.

    Not every dataset has the same input data - some have just tree files and not 
    consensus data, or no sequence data, and so on. The input argumets specify 
    which parts of the processing pipeline to run. By default, meaning if no parameters 
    are given, everything is run, EXCEPT for do_tree, as most bird datasets (as of
    this writing, 18 Mar 2024) do not have tree data.

    :param datainfo: Metadata about the dataset.
    :type datainfo: dict of {str : list}
    :param vocab: A taxon to common name DataFrame.
    :type vocab: DataFrame
    """

    common.print_head_status(datainfo['sub_project'])

    # Dump the bird metadata to a file for debug.
    meta_data = metadata.process_data(datainfo)
    meta_data.to_csv('birds_metadata_debugHH.csv', index=False)

    if (do_consensus):
        consensus = consensus_species.process_data(datainfo, vocab)
        consensus_species.make_asset(datainfo)

    if (do_sequence):
        meta_data = metadata.process_data(datainfo)
        seq = sequence.process_data(datainfo, meta_data)
        sequence.make_asset(datainfo)
    
    if (do_sequence_lineage):
        sequence_lineage.process_data(datainfo, consensus, seq)
        sequence_lineage.make_asset(datainfo)

    if (do_slice_by_clade):
        common.print_subhead_status('Processing individual clades')
        slice_by_clade.process_data(datainfo, 'Anas')   # 33084
        slice_by_clade.make_asset(datainfo)

    if (do_slice_by_lineage):
        common.print_subhead_status('Processing traced lineage branch files')
        slice_by_lineage.process_data(datainfo, 'Anas')
        slice_by_lineage.make_asset(datainfo, 'Anas')

        slice_by_lineage.process_data(datainfo, 'Columba')
        slice_by_lineage.make_asset(datainfo, 'Columba')

    if (do_slice_by_taxon):
        common.print_subhead_status('Processing individual taxon/species files')
        slice_by_taxon.process_data(datainfo, 'Turdus migratorius')         # American robin
        slice_by_taxon.process_data(datainfo, 'Cardinalis cardinalis')      # Cardinal
        slice_by_taxon.process_data(datainfo, 'Haliaeetus leucocephalus')   # Bald eagle
        slice_by_taxon.process_data(datainfo, 'Columba livia')              # Rock dove
        slice_by_taxon.process_data(datainfo, 'Anas platyrhynchos')         # Mallard duck
        slice_by_taxon.process_data(datainfo, 'Larus canus')                # Common gull
        slice_by_taxon.make_asset(datainfo)
        # # Sphenisciformes   all penguins
        # # 29001
        # # Passeriformes perching birds

    if (do_tree):

        # Metadata processing is completely broken for the bird datasets. Unset the
        # metadata file so that the tree processing doesn't try to read it.
        datainfo['metadata_file'] = None
        mytree = tree.tree()
        mytree.process_leaves(datainfo)
        mytree.make_asset_nodes(datainfo, 'leaves')
        mytree.process_internal(datainfo)
        mytree.make_asset_nodes(datainfo, 'internal')
        mytree.process_branches(datainfo)
        mytree.make_asset_branches(datainfo)

    print()


def insects(datainfo, vocab, do_tree = True):
    """
    Process the insect data.

    :param datainfo: Metadata about the dataset.
    :type datainfo: dict of {str : list}
    :param vocab: A taxon to common name DataFrame.
    :type vocab: DataFrame

    """

    common.print_head_status(datainfo['sub_project'])

    if (do_tree):
        mytree = tree.tree()
        mytree.process_leaves(datainfo)
        mytree.make_asset_nodes(datainfo, 'leaves')
        mytree.process_internal(datainfo)
        mytree.make_asset_nodes(datainfo, 'internal')
        mytree.process_branches(datainfo)
        mytree.make_asset_branches(datainfo)

    #if (do_tree):
    #    mytree = tree.tree()
    #    mytree.process_newick(datainfo)




def insect_proof_of_concept_tree_taxa():
    """
    This is a proof of concept for the insect data. It's a bit different than the other
    datasets in that the data is not a consensus species or sequence data, but rather a
    series of assets that represent the insects. This is a test to see how the data
    can be used in OpenSpace.
    """

    # This is test code for producing a taxonomic tree. It has hardcoded values
    # for positions and is mainly a proof of concept.

    # Write data to files
    outpath = Path.cwd() / datainfo['dir'] / datainfo['tree_dir']
    common.test_path(outpath)

    def make_insect_asset_file(taxon, position):

        # Position is in m as passed in and needs to be scaled up to km.
        position = [x * 1000 for x in position]

        asset_file = Path.cwd() / datainfo['dir'] / f'{taxon}.asset'
        with open(asset_file, 'w') as f:
            f.write(f'local sun = asset.require("scene/solarsystem/sun/transforms")\n')
            f.write(f'local {taxon} = {{\n')
            f.write(f'    Identifier = "{taxon}",\n')
            f.write(f'    Transform = {{\n')
            f.write(f'        Translation = {{\n')
            f.write(f'            Type = "StaticTranslation",\n')
            f.write(f'            Position = {{ {position[0]}, {position[1]}, {position[2]} }}\n')
            f.write(f'        }}\n')
            f.write(f'    }},\n')
            f.write(f'    Renderable = {{\n')
            f.write(f'        UseCaching = false,\n')
            f.write(f'        Type = "RenderableModel",\n')
            f.write(f'        Coloring = {{\n')
            f.write(f'            FixedColor = {{ 0.8, 0.8, 0.8 }}\n')
            f.write(f'        }},\n')
            f.write(f'        Opacity = 1.0,\n')
            f.write(f'        GeometryFile = asset.resource("Gryllus.obj"),\n')
            f.write(f'        ModelScale = 250,\n')
            f.write(f'        Enabled = true,\n')
            f.write(f'        LightSources = {{\n')
            f.write(f'            sun.LightSource\n')
            f.write(f'        }}\n')
            f.write(f'    }},\n')
            f.write(f'    GUI = {{\n')
            f.write(f'        Name = "{taxon}",\n')
            f.write(f'        Path = "/Leaves",\n')
            f.write(f'    }}\n')
            f.write(f'}}\n')
            f.write(f'asset.onInitialize(function()\n')
            f.write(f'    openspace.addSceneGraphNode({taxon})\n')
            f.write(f'end)\n')
            f.write(f'asset.onDeinitialize(function()\n')
            f.write(f'    openspace.removeSceneGraphNode({taxon})\n')
            f.write(f'end)\n')
            f.write(f'asset.export({taxon})\n')

            # Close the file.
            f.close()



    # Each insect is a separate asset as this is one way to make each of them
    # a SceneGraphNode in OpenSpace. They could all be in one file, but this is
    # a first pass proof of concept.
    make_insect_asset_file('Blattodea', [60, 0, 140])
    make_insect_asset_file('Mantodea', [60, 0, 130])
    make_insect_asset_file('Phasmatodea', [60, 0, 120])
    make_insect_asset_file('Embioptera', [60, 0, 110])
    make_insect_asset_file('Grylloblatta', [60, 0, 100])
    make_insect_asset_file('Mantophasmatodea', [60, 0, 90])
    make_insect_asset_file('Orthoptera', [60, 0, 80])
    make_insect_asset_file('Plecoptera', [60, 0, 70])
    make_insect_asset_file('Dermaptera', [60, 0, 60])
    make_insect_asset_file('Zoraptera', [60, 0, 50])
    make_insect_asset_file('Ephemeroptera', [60, 0, 40])
    make_insect_asset_file('Odonata', [60, 0, 30])
    make_insect_asset_file('Zygentoma', [60, 0, 20])
    make_insect_asset_file('Archaeognatha', [60, 0, 10])


if __name__ == "__main__":
    main()