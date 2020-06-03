import configparser
import psycopg2
from sql_queries import copy_table_queries, insert_table_queries

def load_staging_tables(cur, conn):
    """ 
    Extract S3 data and COPY into Redshift staging tables
    """
    for query in copy_table_queries:
        cur.execute(query)
        conn.commit()

def insert_tables(cur, conn):
    """ 
    Insert data from 3FN schema (staging tables) into star schema (fact and dimension tables)
    """
    for query in insert_table_queries:
        cur.execute(query)
        conn.commit()

def main():
    """ 
    Connects to Redshift and Extract/Load/Transform data in Redshift
    """
    config = configparser.ConfigParser()
    config.read('dwh.cfg')

    conn = psycopg2.connect("host={} dbname={} user={} password={} port={}".format(*config['CLUSTER'].values()))
    cur = conn.cursor()
    
    load_staging_tables(cur, conn)
    insert_tables(cur, conn)

    conn.close()


if __name__ == "__main__":
    main()
