import psycopg2
import psycopg2.extras
from sqlalchemy import create_engine
from pandas import DataFrame


def execute_query(db_config_params, query):
    """ Executes a given query in the database

        Args:
            db_config_params (dict): contains the connection parameters of the database
            query (str): SQL statement to be executed
    """
    conn = None
    try:
        # connect to the PostgreSQL server
        conn = psycopg2.connect(**db_config_params)

        # create a cursor
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # execute query
        cur.execute(query)

        # close the communication with the PostgreSQL
        cur.close()
    except psycopg2.ProgrammingError as err:
        print(err)
        pass
    finally:
        if conn is not None:
            conn.commit()
            conn.close()


def create_database(db_config_params):
    """ Executes a given query in the database

        Args:
            db_config_params (dict): contains the connection parameters of the database
            query (str): SQL statement to be executed
    """
    conn = None
    try:
        # connect to default database to be able to create the database
        # make sure the user has the corresponding privileges
        con = psycopg2.connect(database='postgres',
                               host=db_config_params['host'],
                               port=db_config_params['port'],
                               user=db_config_params['user'],
                               password=db_config_params['password'])

        con.autocommit = True

        cur = con.cursor()
        cur.execute('CREATE DATABASE {0};'.format(db_config_params['database']))

        # close the communication with the PostgreSQL
        cur.close()
    except psycopg2.ProgrammingError as err:
        print(err)
        pass
    finally:
        if conn is not None:
            conn.commit()
            conn.close()


def insert_generated_simulations_into_db(simulations: DataFrame, max_simulation_id, db_config_params):
    """ Executes a query in the database to store the experimentation set up

        Args:
            simulations (DataFrame): configuration of all the simulations involving the experimentation
            max_simulation_id (int): the maximum simulation id stored in the database
            db_config_params (dict): contains the connection parameters of the database

    """
    # create database connection string
    connection_str = 'postgresql+psycopg2://{0}:{1}@{2}:{3}/{4}'.format(db_config_params['user'],
                                                                        db_config_params['password'],
                                                                        db_config_params['host'],
                                                                        db_config_params['port'],
                                                                        db_config_params['database'])

    pg_engine = create_engine(connection_str)

    # reset the IDs of the simulations
    index_list = list(range(max_simulation_id + 1, max_simulation_id + 1 + len(simulations)))
    simulations['simulation_id'] = index_list

    # create the table. If the table exists, the simulations are appended to the stored ones
    table_name = 'experimentation_config'
    simulations.to_sql(name=table_name, con=pg_engine, if_exists='append', index=False)

    # set the column "simulation_id" as the primary key
    try:
        with pg_engine.connect() as con:
            con.execute('ALTER TABLE {0} ADD PRIMARY KEY (simulation_id);'.format(table_name))
    except (Exception, psycopg2.ProgrammingError):
        pass


def get_max_simulation_id(db_config_params):
    """ Queries the database to get the maximum simulation id. It returns 0 in case no simulations are yet stored.

        Args:
            db_config_params (dict): contains the connection parameters of the database

        Returns:
            int: the maximum simulation id

    """
    conn = None
    try:
        # connect to the PostgreSQL server
        conn = psycopg2.connect(**db_config_params)

        # create a cursor
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        get_max_simulation_id_sql = "select max(simulation_id) as max_simulation_id from experimentation_config"

        # execute query
        cur.execute(get_max_simulation_id_sql)

        # get result
        max_simulation_id = cur.fetchone()
        max_simulation_id = max_simulation_id['max_simulation_id']

        # close the communication with the PostgreSQL
        cur.close()
    except psycopg2.ProgrammingError:
        max_simulation_id = 0
        return max_simulation_id
    else:
        if max_simulation_id is None:
            max_simulation_id = 0
        return max_simulation_id
    finally:
        if conn is not None:
            conn.commit()
            conn.close()
