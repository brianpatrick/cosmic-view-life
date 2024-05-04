# Cosmic View of Life on Earth
#
# Author: Brian Abbott <abbott@amnh.org>
# Created: September 2022
"""

This module contains insect-specific code for the Cosmic View of Life on Earth project. 

A number of different modules need to access insect-specific taxonomic (and other) data,
and this class provides a central location for that data.

"""

import taxidTools

class insects:
    def __init__(self, taxon_dump_dir):
        self.taxon_dump_dir = taxon_dump_dir
        self.taxidTools = None
        pass

    def get_taxidTools(self):
        if self.taxidTools is None:
            print("Loading NCBI taxonomy data...", end="")
            sys.stdout.flush()
            self.taxidTools = taxidTools.Taxonomy.from_taxdump(f"{args.taxdump}/nodes.dmp", 
                                                            f"{args.taxdump}/rankedlineage.dmp")
            print("done.")
        return self.taxidTools


    def get_color_index(taxon):
        """_summary_

        Args:
            taxon (_type_): _description_
        """


    def get_insect_order_colors():
        """
        Returns a dictionary of insect orders and their associated colors.
        """
        pass

        def get_insect_order(taxon):
            """
            Returns the order of the given taxon.
            """
            pass