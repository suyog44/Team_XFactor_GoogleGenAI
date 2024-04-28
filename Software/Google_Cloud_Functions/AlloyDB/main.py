import functions_framework

import subprocess
from typing import Tuple

import pandas as pd
import pg8000
import sqlalchemy
import vertexai
from google.cloud.alloydb.connector import Connector
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DatabaseError
from vertexai.generative_models import GenerationConfig, GenerativeModel

import json
from collections import defaultdict


def create_sqlalchemy_engine(
    inst_uri: str, user: str, password: str, db: str
) -> Tuple[sqlalchemy.engine.Engine, Connector]:
    """Creates a connection pool for an AlloyDB instance and returns the pool
    and the connector. Callers are responsible for closing the pool and the
    connector.


    Args:
        inst_uri (str):
        
            The instance URI specifies the instance relative to the project,
            region, and cluster. For example:
            "projects/my-project/locations/us-central1/clusters/my-cluster/instances/my-instance"
        user (str):
            The database user name, e.g., postgres
        password (str):
            The database user's password, e.g., secret-password
        db (str):
            The name of the database, e.g., mydb

     Returns:
        Tuple[sqlalchemy.engine.Engine, Connector]:
            * A SQLAlchemy engine object for managing database interactions.
            * A Connector object for underlying database connections (can be used for closing).
    """
    connector = Connector()

    def getconn() -> pg8000.dbapi.Connection:
        """
        Establishes a connection to a Google Cloud AlloyDB instance (PostgreSQL database) using the pg8000 driver.

        Returns:
            pg8000.dbapi.Connection: An active database connection object.
        """
        conn: pg8000.dbapi.Connection = connector.connect(
            instance_uri=inst_uri,
            driver="pg8000",
            user=user,
            password=password,
            db=db,
            ip_type="PUBLIC",  # use ip_type to specify Public IP
        )
        return conn

    # create SQLAlchemy connection pool
    engine = sqlalchemy.create_engine(
        "postgresql+pg8000://", creator=getconn, isolation_level="AUTOCOMMIT"
    )
    engine.dialect.description_encoding = None
    return engine, connector

def check_table_exists(engine: Engine, connector: Connector, table_name: str) -> bool:
    """Checks if a table exists in the database.

    Args:
        engine (sqlalchemy.engine.Engine): SQLAlchemy engine object.
        connector (Connector): AlloyDB Connector object.
        table_name (str): Name of the table to check.

    Returns:
        bool: True if the table exists, False otherwise.
    """

    try:
        with engine.connect() as conn:
            check_cmd = sqlalchemy.text(f"SELECT 1 FROM {table_name} LIMIT 1")
            conn.execute(check_cmd)
        connector.close()
        return True

    except DatabaseError:
        return False



PROJECT_ID = "hackathon-genai-08032024"  
LOCATION = "asia-south1"  
REGION = LOCATION
CLUSTER = "self-learner"  
INSTANCE = "prototype"  
CPU_COUNT = 2

vertexai.init(project=PROJECT_ID, location=LOCATION)


INSTANCE_URI = (
    f"projects/{PROJECT_ID}/locations/{REGION}/clusters/{CLUSTER}/instances/{INSTANCE}"
)
USER = "postgres"
DB = "postgres"
TABLE_NAME = "google_patents_research_new"
password = "Starter_xfactor"


@functions_framework.http
def acess_alloydb(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    """
    data = request.get_json(silent=True)
    #request_args = request.args

    # Load the JSON data
    # data = request_json #json.loads(request_json)


    if data and ('action_call' in data):
        perform_action = data['action_call'][0]
        perform_data = data['action_call'][1]
    else:
        return "Sorry no action call item"

    
    engine, connector = create_sqlalchemy_engine(
    inst_uri=INSTANCE_URI,
    user=USER,
    password=password,
    db=DB,)

    if perform_action == "CREATE_TABLE": 

        TABLE_NAME = perform_data['TABLE_NAME']
        sql_text = perform_data['sql_text']

        embedding_column = "embedding"
        DIMENSIONS = 768 

        if not check_table_exists(engine, connector, TABLE_NAME):
    
            # Create table
            create_table_cmd = sqlalchemy.text(
                f"CREATE TABLE {TABLE_NAME} {sql_text}",
            )

            # Add extensions
            google_ml_integration_cmd = sqlalchemy.text(
                "CREATE EXTENSION IF NOT EXISTS google_ml_integration CASCADE"
            )
            vector_cmd = sqlalchemy.text("CREATE EXTENSION IF NOT EXISTS vector")

            # Add column to store embeddings
            add_column_cmd = sqlalchemy.text(
                f"ALTER TABLE {TABLE_NAME} ADD COLUMN {embedding_column} vector({DIMENSIONS});"
            )

            try:
                # Execute the queries
                with engine.connect() as conn:
                    print("Creating table...")
                    conn.execute(create_table_cmd)
                    print("Add extensions...")
                    conn.execute(google_ml_integration_cmd)
                    conn.execute(vector_cmd)
                    print("Add column to store embeddings...")
                    try:
                        conn.execute(add_column_cmd)
                    except Exception as e:
                        print("Errror : ", e)
                        print(f"Column {embedding_column} already exists")
                    print("Commiting...")
                    conn.commit()
                    print("Done")
                connector.close()
            except:
                return "Error in creating table"
            

            return "Table with name {0} has been sucessfully created".format(TABLE_NAME)

        else:
            return "Table with name {0} already exits".format(TABLE_NAME)

    elif perform_action == "UPDATE_TABLE":

        TABLE_NAME = perform_data['TABLE_NAME']
        sql_text = perform_data['sql_text']
        # parameter_map_json = json.loads(perform_data['parameter_map'])

        parameter_map = perform_data['parameter_map']

        EMBEDDING_MODEL = "textembedding-gecko@003"  
        embedding_column = "embedding"


        if check_table_exists(engine, connector, TABLE_NAME):

            # Insert data
            insert_data_cmd = sqlalchemy.text(
                f"""
            INSERT INTO {TABLE_NAME} VALUES {sql_text}
            """
            )

            # Generate embeddings for `image_description` columns of the dataset
            embedding_cmd = sqlalchemy.text(
                f"UPDATE {TABLE_NAME} SET {embedding_column} = embedding('{EMBEDDING_MODEL}', image_description) WHERE {embedding_column} IS NULL;"
            )


            # Execute the queries
            with engine.connect() as conn:
                print("Inserting values...")
                conn.execute(
                    insert_data_cmd,
                    parameter_map,
                )
                #print("Creating Embeddings...")
                #conn.execute(embedding_cmd)
                print("Commiting...")
                conn.commit()
                print("Done")
            connector.close()

            return "Table with name {0} has been sucessfully updated".format(TABLE_NAME)

    elif perform_action == "RECALCULATE_THE_INDEX":

        TABLE_NAME = perform_data['TABLE_NAME']
        # sql_text = perform_data['sql_text']

        embedding_column = "embedding"
        distance_function = "vector_cosine_ops"
  
        # Create an ivfflat index on the table with embedding column and cosine distance
        index_cmd = sqlalchemy.text(
            f"CREATE INDEX ON {TABLE_NAME} USING ivf ({embedding_column} {distance_function})"
        )

        # Execute the queries
        with engine.connect() as conn:
            print("Creating Index...")
            conn.execute(index_cmd)
            print("Commiting...")
            conn.commit()
            print("Done")
        connector.close()

        return "Table with name {0} has been sucessfully reindexed".format(TABLE_NAME)

    elif perform_action == "RETRIEVE_FROM_TABLE_EMBEDDING":

        TABLE_NAME = perform_data['TABLE_NAME']
        sel_columns = perform_data['sel_columns']
        query = perform_data['query']
        row_count = perform_data['row_count']
        #session_id = perform_data['session_id']

        
        embedding_model = "textembedding-gecko@003"  
        embedding_column = "embedding"

        # Perform semantic search
        search_cmd = sqlalchemy.text(
            f"""
        SELECT {sel_columns} , {embedding_column} <-> embedding('{embedding_model}', '{query}')::vector AS similarity_score
        FROM {TABLE_NAME}
        ORDER BY similarity_score DESC  
        LIMIT {row_count}
        """
        )
        
        # 

        # Execute the query
        with engine.connect() as conn:
            result = conn.execute(search_cmd)
            context = [row._asdict() for row in result]
        connector.close()


        # String format the retrieved information
        retrieved_information = "\n".join(
            [
                f" __splitKey__ ".join([f"{value}" for key, value in element.items() if element["similarity_score"] > 0.6])
                for index, element in enumerate(context)
            ]
        )

        return retrieved_information

    elif perform_action == "RETRIEVE_FROM_TABLE_SESSION":

        TABLE_NAME = perform_data['TABLE_NAME']
        sel_columns = perform_data['sel_columns']
        sel_session = perform_data['sel_session']

        get_session_data_cmd = sqlalchemy.text(
            f"""
        SELECT {sel_columns}
        FROM {TABLE_NAME}
        WHERE session_id = :value;
        """
        )

        # Execute the query
        with engine.connect() as conn:
            result = conn.execute(get_session_data_cmd , {'value': sel_session})
            context = [row._asdict() for row in result]
        connector.close()

      

        # keyslist = context[0].keys().tolist()
        
        combined_dict = defaultdict(list)

        for index, element in enumerate(context):
            for key, value in element.items():
                combined_dict[key].append(value)

        return json.dumps(combined_dict)



    else:
        return "It went to none "

    # else if perform_action == "RETRIEVE_FROM_TABLE_CLOUMN":
