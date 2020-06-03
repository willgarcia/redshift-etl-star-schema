import configparser


# CONFIG
config = configparser.ConfigParser()
config.read('dwh.cfg')

# DROP TABLES

staging_events_table_drop = "DROP TABLE IF EXISTS staging_events"
staging_songs_table_drop = "DROP TABLE IF EXISTS staging_songs"
songplay_table_drop = "DROP TABLE IF EXISTS factsongplay"
user_table_drop = "DROP TABLE IF EXISTS dimuser"
song_table_drop = "DROP TABLE IF EXISTS dimsong"
artist_table_drop = "DROP TABLE IF EXISTS dimartist"
time_table_drop = "DROP TABLE IF EXISTS dimtime"

# CREATE TABLES

staging_events_table_create= ("""
CREATE TABLE staging_events (
    artist VARCHAR(255),
    auth VARCHAR(40),
    firstName VARCHAR(255),
    gender VARCHAR(1),
    itemInSession SMALLINT, 
    lastName VARCHAR(255),
    length  DECIMAL(10, 5),
    level VARCHAR(40),
    location VARCHAR(255),
    method VARCHAR(20),
    page VARCHAR(40),
    registration VARCHAR(40),
    sessionId INT,
    song VARCHAR(255),
    status SMALLINT,
    ts BIGINT,
    user_agent  VARCHAR(255),
    userId INTEGER 
)
""")

staging_songs_table_create = ("""
CREATE TABLE staging_songs (
    artist_id VARCHAR(100),
    artist_latitude DECIMAL(9,6),
    artist_longitude DECIMAL(9,6),
    artist_location VARCHAR(255),
    artist_name VARCHAR(255),
    duration DOUBLE PRECISION,
    num_songs SMALLINT,
    song_id VARCHAR(255),
    title  VARCHAR(255),
    year SMALLINT 
)
""")

songplay_table_create = ("""
CREATE TABLE factsongplay (
    songplay_id INT IDENTITY(0,1),
    start_time TIMESTAMP NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    level VARCHAR(10),
    song_id VARCHAR(100) NOT NULL,
    artist_id VARCHAR(100) NOT NULL,
    session_id VARCHAR(100) NOT NULL,
    location VARCHAR(200),
    user_agent  VARCHAR(200)
)
""")

user_table_create = ("""
CREATE TABLE dimuser (
    user_id VARCHAR(100) PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    gender VARCHAR(1),
    level VARCHAR(10) 
)
""")

song_table_create = ("""
CREATE TABLE dimsong (
    song_id VARCHAR(100) PRIMARY KEY,
    title  VARCHAR(255),
    artist_id VARCHAR(100) NOT NULL,
    year SMALLINT,
    duration SMALLINT 
)
""")

artist_table_create = ("""
CREATE TABLE dimartist (
    artist_id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(100),
    location VARCHAR(200),
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6) 
)
""")

time_table_create = ("""
CREATE TABLE dimtime (
    start_time TIMESTAMP PRIMARY KEY,
    hour SMALLINT,
    day SMALLINT,
    week SMALLINT,
    month SMALLINT,
    year SMALLINT,
    weekday SMALLINT 
)
""")

# STAGING TABLES

staging_events_copy = ("""
    copy staging_events from '{}'
    json '{}'
    credentials 'aws_iam_role={}'
    region 'ap-southeast-2';
""").format(
    config["S3"]["LOG_DATA"], 
    config["S3"]["LOG_JSONPATH"], 
    config["IAM_ROLE"]["ARN"]
)

staging_songs_copy = ("""
    copy staging_songs from '{}'
    credentials 'aws_iam_role={}'
    json 'auto'
    region 'ap-southeast-2';
""").format(
    config["S3"]["SONG_DATA"],
    config["IAM_ROLE"]["ARN"]
)

# FINAL TABLES

songplay_table_insert = ("""
INSERT INTO factsongplay (start_time, user_id, level, song_id, artist_id, session_id, location, user_agent)
SELECT
    '1970-01-01'::date + events.ts / 1000 * interval '1 second' as start_time,
    events.userId as user_id,
    events.level,
songs.song_id,
songs.artist_id,
    events.sessionId as session_id,
    events.location,
    events.user_agent
FROM staging_events events
JOIN staging_songs songs ON
    events.song = songs.title and events.artist = songs.artist_name
WHERE
    events.page = 'NextSong'
""")

user_table_insert = ("""
INSERT INTO dimuser (user_id, first_name, last_name, gender, level)  
SELECT DISTINCT 
    userId,
    firstName,
    lastName,
    gender, 
    level
FROM staging_events
WHERE 
    page = 'NextSong'
    AND userId NOT IN (SELECT DISTINCT user_id FROM dimuser)
""")

song_table_insert = ("""
INSERT INTO dimsong (song_id, title, artist_id, year, duration)
SELECT DISTINCT
    song_id,
    title,
    artist_id,
    year,
    duration
FROM staging_songs
WHERE 
    song_id NOT IN (SELECT DISTINCT song_id FROM dimsong)
""")

artist_table_insert = ("""
INSERT INTO dimartist (artist_id, name, location, latitude, longitude)
SELECT DISTINCT
    artist_id,
    artist_name as name,
    artist_location as location,
    artist_latitude as latitude,
    artist_longitude as longitude
FROM staging_songs
WHERE 
    artist_id NOT IN (SELECT DISTINCT artist_id FROM dimartist)
""")

time_table_insert = ("""
INSERT INTO dimtime (start_time, hour, day, week, month, year, weekday)
SELECT DISTINCT
    start_time,
    EXTRACT(hour FROM start_time) as hour,
    EXTRACT(day FROM start_time) as day,
    EXTRACT(week FROM start_time) as week,
    EXTRACT(month FROM start_time) as month,
    EXTRACT(year FROM start_time) as year,
    EXTRACT(weekday FROM start_time) as weekday
FROM (
    SELECT DISTINCT '1970-01-01'::date + ts / 1000 * interval '1 second' as start_time
    FROM staging_events
    WHERE page = 'NextSong'
)
WHERE 
    start_time NOT IN (SELECT DISTINCT start_time FROM dimtime)
""")


# QUERY LISTS

create_table_queries = [staging_events_table_create, staging_songs_table_create, songplay_table_create, user_table_create, song_table_create, artist_table_create, time_table_create]
drop_table_queries = [staging_events_table_drop, staging_songs_table_drop, songplay_table_drop, user_table_drop, song_table_drop, artist_table_drop, time_table_drop]
copy_table_queries = [staging_events_copy, staging_songs_copy]
insert_table_queries = [songplay_table_insert, user_table_insert, song_table_insert, artist_table_insert, time_table_insert]
