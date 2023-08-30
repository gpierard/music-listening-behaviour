# # tests/conftest.py
# @pytest.fixture
# def spark() -> SparkSession:
#     _spark = (
#         SparkSession.builder.master("local[*]")
#             .appName("local-tests")
#             .enableHiveSupport()
#             .getOrCreate()
#     )
#     return _spark
# tests/pipelines/data_processing/conftest.py

import pandas as pd
import pytest

@pytest.fixture
def track_sessions():
    return pd.read_csv("C:/GP/music-listening-behaviour/data/01_raw/test_data.csv", sep ='\t')

@pytest.fixture
def userid_profiles():
    return pd.read_csv("data/01_raw/lastfm-dataset-1K/userid-profile.tsv",sep='\t')
