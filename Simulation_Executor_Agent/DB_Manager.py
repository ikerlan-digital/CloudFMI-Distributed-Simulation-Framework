import psycopg2
import psycopg2.extras
from collections import OrderedDict


def update_simulation_state(db_config_params, simulation_id, status):
    """ Updates the state of a given simulation in the database

        Args:
            db_config_params (dict): contains the connection parameters of the database
            simulation_id (int): identifier of the simulation to be updated
            status (str): the new status of the corresponding simulation
    """
    conn = None
    try:
        # connect to the PostgreSQL server
        conn = psycopg2.connect(**db_config_params)

        # create a cursor
        cur = conn.cursor()

        # generate the SQL statement
        if status == 'Executed':
            update_simulation_state_sql = "UPDATE experimentation_config SET state=%s, " \
                                          "timestamp_end=to_char(current_timestamp, 'YYYY/MM/DD HH24:MI:SS') " \
                                          "WHERE simulation_id=%s"
        else:
            update_simulation_state_sql = 'UPDATE experimentation_config SET state=%s WHERE simulation_id=%s'

        # execute the SQL statement
        variables = [status, simulation_id]
        cur.execute(update_simulation_state_sql, variables)

        # close the communication with the PostgreSQL
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        print('\tSimulation {0} marked as {1}\n\n'.format(simulation_id, status))
        if conn is not None:
            conn.commit()
            conn.close()


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


def get_next_simulation_config(db_config_params):
    """ Gets the configuration of the next simulation to be executed

        Args:
            db_config_params (dict): contains the connection parameters of the database
        Returns:
            dict: contains the configuration of the next simulation to be executed
    """
    # connect to the PostgreSQL server
    conn = psycopg2.connect(**db_config_params)

    # create a cursor
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # get next simulation id and mark it as executing
    get_simulation_id_sql = 'SELECT * from get_next_simulation_config()'
    cur.execute(get_simulation_id_sql)
    user_parameters = cur.fetchone()

    # close the communication with the PostgreSQL
    cur.close()

    if conn is not None:
        conn.commit()
        conn.close()

    return user_parameters


def insert_simulation_results(db_config_params, simulation_id, sea_id, execution_time, output_params_names,
                              simulation_output, label):
    """ Inserts into the database the results obtained after completing the simulation

        Args:
            db_config_params (dict): contains the connection parameters of the database
            simulation_id (int): identifier of the simulation to be updated
            sea_id (string): id of the simulation executor agent that executes the current simulation
            execution_time (int): time required to complete the simulation (in seconds)
            output_params_names (list): contains the names of the output parameters
            simulation_output (dict): contains the results of the simulation
            label: represents to which class belongs the simulation
    """
    # connect to the PostgreSQL server
    conn = psycopg2.connect(**db_config_params)

    # create a cursor
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # create insert query
    column_names_str = ",".join('"' + variable + '"' for variable in output_params_names)
    placeholders_str = ",".join("decode(%s, 'escape')" for i in output_params_names)
    insert_simulation_results_sql = 'INSERT INTO simulation_results("simulation_id",' \
                                    '"sea_id", "execution_time",' \
                                    + column_names_str + ',"label") VALUES (%s,%s,%s,' + placeholders_str + ',%s)'

    # convert results array into comma separated text
    simulation_output_str = OrderedDict()
    for variable in output_params_names:
        simulation_output_str[variable] = ','.join(str(e) for e in simulation_output[variable])

    # get a list of values from dict
    simulation_output_list = [v for k, v in simulation_output_str.items()]

    # add simulation identifier, SEA identifier, execution time and the label
    variables = list([str(simulation_id), sea_id, str(execution_time)]) \
                + simulation_output_list + list(str(label))

    # execute query
    cur.execute(insert_simulation_results_sql, variables)

    # close the communication with the PostgreSQL
    cur.close()

    if conn is not None:
        conn.commit()
        conn.close()


def check_failed_simulations(db_config_params, simulation_environment_variables):
    """ Checks in the database whether there are failed simulations that have not exceed the maximum failures.

        Args:
            db_config_params (dict): contains the connection parameters of the database
            simulation_environment_variables (dict): environment variables required for the correct operation of
                                                     the simulation

        Returns:
            boolean: indicates whether failed simulations are reset (True) or not (False).
    """
    # connect to the PostgreSQL server
    conn = psycopg2.connect(**db_config_params)

    # create a cursor
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # check whether there are failed simulations that have not exceed the maximum failures
    check_failed_simulations_sql = 'SELECT search_failed_simulations(%s,%s)'
    cur.execute(check_failed_simulations_sql, (simulation_environment_variables['max_failures'],
                                               simulation_environment_variables['time_out']))
    is_simulation_reset = cur.fetchone()
    is_simulation_reset = is_simulation_reset['search_failed_simulations']

    # close the communication with the PostgreSQL
    cur.close()

    if conn is not None:
        conn.commit()
        conn.close()

    return is_simulation_reset


def insert_simulation_failure_registry(db_config_params, simulation_id, sea_id, failure_type):
    """ Inserts into the database a new failure registry when a failure occurs during the execution of a given simulation

        Args:
            db_config_params (dict): contains the connection parameters of the database
            simulation_id (int): identifier of the simulation to be updated
            sea_id (string): id of the simulation executor agent that executes the current simulation
            failure_type (string): description of the failure
    """
    conn = None
    try:
        # connect to the PostgreSQL server
        conn = psycopg2.connect(**db_config_params)

        # create a cursor
        cur = conn.cursor()

        insert_sql = "INSERT INTO simulation_failure_registry " \
                     "VALUES (%s, to_char(current_timestamp, 'YYYY/MM/DD HH24:MI:SS'), %s, %s)"

        variables = [simulation_id, sea_id, failure_type]
        cur.execute(insert_sql, variables)

        # close the communication with the PostgreSQL
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        print('\tInserted new failure registry for Simulation {0}\n\n'.format(simulation_id))
        if conn is not None:
            conn.commit()
            conn.close()


def rollback_simulation_state(db_config_params, simulation_id, sea_id, failure_type):
    """ Modifies the state of a simulation to "Failed" when an error occurs

        Args:
            db_config_params (dict): contains the connection parameters of the database
            simulation_id (int): identifier of the simulation to be updated
            sea_id (string): id of the simulation executor agent that executes the current simulation
            failure_type (string): description of the failure
    """
    if simulation_id is not None:
        print('An error occurred during the simulation')
        update_simulation_state(db_config_params, simulation_id, 'Failed')
        insert_simulation_failure_registry(db_config_params, simulation_id, sea_id, failure_type)

