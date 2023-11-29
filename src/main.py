'''
Cosmic View of Life on Earth

The main script for processing the Cosmic View of Life on Earth project.

This reads in the raw data and processes speck, label, color map, and asset files ready for OpenSpace.
Main steps include reading and passing the metadata, processing the consensus species data, 
and processing the DNA sequence data. 

Author: Brian Abbott <abbott@amnh.org>
Created: September 2022
'''

#from mimetypes import guess_all_extensions
import pandas as pd
from pathlib import Path
#import shutil
#import os

import common, colors, human_origins, metadata, consensus_species, sequence, sequence_lineage, slice_by_taxon, slice_by_clade, slice_by_lineage, takanori_trials, tree
#import  


def main():
    '''
    Process the DNA sequence data for the Cosmic View of Life on Earth project.

    Reads the common name vocabulary, then consists of a series of blocks for a particular class.
    In each block, we define some info about the datasets, we then process the metadata, 
    the consensus species data, and the sequence data.

    The datainfo dictionary floats through all modules. Its keys (all strings except where noted) are:
        project                 'Cosmic View of Life on Earth'
        sub_project             'Primates', 'Birds', etc.
        reference               The data ref
        author                  Authors of this project and affiliations
        version                 Version of the data (whole numbers)

        dir                     Directory of the sub_project, 'primates', 'birds', 'human_origins', etc.
        catalog_directory       Raw data version folder, often things like 'Version_1__2022_07_05'

        metadata_file           Name of the raw metadata file
        consensus_file          Name of the consensus species raw data file
        sequence_file           Name of the raw DNA sequence data file
        seq2taxon_file          File that matches sequence number and the taxon name
        synonomous_file         Synonomous / Non-synonomous data file
        lineage_columns         The range of lineage columns we want to sample for the final data. Format: [int, int]
        
        data_group_title        The name of the subdata group, usually datainfo[sub_project] + 'a short title'
        data_group_desc         A longer description of the data group.
    '''


    # Define some universal metadata
    datainfo = {}

    datainfo['project'] = 'Cosmic View of Life on Earth'
    datainfo['reference'] = 'Wandrille Duchemin (University of Basel & SIB Swiss Institute of Bioinformatics), Barcode Of Life Database'
    datainfo['author'] = 'Brian Abbott (American Museum of Natural History, New York), Wandrille Duchemin (University of Basel & SIB Swiss Institute of Bioinformatics), Jackie Faherty (American Museum of Natural History, New York), David Thaler (University of Basel, Switzerland & Rockefeller University, New York)'


    # Copy the viz assets file to each subproject folder.Define the path to the source file here.
    # sourcePath = Path.cwd() / 'viz_assets' / 'point3A.png'
    


    # Make the color table
    # (This is commented out because it's run once, but it's here for completeness)
    # -----------------------------------------------------------------------------------
    #make_color_tables(datainfo)


    # Open the taxonomy vocabulary file, this correlates the taxon with the common name
    # -----------------------------------------------------------------------------------
    vocab = vocabulary(datainfo)


    # Human origin / population DNA data
    # -----------------------------------------------------------------------------------
    #origins(datainfo)
    



    # Primates
    # ------------------------------------------------------------------------

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
    #primates(datainfo, vocab)


    # datainfo['version'] = '1'
    # datainfo['catalog_directory'] = 'UMAP_v1'
    # datainfo['metadata_file'] = 'primates.taxons.metadata.csv'
    # datainfo['consensus_file'] = 'pumap_taxon.csv'
    # datainfo['sequence_file'] = 'pumap_taxon_allpoints.csv'
    # datainfo['seq2taxon_file'] = 'primates.seqId2taxon.csv'
    # datainfo['synonomous_file'] = 'primates.syn.nonsyn.distToHumanConsensus.csv'
    # datainfo['lineage_columns'] = [24, 31]

    # # Preprocess the consensus file to get the right format
    # new_consensus_filename = src.common.pre_process_takanori_consensus(datainfo)
    # datainfo['consensus_file'] = new_consensus_filename

    # # Process the sequence data file to fet the right format
    # new_seq_filename = src.common.pre_process_takanori_seq(datainfo)
    # datainfo['sequence_file'] = new_seq_filename

    # primates(datainfo, vocab)



    
    # Birds
    # ------------------------------------------------------------------------
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
    #birds(datainfo, vocab)

    # datainfo['version'] = '2'
    # datainfo['catalog_directory'] = 'UMAP_v1'
    # datainfo['metadata_file'] = 'aves.taxons.metadata.csv'
    # datainfo['consensus_file'] = 'aves.cleaned.species.PUMAP.euclidean.primates_scale_ver1.csv'
    # datainfo['sequence_file'] = 'aves.cleaned.seq_speciesRef.PUMAP.euclidean.primates_scale_ver1.csv'
    # datainfo['seq2taxon_file'] = 'aves.seqId2taxon.csv'
    # datainfo['synonomous_file'] = None
    # datainfo['lineage_columns'] = [27, 34]
    # birds(datainfo, vocab)

    datainfo['version'] = '3'
    datainfo['catalog_directory'] = 'UMAP_v2'
    datainfo['metadata_file'] = 'aves.taxons.metadata.csv'
    datainfo['consensus_file'] = 'aves.cleaned.species.PUMAP.euclidean.primates_scale_ver2.csv'
    datainfo['sequence_file'] = 'aves.cleaned.seq_speciesRef.PUMAP.euclidean.primates_scale_ver2.csv'
    datainfo['seq2taxon_file'] = 'aves.seqId2taxon.csv'
    datainfo['synonomous_file'] = None
    datainfo['lineage_columns'] = [27, 34]
    birds(datainfo, vocab)







def make_color_tables(datainfo):
    '''
    Make the refined color table from the scraped HTML list
    The result is a .dat file of chosen colors we can tap for other scripts.
    '''

    datainfo['version'] = '1'
    datainfo['catalog_directory'] = 'crayola'

    common.print_head_status('color table')

    colors.crayola_color_table(datainfo)




def vocabulary(datainfo):
    '''
    Read the species vocabulary file (common name to taxon)
    and pass to the various functions below.
    '''

    datainfo['version'] = '1'
    datainfo['catalog_directory'] = 'Version_1__2022_07_05'

    infile_vocab_path = Path.cwd() / common.DATA_DIRECTORY / common.VOCAB_DIRECTORY / datainfo['catalog_directory'] / 'Animal_taxonomic_vocabulary_common_names.tsv'
    common.test_input_file(infile_vocab_path)
    vocab = pd.read_csv(infile_vocab_path, sep='\t')

    return vocab





def origins(datainfo):
    '''
    This processes the human origins data.
    '''

    datainfo['sub_project'] = 'Human Origins'
    datainfo['version'] = '1'

    datainfo['dir'] = datainfo['sub_project'].replace(' ', '_').lower()
    datainfo['catalog_directory'] = 'Version_1__2022_05_22'
    datainfo['sequence_file'] = 'patterson2012_humanPopulations_allSNPs.mMDS.noOutliers.xyz.reProjected.csv'

    common.print_head_status(datainfo['sub_project'])

    human_origins.seq_populations(datainfo)
    human_origins.make_asset_all(datainfo)
    human_origins.make_asset_regions(datainfo)




def primates(datainfo, vocab):
    '''
    Process the primates data. Run these functions for metadata processing, the consensus species,
    and the sequence data. All the speck, label, color map, and asset files are generated.
    '''

    common.print_head_status(datainfo['sub_project'])


    meta_data = metadata.process_data(datainfo)


    consensus = consensus_species.process_data(datainfo, vocab)
    consensus_species.make_asset(datainfo)


    seq = sequence.process_data(datainfo, meta_data)
    sequence.make_asset(datainfo)

    sequence_lineage.process_data(datainfo, consensus, seq)
    sequence_lineage.make_asset(datainfo)



    # Process the tree of primates
    # NOTE: need to run the ./catalogs_raw/primates/tree/integrate_tree_to_XYZ.py, see the readme file there.
    tree.process_data(datainfo)
    tree.process_branches(datainfo)
    tree.make_asset_branches(datainfo)

    


    # common.print_subhead_status('Processing individual clades')
    slice_by_clade.process_data(datainfo, 'Homo')       # fellow peeps, neanderthal, denisovan
    slice_by_clade.process_data(datainfo, 'Pan')        # chimps
    slice_by_clade.process_data(datainfo, 'Gorilla')    # gorillas
    slice_by_clade.process_data(datainfo, 'Pongo')      # orangutans
    slice_by_clade.process_data(datainfo, 'Lemur')
    slice_by_clade.make_asset(datainfo)


    # common.print_subhead_status('Processing traced lineage branch files')
    slice_by_lineage.process_data(datainfo, 'Homo sapiens')
    slice_by_lineage.make_asset(datainfo, 'Homo sapiens')

    # # slice_by_lineage.process_data(datainfo, 'Lemur catta')
    # # slice_by_lineage.make_asset(datainfo, 'Lemur catta')


    # common.print_subhead_status('Processing individual taxon/species files')
    slice_by_taxon.process_data(datainfo, 'Homo sapiens')
    slice_by_taxon.process_data(datainfo, 'Macaca')
    slice_by_taxon.make_asset(datainfo)


    takanori_trials.process_data(datainfo, seq)
    takanori_trials.make_asset(datainfo)
   
    print()
    




def birds(datainfo, vocab):
    '''
    Process the birds data. Run three functions for metadata processing, the consensus species,
    and the sequence data. All the speck, label, color map, and asset files are generated.
    '''

    common.print_head_status(datainfo['sub_project'])


    meta_data = metadata.process_data(datainfo)


    consensus = consensus_species.process_data(datainfo, vocab)
    consensus_species.make_asset(datainfo)


    seq = sequence.process_data(datainfo, meta_data)
    sequence.make_asset(datainfo)

    sequence_lineage.process_data(datainfo, consensus, seq)
    sequence_lineage.make_asset(datainfo)


    common.print_subhead_status('Processing individual clades')
    slice_by_clade.process_data(datainfo, 'Anas')   # 33084
    slice_by_clade.make_asset(datainfo)



    common.print_subhead_status('Processing traced lineage branch files')
    slice_by_lineage.process_data(datainfo, 'Anas')
    slice_by_lineage.make_asset(datainfo, 'Anas')

    slice_by_lineage.process_data(datainfo, 'Columba')
    slice_by_lineage.make_asset(datainfo, 'Columba')





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


    print()



if __name__ == "__main__":
    main()