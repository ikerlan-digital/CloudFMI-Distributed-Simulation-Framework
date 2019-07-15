import psycopg2
import psycopg2.extras


def get_output_params_names(db_config_params):
    """ Gets the names of the output parameters from the database

        Args:
            db_config_params (dict): contains the connection parameters of the database

        Returns:
            list: contains the name of the output parameters
    """
    conn = None
    column_names = list()
    try:
        # connect to the PostgreSQL server
        conn = psycopg2.connect(**db_config_params)

        # create a cursor
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # select only the columns corresponding to the output parameters
        get_columns_name_sql = "SELECT column_name FROM information_schema.columns " \
                               "WHERE table_name = 'simulation_results' " \
                               "and column_name != 'simulation_id'" \
                               "and column_name != 'sea_id'" \
                               "and column_name != 'execution_time'" \
                               "and column_name != 'label'"

        cur.execute(get_columns_name_sql)
        column_names_result = cur.fetchall()

        for column in column_names_result:
            column_names.append(column['column_name'])

        column_names = sorted(column_names)

        # close the communication with the PostgreSQL
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        raise SystemExit("Failure cause: {0}".format(error))
    finally:
        if conn is not None:
            conn.commit()
            conn.close()

        return column_names



def execute_vacuum(db_config_params, query):
    """ Executes a given query in the database

        Args:
            db_config_params (dict): contains the connection parameters of the database
            query (str): SQL statement to be executed
    """
    conn = None
    try:
        # connect to the PostgreSQL server
        conn = psycopg2.connect(**db_config_params)
        conn.set_isolation_level(0)

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


def generate_remove_columns_query(output_params):
    initial_query = 'ALTER TABLE simulation_results '

    # the dynamic part of the query depends on the output parameters specified by the user
    dynamic_query = ",".join('DROP COLUMN "' + variable_name + '"' for variable_name in output_params)

    final_create_table_sql = initial_query + dynamic_query

    return final_create_table_sql


def truncate_database(db_config_params):
    output_params = get_output_params_names(db_config_params)
    query = generate_remove_columns_query(output_params)
    execute_query(db_config_params, query)
    execute_vacuum(db_config_params, "VACUUM FULL")

