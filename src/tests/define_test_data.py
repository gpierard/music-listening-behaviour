from pyspark.sql import SparkSession
# from pyspark.sql.functions import col  # Import the col function
import logging
from pyspark.sql.window import Window
import pyspark.sql.functions as F
from pyspark.sql.functions import unix_timestamp, lag, col
import pandas as pd
from pyspark.sql.functions import row_number

spark = SparkSession.builder \
    .appName("music-listening") \
    .master("local[6]") \
    .getOrCreate()

tracksess = spark.read.csv('C:/GP/music-listening-behaviour/data/01_raw/lastfm-dataset-1K/userid-timestamp-artid-artname-traid-traname.tsv', sep = '\t') \
            .withColumnRenamed("_c0", "userid") \
            .withColumnRenamed("_c1", "timestamp") \
            .withColumnRenamed("_c2", "artistid") \
            .withColumnRenamed("_c3", "artistname") \
            .withColumnRenamed("_c4", "traid") \
            .withColumnRenamed("_c5", "traname").orderBy(['userid', "timestamp"]) # catalog.load('track-sessions')


window_spec = Window.partitionBy("userid").orderBy("timestamp")
tracksess = tracksess.withColumn("row_num", row_number().over(window_spec))

# Filter and collect the first 30 lines per user
tracksess_filtered = tracksess.where(tracksess.row_num <= 30).drop("row_num")
pandas_df = tracksess_filtered.toPandas()
pandas_df.to_csv('C:/GP/music-listening-behaviour/data/01_raw/test_data.csv', sep ='\t', index=False)





