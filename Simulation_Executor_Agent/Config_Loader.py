import os


def load_environment_variables():
    """ Reads the environmental variables required for the correct operation of the application

        Returns:
            dict: contains the connection parameters of the database
            dict: contains required parameters for the simulation

    """

    db_config_params = {}
    simulation_environment_variables = {}
    try:
        db_config_params['host'] = os.environ['POSTGRESQL_IP']
        db_config_params['port'] = os.environ['POSTGRESQL_PORT']
        db_config_params['database'] = os.environ['POSTGRESQL_DB_NAME']
        db_config_params['user'] = os.environ['POSTGRESQL_DB_USER']
        db_config_params['password'] = os.environ['POSTGRESQL_DB_PASS']
        simulation_environment_variables['max_failures'] = os.environ['MAX_SIMULATION_FAILURES']
        simulation_environment_variables['time_out'] = os.environ['SIMULATION_TIME_OUT']
    except KeyError as error:
        print("One or more environmental variables are not set. Required environmental variables:")
        print("\tPOSTGRESQL_IP")
        print("\tPOSTGRESQL_PORT")
        print("\tPOSTGRESQL_DB_NAME")
        print("\tPOSTGRESQL_DB_USER")
        print("\tPOSTGRESQL_DB_PASS")
        print("\tMAX_SIMULATION_FAILURES")
        print("\tSIMULATION_TIME_OUT")
        raise SystemExit("Failure cause: {0}".format(error))
    else:
        return db_config_params, simulation_environment_variables



