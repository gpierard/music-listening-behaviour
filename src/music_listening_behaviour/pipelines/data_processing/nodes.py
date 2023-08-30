"""
generated using Kedro 0.18.12
"""
import logging
from typing import Dict, Tuple
import numpy as np
import pandas as pd
from pyspark.sql import DataFrame

from pyspark.sql import SparkSession
# from pyspark.sql.functions import col  # Import the col function
from pyspark.sql.window import Window
import pyspark.sql.functions as F
from pyspark.sql.functions import unix_timestamp, lag, col
from kedro.io import MemoryDataset

# import pytest

def preprocess_format_tracksessions(tracksess: DataFrame, userid_profiles:pd.DataFrame , parameters: Dict) -> MemoryDataset: 
    """Pre-process the "track session" data from the file userid-timestamp-artid-artname-traid-traname.tsv, defined in catalog.yml.
    This dataframe is named track_session because it basically represents one user listening to a certain track at a certain time. 
    In contrast, "user sessions" are defined for a single user listening to several tracks in short succession.

    Args:
        tracksess: Data containing track session information.
    Returns:
        formatted track session data.
    """

    log = logging.getLogger("kedro")
    spark = SparkSession.builder.getOrCreate()
    
    # define basic assertions
    assert spark.conf.get("spark.app.name") == 'music-listening-behaviour' # assert that the spark session was initialized by kedro before the pipeline run
    assert tracksess.columns == ['userid', 'timestamp', 'artistid', 'artistname', 'traid', 'traname'] 
    nb_distinct_users = tracksess.select("userid").distinct().count()
    # nb_unique_users = 992
    assert nb_distinct_users==len(userid_profiles['#id'].drop_duplicates())
    log.info('nb_distinct_users '+str(nb_distinct_users))
    
    # Convert timestamp column to timestamp datatype
    ts_formatted = tracksess.withColumn("timestamp", unix_timestamp("timestamp", "yyyy-MM-dd'T'HH:mm:ss'Z'").cast("timestamp"))
    timestamp_col_type = next((col_type for col_name, col_type in ts_formatted.dtypes if col_name == 'timestamp'), None)
    assert timestamp_col_type=='timestamp'
    #ts_formatted.write.csv(r"data/02_intermediate/ts_formatted.csv")
    # ts_formatted_ = MemoryDataset(data=ts_formatted)
    return ts_formatted

def process_tracksessions(ts: MemoryDataset, parameters: Dict) -> pd.DataFrame: 
    """Grouping, windowing, and otherwise processing the track sessions

    Args:
        tracksess: Data containing track session information.
    Returns:
        formatted track session data.
    """

    log = logging.getLogger("kedro")
    spark = SparkSession.builder.getOrCreate()

    session_maxidletime = parameters['session_maxidletime']
    long_session_quantile = parameters['long_session_quantile']

    # Define a window specification for user-based operations
    user_window = Window.partitionBy("userid").orderBy("timestamp")
    # Calculate time differences between consecutive rows for each user
    ts = ts.withColumn("time_diff", F.unix_timestamp("timestamp") - F.unix_timestamp(F.lag("timestamp").over(user_window))).orderBy(['userid', "timestamp"])
    # Calculate session boundaries: a new session starts if time difference is greater than 15 minutes
    # or if the time_diff is null (start of a new user's sessions)
    ts = ts.withColumn("is_new_session", F.when((F.col("time_diff") > session_maxidletime) | (F.col("time_diff").isNull()), 1).otherwise(0))
    # Calculate session ID for each session using cumulative sum of "is_new_session" column
    ts = ts.withColumn("session_id", F.sum("is_new_session").over(user_window)).orderBy(['userid', "timestamp"])
    #ts.show(10)
    # Calculate session duration for each session
    session_duration = ts.groupBy("userid", "session_id").agg(
        F.min("timestamp").alias("start_time"),
        F.max("timestamp").alias("end_time")
    ).withColumn("session_duration", F.unix_timestamp("end_time") - F.unix_timestamp("start_time")).orderBy(['userid', "session_id"])

    # Calculate a unique session_id across all users
    session_duration = session_duration.withColumn(
        "unique_session_id",
        F.row_number().over(Window.orderBy("userid", "session_id"))
    )
    #session_duration.show(10)
    session_duration.count()

    # Determine the threshold for a long session duration (top 10 percentile)
    long_session_threshold = session_duration.approxQuantile("session_duration", [0.9], 0)[0] # error can be increased for performance
    log.info('long session threshold ' + str(long_session_threshold))

    # Identify users with at least one long session
    users_with_long_sessions = session_duration.filter(F.col("session_duration") >= long_session_threshold).select("userid").distinct()
    #users_with_long_sessions.show(100)

    # assert that the quantile was correctly approximated
    quantile_check = session_duration.agg(
        F.count(F.when(F.col("session_duration") < long_session_threshold, F.col("session_duration"))).alias("short_sessions_sum"),
        F.count(F.when(F.col("session_duration") >= long_session_threshold, F.col("session_duration"))).alias("long_sessions_sum")
    )
    qcheck = quantile_check.toPandas()
    qcheck['short_long_ratio'] = qcheck["short_sessions_sum"] / (qcheck["short_sessions_sum"]+qcheck["long_sessions_sum"])
    qcheck['long_short_ratio'] = qcheck["long_sessions_sum"] / (qcheck["short_sessions_sum"]+qcheck["long_sessions_sum"])
    assert abs(qcheck.short_long_ratio[0]-long_session_quantile)<0.001, "threshold long session quantiles were not correctly defined"

    # Count the total number of users and users with at least one long session
    total_users = ts.select("userid").distinct().count()
    users_with_long_session_count = users_with_long_sessions.count()
    users_with_long_session_count

    # Calculate the proportion of users with at least one long session
    proportion_with_long_sessions = users_with_long_session_count / total_users

    resultdata = {
        'users_with_long_session_count': [users_with_long_session_count],
        'total_users': [total_users],
        'proportion_with_long_sessions': [proportion_with_long_sessions],
        'long_session_threshold': long_session_threshold,
        'total short sessions': qcheck["short_sessions_sum"][0],
        'total long sessions': qcheck["long_sessions_sum"][0],
        'long_session_ratio': qcheck["long_short_ratio"][0]
    }
    
    res = pd.DataFrame(resultdata)
    log.info(str(res.head()))
    return res
