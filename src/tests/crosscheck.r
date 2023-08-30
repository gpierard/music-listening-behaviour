library(data.table)
library(dplyr)

# Read the TSV file
tracksess <- fread('C:/GP/music-listening-behaviour/data/01_raw/lastfm-dataset-1K/userid-timestamp-artid-artname-traid-traname.tsv', sep = '\t',
                   col.names = c("userid", "timestamp", "artistid", "artistname", "traid", "traname"))

tracksess %>% dim

class(tracksess$timestamp)

# Convert timestamp column to POSIXct datatype
#tracksess[, timestamp := as.POSIXct(timestamp, format = "%Y-%m-%dT%H:%M:%SZ")]

# Set session_maxidletime and long_session_quantile
session_maxidletime <- 900
long_session_quantile <- 0.9
cat("starting pipeline with session_maxidletime", session_maxidletime, "long_session_quantile", long_session_quantile, "\n")

# Basic assertion
nb_distinct_users <- unique(tracksess$userid) %>% length
nb_distinct_users
stopifnot(nb_distinct_users == 992)

tracksess = tracksess[order(userid, timestamp)]

# Calculate time differences and session boundaries
tracksess[, time_diff := difftime(timestamp, shift(timestamp, fill = NA),units="secs"), by = userid]

tracksess[, is_new_session := ifelse(is.na(time_diff) | time_diff > session_maxidletime, 1, 0), by = userid]


tracksess$is_new_session <- ifelse(is.na(tracksess$time_diff) | tracksess$time_diff > session_maxidletime, 1, 0)
tracksess[, session_id := cumsum(is_new_session), by = userid]

tracksess %>% head(100)

# Calculate session duration
session_durationdf <- tracksess[, .(start_time = min(timestamp), end_time = max(timestamp)),
                              by = .(userid, session_id)]

session_durationdf[, session_duration := as.numeric(difftime(end_time, start_time, units = "secs"))]

session_durationdf %>% head(100)

# Calculate unique_session_id
session_durationdf[, unique_session_id := seq_len(.N), by = userid]

# Calculate long session threshold
long_session_threshold <- quantile(session_durationdf$session_duration, probs = long_session_quantile)

session_durationdf %>% head
pydurs = fread('data/pydurs.csv')



cat("long session threshold", long_session_threshold, "\n")

# Identify users with long sessions
users_with_long_sessions <- unique(session_durationdf[session_duration >= long_session_threshold, userid])

# Calculate proportions
total_users <- length(unique(tracksess$userid))
users_with_long_session_count <- length(users_with_long_sessions)
proportion_with_long_sessions <- users_with_long_session_count / total_users

# Calculate short and long session counts
short_sessions_sum <- sum(session_duration$session_duration < long_session_threshold)
long_sessions_sum <- sum(session_duration$session_duration >= long_session_threshold)

# Calculate long_short_ratio
long_short_ratio <- long_sessions_sum / (short_sessions_sum + long_sessions_sum)

resultdata <- data.frame(users_with_long_session_count = users_with_long_session_count,
                         total_users = total_users,
                         proportion_with_long_sessions = proportion_with_long_sessions,
                         long_session_threshold = long_session_threshold,
                         total_short_sessions = short_sessions_sum,
                         total_long_sessions = long_sessions_sum,
                         long_short_ratio = long_short_ratio)

print(resultdata)

