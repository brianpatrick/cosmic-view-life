: This batch file is meant to kinda-sorta emulate the makefile. The original Makefile
: is not very intelligent in that it does not really check for dependencies.
: Because it runs on Linux, it winds up being very slow as WSL's file access to
: Windows is slow.

: Turn off echoing commands
@echo off

: Set the repo path to the current directory. We use this later to find paths to the
: executables.
set REPO_PATH=%~dp0

: Use a command line argument to determine what to build so that this works
: more like a makefile.

IF "%1"=="faherty_apr_23" (
    echo Cleaning up OpenSpace cache and assets...
    python .\clean_openspace_cache.py -c E:\git\OpenSpace\cache\ -a E:\OpenSpace\user\data\assets\faherty_apr_23

    cd data/Jan_30_2025_recentered
    python %REPO_PATH%/group_dataset.py -i eukaryotes_classes.csv -c kingdom
    cd %REPO_PATH%

    cd data/Jan_30_2025_recentered
    python %REPO_PATH%/csv_to_openspace.py -i faherty_apr_23.json -a E:\OpenSpace\user\data\assets\faherty_apr_23 -o ./outfiles_faherty_apr_23 -t E:\git\cosmic-view-life\textures

) ELSE IF "%1"=="jan_30_2025_recentered" (
    echo Cleaning up OpenSpace cache and assets...
    python .\clean_openspace_cache.py -c E:\git\OpenSpace\cache\ -a E:\OpenSpace\user\data\assets\Jan_30_2025_recentered

    cd data/Jan_30_2025_recentered
    python %REPO_PATH%/group_dataset.py -i eukaryotes_classes.csv -c kingdom
    python %REPO_PATH%/group_dataset.py -i eukaryotes_classes.csv -c class
    python %REPO_PATH%/group_dataset.py -i eukaryotes_classes.csv -c class_eng
    cd %REPO_PATH%

    cd data/Jan_30_2025_recentered
    python %REPO_PATH%/csv_to_openspace.py -i jan_30_2025_recentered.json -a E:\OpenSpace\user\data\assets\jan_30_2025_recentered -o ./outfiles_jan_30_2025_recentered -t E:\git\cosmic-view-life\textures

) ELSE IF "%1"=="may_12" (
    echo Cleaning up OpenSpace cache and assets...
    python .\clean_openspace_cache.py -c E:\git\OpenSpace\cache\ -a E:\OpenSpace\user\data\assets\may_12

    echo Making grouped datasets...
    cd data/Jan_30_2025_recentered
    python %REPO_PATH%/group_dataset.py -i eukaryotes_classes.csv -c kingdom
    python %REPO_PATH%/group_dataset.py -i eukaryotes_classes.csv -c class
    cd %REPO_PATH%

    echo Making May 12 assets...
    cd data/Jan_30_2025_recentered
    python %REPO_PATH%/csv_to_openspace.py -i may_12.json -a E:\OpenSpace\user\data\assets\may_12 -o ./outfiles_may_12 -t E:\git\cosmic-view-life\textures

) ELSE IF "%1"=="testbed" (
    echo Cleaning up OpenSpace cache and assets...
    python .\clean_openspace_cache.py -c E:\git\OpenSpace\cache\ -a E:\OpenSpace\user\data\assets\testbed

    echo Making grouped datasets...
    cd data/Jan_30_2025_recentered
    python %REPO_PATH%/group_dataset.py -i eukaryotes_classes.csv -c kingdom
    python %REPO_PATH%/group_dataset.py -i eukaryotes_classes.csv -c class
    cd %REPO_PATH%

    echo Making testbed assets...
    cd data/Jan_30_2025_recentered
    python %REPO_PATH%/csv_to_openspace.py -i testbed.json -a E:\OpenSpace\user\data\assets\testbed -o ./outfiles_testbed -t E:\git\cosmic-view-life\textures
) ELSE (
    echo ***** No valid target passed. Please pass a valid target. *****
    echo ***** Valid targets are: faherty_apr_23, jan_30_2025_recentered, may_12, testbed *****
    echo ***** Example: make.bat jan_30_2025_recentered *****
)
