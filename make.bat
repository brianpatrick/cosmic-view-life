: This batch file is meant to kinda-sorta emulate the makefile. The original Makefile
: is not very intelligent in that it does not really check for dependencies.
: Because it runs on Linux, it winds up being very slow as WSL's file access to
: Windows is slow.

: Set the repo path to the current directory. We use this later to find paths to the
: executables.
set REPO_PATH=%~dp0

echo %REPO_PATH%

echo Cleaning up OpenSpace cache and assets...
python .\clean_openspace_cache.py -c E:\git\OpenSpace\cache\ -a E:\OpenSpace\user\data\assets\faherty_apr_23

cd data/Jan_30_2025_recentered
python %REPO_PATH%/group_dataset.py -i eukaryotes_classes.csv -c kingdom
cd %REPO_PATH%

cd data/Jan_30_2025_recentered
python %REPO_PATH%/csv_to_openspace.py -i faherty_apr_23.json -a E:\OpenSpace\user\data\assets\faherty_apr_23 -o ./outfiles_faherty_apr_23 -t E:\git\cosmic-view-life\textures