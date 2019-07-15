import os


def load_environment_variables_aws():
    db_config_params = {}
    try:
        db_config_params['host'] = '<hostname or IP>'
        db_config_params['port'] = 5432
        db_config_params['database'] = '<db_name>'
        db_config_params['user'] = '<db_user>'
        db_config_params['password'] = '<db_password>'
    except KeyError as error:
        print("One or more environmental variables are not set. Required environmental variables:")
        print("\tPOSTGRESQL_IP")
        print("\tPOSTGRESQL_PORT")
        print("\tPOSTGRESQL_DB_NAME")
        print("\tPOSTGRESQL_DB_USER")
        print("\tPOSTGRESQL_DB_PASS")
        raise SystemExit("Failure cause: {0}".format(error))
    else:
        return db_config_params




