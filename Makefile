#
# Cosmic View of Life Makefile
#


repo_path := $(shell pwd)

mammals_nov_26:
	@echo "Building Mammals"
	@cd catalogs_raw/Nov_26_relaxed_dataset_english_names; python ${repo_path}/csv_to_openspace.py -i Nov_26_mammals_dataset.csv -c /mnt/e/git/OpenSpace/cache -a /mnt/e/OpenSpace/user/data/assets/Nov_26_mammals_dataset -o ./outfiles -t ${repo_path}/textures

birds_Jan_2025:
	@echo "Building Birds"
	@cd catalogs_raw/birds/Jan_2025_birds; python ${repo_path}/csv_to_openspace.py -i Jan_2025_birds_dataset.csv -c /mnt/e/git/OpenSpace/cache -a /mnt/e/OpenSpace/user/data/assets/Jan_2025_birds_dataset -o ./outfiles -t ${repo_path}/textures

