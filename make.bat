: This batch file is meant to kinda-sorta emulate the makefile. The original Makefile
: is not very intelligent in that it does not really check for dependencies.
: Because it runs on Linux, it winds up being very slow as WSL's file access to
: Windows is slow.

: Turn off echoing commands
@echo off

: Set the repo path to the current directory. We use this to find various scripts.
set REPO_PATH=%~dp0

: makebat.config is required. It should set the local OpenSpace executable dir 
: and the OpenSpace data dir, for example:
:
: set OPENSPACE_EXE_DIR=C:\Users\hherhold\git\OpenSpace
: set OPENSPACE_DATA_DIR=C:\OpenSpace\user\data
:
: We use these to clean up the OpenSpace cache and install the assets.
if not exist makebat_config.bat (
    echo ***** makebat_config.bat not found. Please create it with the required variables. *****
    echo ***** See the comments in make.bat for details. *****
    exit /b 1
)
call makebat_config.bat

: Use a command line argument (%1) to determine what to build so that this works
: more like a makefile.

IF "%1"=="faherty_apr_23" (
    echo Cleaning up OpenSpace cache and assets...
    python .\clean_openspace_cache.py -c %OPENSPACE_EXE_DIR%\cache\ -a %OPENSPACE_DATA_DIR%\assets\faherty_apr_23

    cd data/Jan_30_2025_recentered
    python %REPO_PATH%/group_dataset.py -i eukaryotes_classes.csv -c kingdom
    cd %REPO_PATH%

    cd data/Jan_30_2025_recentered
    python %REPO_PATH%/csv_to_openspace.py -i faherty_apr_23.json -a %OPENSPACE_DATA_DIR%\assets\faherty_apr_23 -o ./outfiles_faherty_apr_23 -t %REPO_PATH%\textures

) ELSE IF "%1"=="jan_30_2025_recentered" (
    echo Cleaning up OpenSpace cache and assets...
    python .\clean_openspace_cache.py -c %OPENSPACE_EXE_DIR%\cache\ -a %OPENSPACE_DATA_DIR%\assets\Jan_30_2025_recentered

    cd data/Jan_30_2025_recentered
    python %REPO_PATH%/group_dataset.py -i eukaryotes_classes.csv -c kingdom
    python %REPO_PATH%/group_dataset.py -i eukaryotes_classes.csv -c class
    python %REPO_PATH%/group_dataset.py -i eukaryotes_classes.csv -c class_eng
    cd %REPO_PATH%

    cd data/Jan_30_2025_recentered
    python %REPO_PATH%/csv_to_openspace.py -i jan_30_2025_recentered.json -a %OPENSPACE_DATA_DIR%\assets\jan_30_2025_recentered -o ./outfiles_jan_30_2025_recentered -t %REPO_PATH%\textures

) ELSE IF "%1"=="may_12" (
    echo Cleaning up OpenSpace cache and assets...
    python .\clean_openspace_cache.py -c %OPENSPACE_EXE_DIR%\cache\ -a %OPENSPACE_DATA_DIR%\assets\may_12

    echo Making grouped datasets...
    cd data/Jan_30_2025_recentered
    python %REPO_PATH%/group_dataset.py -i eukaryotes_classes.csv -c kingdom
    python %REPO_PATH%/group_dataset.py -i eukaryotes_classes.csv -c class
    cd %REPO_PATH%

    echo Making May 12 assets...
    cd data/Jan_30_2025_recentered
    python %REPO_PATH%/csv_to_openspace.py -i may_12.json -a %OPENSPACE_DATA_DIR%\assets\may_12 -o ./outfiles_may_12 -t %REPO_PATH%\textures

) ELSE IF "%1"=="may_28" (
    echo Cleaning up OpenSpace cache and assets...
    python .\clean_openspace_cache.py -c %OPENSPACE_EXE_DIR%\cache\ -a %OPENSPACE_DATA_DIR%\assets\may_28

    echo Making grouped datasets...
    cd data/Jan_30_2025_recentered
    python %REPO_PATH%/group_dataset.py -i eukaryotes_classes.csv -c kingdom
    python %REPO_PATH%/group_dataset.py -i eukaryotes_classes.csv -c class
    cd %REPO_PATH%

    echo Making May 28 assets...
    cd data/Jan_30_2025_recentered
    python %REPO_PATH%/csv_to_openspace.py -i may_28.json -a %OPENSPACE_DATA_DIR%\assets\may_28 -o ./outfiles_may_28 -t %REPO_PATH%\textures

) ELSE IF "%1"=="testbed" (
    echo Cleaning up OpenSpace cache and assets...
    python .\clean_openspace_cache.py -c %OPENSPACE_EXE_DIR%\cache\ -a %OPENSPACE_DATA_DIR%\assets\testbed

    echo Making grouped datasets...
    cd data/Jan_30_2025_recentered
    python %REPO_PATH%/group_dataset.py -i eukaryotes_classes.csv -c kingdom
    python %REPO_PATH%/group_dataset.py -i eukaryotes_classes.csv -c class
    python %REPO_PATH%/group_dataset.py -i insect_genus_tree_mMDS.csv -c order
    cd %REPO_PATH%

    echo Making testbed assets...
    cd data/Jan_30_2025_recentered
    python %REPO_PATH%/csv_to_openspace.py -i testbed.json -a %OPENSPACE_DATA_DIR%\assets\testbed -o ./outfiles_testbed -t %REPO_PATH%\textures

) ELSE IF "%1"=="astc" (
    echo Cleaning up OpenSpace cache and assets...
    python .\clean_openspace_cache.py -c %OPENSPACE_EXE_DIR%\cache\ -a %OPENSPACE_DATA_DIR%\assets\astc

    echo Making grouped datasets...
    cd data/Jan_30_2025_recentered
    python %REPO_PATH%/group_dataset.py -i eukaryotes_classes.csv -c kingdom
    python %REPO_PATH%/group_dataset.py -i eukaryotes_classes.csv -c class
    cd %REPO_PATH%

    echo Making ASTC assets...
    cd data/Jan_30_2025_recentered
    python %REPO_PATH%/csv_to_openspace.py -i astc.json -a %OPENSPACE_DATA_DIR%\assets\astc -o ./outfiles_astc -t %REPO_PATH%\textures

) ELSE (
    echo ***** No valid target passed. Please pass a valid target. *****
    echo ***** Valid targets are: faherty_apr_23, jan_30_2025_recentered, may_12, may_28, testbed, astc *****
    echo ***** Example: make.bat jan_30_2025_recentered *****
)
echo.
echo ***** Done. *****
echo.

: Exit the script
exit /b 0
