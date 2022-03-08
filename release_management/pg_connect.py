import os
import pandas as pd
import sqlalchemy as sa
import psycopg2
from psycopg2 import Error
from sqlalchemy import create_engine


# for local testing only
DOCKER_CONTAINER = os.environ.get('DOCKER_CONTAINER', False)
print(f'Docker Container: {DOCKER_CONTAINER}')
if not DOCKER_CONTAINER:
    from dotenv import load_dotenv
    load_dotenv()


pg_username = os.environ.get('PG_USERNAME')
pg_password = os.environ.get('PG_PASSWORD')
pg_server = os.environ.get('PG_SERVER')
pg_port = os.environ.get('PG_PORT')
pg_db = os.environ.get('PG_DB')
pg_schema = os.environ.get('PG_SCHEMA')


def get_pg_engine():
    try:
        engine = create_engine('postgresql://' + pg_username + ':' + pg_password + '@' + pg_server + ':' + pg_port + '/' + pg_db)
        print('Engine created successfully')
        return engine
    except (Exception, Error) as e:
        print(f'An exception occurred: {e}')
        return None

def write_to_pg_database(pg_table_name, df):
    try:
        pg_engine = get_pg_engine()
        if pg_engine is not None:
            df.to_sql(name=pg_table_name, con=pg_engine, schema=pg_schema, if_exists='replace')
            return f'Data written to database: {pg_db}'
        else:
            return 'No Postgres Engine is available'
    except (Exception) as e:
        return f'An exception occurred: {e}'

def write_to_pg_database(pg_table_name, df, clear_table=True):
    try:
        pg_engine = get_pg_engine()
        if pg_engine is not None:
            if clear_table:
                insp = sa.inspect(pg_engine)
                if(insp.has_table(table_name=pg_table_name,schema=pg_schema)):
                    sql_stmt = 'DELETE FROM {schema}.{table_name}'.format(schema=pg_schema, table_name=pg_table_name)
                    with pg_engine.connect() as conn:
                        res = conn.execute(                
                            sql_stmt                
                        )
        
            df.to_sql(name=pg_table_name, con=pg_engine, schema=pg_schema, if_exists='append')
            return f'Data written to database: {pg_db}'
        else:
            return 'No Postgres Engine is available'
    except (Exception) as e:
        return f'An exception occurred: {e}'

def read_pg_table(pg_table_name):
    try:
        pg_engine = get_pg_engine()        
        if pg_engine is not None:
            df = pd.read_sql_table(table_name=pg_table_name, con=pg_engine, schema=pg_schema)
            return df
        else:
            return None
    except (Exception) as e:
        return f'An exception occurred: {e}'
        return None
