#
# Cosmic View of Life Makefile
#

# Scripts sit in the root directory of the repository but are run in
# the directory holding the data.
REPO_PATH := $(shell pwd)

# Important paths. Tweak as needed for your system.
OPENSPACE_CACHE := /mnt/e/git/OpenSpace-sonification/cache
OPENSPACE_ASSET_DIR := /mnt/e/OpenSpace/user/data/assets

clean_mammals_nov_26:
	@echo "*** Cleaning ${OPENSPACE_CACHE} of files in ${OPENSPACE_ASSET_DIR}/Nov_26_mammals_dataset"
	python clean_openspace_cache.py -c ${OPENSPACE_CACHE} \
	-a ${OPENSPACE_ASSET_DIR}/Nov_26_mammals_dataset
mammals_nov_26: clean_mammals_nov_26
	@echo "*** Building Mammals"
	@cd catalogs_raw/Nov_26_relaxed_dataset_english_names; \
	python ${REPO_PATH}/csv_to_openspace.py -i Nov_26_mammals_dataset.csv \
	-c ${OPENSPACE_CACHE} \
	-a ${OPENSPACE_ASSET_DIR}/Nov_26_mammals_dataset \
	-o ./outfiles -t ${REPO_PATH}/textures

clean_birds_Jan_2025:
	@echo "*** Cleaning ${OPENSPACE_CACHE} of files in ${OPENSPACE_ASSET_DIR}/Jan_2025_birds_dataset"
	python clean_openspace_cache.py -c ${OPENSPACE_CACHE} \
	-a ${OPENSPACE_ASSET_DIR}/Jan_2025_birds_dataset -v
birds_Jan_2025: clean_birds_Jan_2025
	@echo "*** Building Birds"
	@cd catalogs_raw/birds/Jan_2025_birds; \
	python ${REPO_PATH}/csv_to_openspace.py -i Jan_2025_birds_dataset.csv \
	-c ${OPENSPACE_CACHE} \
	-a ${OPENSPACE_ASSET_DIR}/Jan_2025_birds_dataset \
	-o ./outfiles -t ${REPO_PATH}/textures

# There are two ways to make trees, one is to use a JSON parameter file and the
# other is to provide args on the command line. This uses command line args.
clean_insect_tree_with_models:
	@echo "*** Cleaning ${OPENSPACE_CACHE} of files in ${OPENSPACE_ASSET_DIR}/insect_tree_with_models"
	python clean_openspace_cache.py -c ${OPENSPACE_CACHE} \
	-a ${OPENSPACE_ASSET_DIR}/insect_tree_with_models -v
insect_tree_with_models: clean_insect_tree_with_models
	python ${REPO_PATH}/make_tree_with_models.py \
	-i 'tree_input_files/Insect relationships from Misof et al.nwk' \
	-m 'tree_input_files/misof_insect_models.csv' \
	-o ${OPENSPACE_ASSET_DIR}/insect_tree_with_models \
	-n 'Insect_tree' \
	--branch_scaling_factor 50.0 \
	--taxon_scaling_factor 50.0 \
	--diagonal

