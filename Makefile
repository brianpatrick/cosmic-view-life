#
# Cosmic View of Life Makefile
#

# Scripts sit in the root directory of the repository but are run in
# the directory holding the data.
REPO_PATH := $(shell pwd)

# Important paths. Tweak as needed for your system.
OPENSPACE_CACHE := /mnt/e/git/OpenSpace-sonification/cache
OPENSPACE_ASSET_DIR := /mnt/e/OpenSpace/user/data/assets

mammals_nov_26:
	@echo "Building Mammals"
	@cd catalogs_raw/Nov_26_relaxed_dataset_english_names; \
	python ${REPO_PATH}/csv_to_openspace.py -i Nov_26_mammals_dataset.csv \
	-c ${OPENSPACE_CACHE} \
	-a ${OPENSPACE_ASSET_DIR}/Nov_26_mammals_dataset \
	-o ./outfiles -t ${REPO_PATH}/textures

birds_Jan_2025:
	@echo "Building Birds"
	@cd catalogs_raw/birds/Jan_2025_birds; \
	python ${REPO_PATH}/csv_to_openspace.py -i Jan_2025_birds_dataset.csv \
	-c ${OPENSPACE_CACHE} \
	-a ${OPENSPACE_ASSET_DIR}/Jan_2025_birds_dataset \
	-o ./outfiles -t ${REPO_PATH}/textures

