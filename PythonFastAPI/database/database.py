from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from psycopg2 import DatabaseError
from config import settings
import traceback

# Postgresql database connection
POSTGRES_CONN_STR = settings.POSTGRES_CONN_STR
engine = create_engine(POSTGRES_CONN_STR)

def sp_call(proc_name, params=None):
    response = None
    connection = engine.raw_connection()
    try:
        cursor = connection.cursor()
        # execute statement
        cursor.callproc(proc_name, params)
        # commit the changes to the database
        connection.commit()
        response = [dict((cursor.description[i][0], value) for i, value in enumerate(row)) for row in cursor.fetchall()]
        # close communication with the database
        cursor.close()
        connection.close()
    except(Exception, DatabaseError) as error:
        print(error)
        error_msg = traceback.format_exc()
        print("error while database operation")
    finally:
        if connection is not None:
            connection.close()
    return response