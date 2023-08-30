# music-listening-behaviour

## Overview

Gauthier Pierard's Music Listening Behaviour case study submission to UCB as a Kedro project, which was generated using `kedro 0.18.12`, `pyspark==3.4.1` and `Python 3.10.5` on Windows.

This project includes basic elements of logging and automated testing. A global spark session is defined across the pipeline using a custom hook.

## How to run 

- clone the repository
- create a virtual environment using the following
```
cd <your_envir_path>
.\.venv\Scripts\activate  # Windows
cd <this_repo_path>
pip install -r requirements.txt
pip install -r requirements.txt
pip install "kedro-datasets[pandas]"
```
If `pip install "kedro-datasets[pandas]"` returns errors, you could install with `--no-deps` and manually install `tables==3.7.0` for example. I provided the result of `pip freeze > src/requirements_freeze.txt`.

- [Get the source data](http://ocelma.net/MusicRecommendationDataset/lastfm-1K.html ) which I did not commit to version control. 
  - destination folder is data\01_raw\lastfm-dataset-1K which contains
    - `userid-profile.tsv`
    - `userid-timestamp-artid-artname-traid-traname.tsv`

- For node tests it is necessary to create the sample test data (subset of `userid-timestamp-artid-artname-traid-traname.tsv`) by running `python src/tests/define_test_data.py`. The data required for `kedro test` is now available in data\01_raw\test_data.csv.

- Inside the project, test with `kedro test`, run with `kedro run`, and explore with `kedro jupyter notebook` and `kedro ipython`.

## Approach

### Your mission

*Answer the following question: “What proportion of users had at least one long listening session?”
Here are some definitions:
We define a listening session as one or more songs played by a user, where each song has been started within 15 minutes of the previous’ song’s start time. The duration of a session is the time between the first and the last song’s start time. A long session has a duration in the top 10 percentile of session durations.*

#### Definitions

- `Track sessions` designates the dataset contained in `userid-timestamp-artid-artname-traid-traname.tsv`. It represents a userid playing a track at a certain time.
- `userid_profiles` designates the data in `userid-profile.tsv`, which is currently only used to check consistency between users in both datasets.  

#### Approach description

The general approach to solve this question is as follows.

- The source TSV files are manually extracted, and defined in the catalog as spark dataframes. For now, no custom data type was defined to either extract files from `tar.gz` archives or download them via HTTP requests.

- `conf/base/playlists-schema.json` contains the shema definition for the `track sessions`.

- Global parameters are defined in `conf/base/parameters.yml`
```
session_maxidletime: 900 # threshold time in seconds after which two played tracks don't belong to the same user session. 
long_session_quantile: 0.9 # quantile threshold which separates long from short sessions
```

- Two nodes are defined:

  - preprocess_format_tracksessions, basically just performs consistency checks (assertions), and formats the `timestamp` column to `unix_timestamp`.
  - process_tracksessions: performs the following:
    - windows and groups the data by `userid` and order these groups by `timestamp`
    - The `is_new_session` column is True whether the time between two successive tracks played is above the `session_maxidletime` of 900 seconds. 
    - Total session times are computed across all sessions
    - The threshold corresponding to the top decile is calculated (`9025.0` seconds with the initial data).
    - sessions are segregated as long and short
    - users which contain at least one long session are identified and counted.
    
    
    ![viz image](https://github.com/gpierard/music_listening_behaviour/blob/main/viz.png?raw=true)
    
#### results

941 users out of 992 had at least one long listening session (94.85%). This might seem counterintuitive based on the top 10% percentile, but is realistic given that each user has 1187 sessions on average.

### kedro setup 

- The project contains basic automated testing, globally and at node level, which can be run using `kedro test`.
- An `after_context_created` hook was defined in `src/music_listening_behaviour/hooks.py` and registered in `src/music_listening_behaviour/settings.py` in order to make a global `sparkSession` available to the pipeline. 
- logs are present in `logs\full_log.log`

## How this project could be improved 

- See if the algorithm can be improved (using for example non-equi joins)
- Adapt to streaming data where appropriate
- Run with the larger dataset (25k unique users)
- Expand automated and in-node testing
- Improve logging and exception handling







