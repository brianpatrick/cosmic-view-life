: This batch file is meant to kinda-sorta emulate the makefile. The original Makefile
: is not very intelligent in that it does not really check for dependencies.
: Because it runs on Linux, it winds up being very slow as WSL's file access to
: Windows is slow.

: Set the repo path to the current directory. We use this later to find paths to the
: executables.
set REPO_PATH=%~dp0

echo %REPO_PATH%

: Use a command line argument to determine what to build. If "faherty_apr_23" is passed,
: it will build assets for Faherty Apr 23 talk.

: If "faherty_apr_23" is not passed, it will build assets for the Jan 30, 2025 talk.
: If no argument is passed, it will build assets for the Jan 30, 2025 talk.

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
    cd %REPO_PATH%

    cd data/Jan_30_2025_recentered
    python %REPO_PATH%/csv_to_openspace.py -i jan_30_2025_recentered.json -a E:\OpenSpace\user\data\assets\jan_30_2025_recentered -o ./outfiles_jan_30_2025_recentered -t E:\git\cosmic-view-life\textures

) ELSE (
    echo No valid argument passed. Please pass "faherty_apr_23" or "jan_30_2025_recentered".
)


