import pandas as pd
import numpy as np
import urllib.request
import shutil
from pandas import read_json
from argparse import ArgumentParser
from itertools import product
from pandas import DataFrame
from Config_Loader import load_environment_variables
from DB_Manager import execute_query, get_max_simulation_id, insert_generated_simulations_into_db, create_database

# hardcoded file names
config_files = ['input_params.json', 'output_params.json', 'anomalous_params.json', 'experimentation_config.csv']


def get_argument_parser():
    """ Defines the arguments to be read by the application

        Returns:
            ArgumentParser: parser containing the input arguments of the application

    """

    parser = ArgumentParser()
    parser.add_argument("-u", "--url", help="URL of the root directory where configuration files are stored (Use '/' "
                                            "at the end of the path)")
    parser.add_argument("--input_params", help="file containing the input parameters of the simulator")
    parser.add_argument("--output_params", help="file containing the name of output parameters")
    parser.add_argument("--anomalous_params", help="file containing which values make an anomalous simulation")
    parser.add_argument("--experimentation_config", help="file containing the entire experimentation configuration")

    return parser


def get_args(parser):
    """ Reads the input arguments of the application

        Args:
            parser (ArgumentParser): argument parser containing the input parameters to be read

        Returns:
            ArgumentParser: parser containing the input arguments of the application

    """
    args = parser.parse_args()

    url = args.url
    input_params_file = args.input_params
    output_params_file = args.output_params
    anomalous_params_file = args.anomalous_params
    experimentation_config_file = args.experimentation_config

    is_config_file = False

    # It is mandatory to set the input params file or the experimentation configuration file to configure the parameters
    # of the simulations. It is also mandatory to set the output params files. Anomalous params file is optional.
    # In case these requirements are not satisfied, the application will be exited
    if url is not None:
        if input_params_file is not None or experimentation_config_file is not None:
            if output_params_file is not None:
                is_config_file = True

    if is_config_file:
        return url, input_params_file, output_params_file, anomalous_params_file, experimentation_config_file
    else:
        print('Not all arguments have been set. Use -h or --help flags to show help details')
        raise SystemExit(0)


def download_config_files(url, file_list):
    """ Downloads the required files

        Args:
            url (str): root directory where the files to be downloaded are stored
            file_list (list): list containing the name of the files to be downloaded

    """
    # index used to manage the list of hardcoded file names. The same order is always followed
    index = 0
    print("Downloading files...")
    for file in file_list:
        if file is not None:
            print("\t", url + file)
            with urllib.request.urlopen(url + file) as response, open('data/' + config_files[index], 'wb') as out_file:
                shutil.copyfileobj(response, out_file)

        index += 1
    print("Download completed")


def generate_all_simulation_combinations():
    """ Generates all possible simulation configurations based on the input params file defined by the user.

        Returns:
            DataFrame: contains all the generated simulations

    """
    input_params = read_json('data/input_params.json')
    input_params_names = sorted(list(input_params.columns))

    simulation_params = list()

    # get all values of each variable in the json file
    for col in input_params.columns:
        values_col = np.array(input_params[col][0])
        simulation_params.append(values_col[~np.isnan(values_col)])

    # generate all possible combinations and add the column "simulation_id"
    simulation_combinations = pd.DataFrame(list(product(*simulation_params)), columns=input_params.columns)
    simulation_combinations['simulation_id'] = simulation_combinations.index

    # add timestamp_init, timestamp_end state and label columns and initialize them with default values
    simulation_combinations['timestamp_init'] = ' '
    simulation_combinations['timestamp_end'] = ' '
    simulation_combinations['state'] = 'Not executed'
    simulation_combinations['label'] = 0

    # sort columns to match the schema of the database
    sorted_cols = ['simulation_id', 'timestamp_init', 'timestamp_end'] \
                  + input_params_names \
                  + ['state', 'label']

    simulation_combinations = simulation_combinations[sorted_cols]

    return simulation_combinations


def set_labels(simulations: DataFrame):
    """ Sets the label to each simulation based on the anomalous params file defined by the user

        Args:
            simulations (DataFrame): contains all the generated simulations

        Returns:
            DataFrame: contains all the generated simulations with it corresponding label

    """
    anomalous_params = read_json('data/anomalous_params.json')

    # set label=1 if any of the simulations contains an anomalous value
    for col in anomalous_params.columns:
        values_col = np.array(anomalous_params[col][0])
        values_col = values_col[~np.isnan(values_col)]
        simulations.loc[simulations[col].isin(values_col), "label"] = 1

    return simulations


def get_experimentation_config_from_csv():
    """ Defines the experimentation set up based on the configuration file specified by the user. In this case, no
        simulations are generated as the configuration of each simulation is already given by the user.

        Returns:
            DataFrame: contains the experimentation configuration specified by the user

    """
    # TODO: manage the label column. The user may or not set it.
    experimentation_config = pd.read_csv('data/experimentation_config.csv')
    input_params_names = sorted(list(experimentation_config.columns))

    # add timestamp_init, timestamp_end state and label columns and initialize them with default values
    experimentation_config['simulation_id'] = experimentation_config.index
    experimentation_config['timestamp_init'] = ' '
    experimentation_config['timestamp_end'] = ' '
    experimentation_config['state'] = 'Not executed'
    experimentation_config['label'] = 0

    # sort columns to match the schema of the database
    sorted_cols = ['simulation_id', 'timestamp_init', 'timestamp_end'] \
                  + input_params_names \
                  + ['state', 'label']

    experimentation_config = experimentation_config[sorted_cols]

    return experimentation_config


def generate_create_simulations_result_table_sql():
    """ Generates an SQL statement to create a table on the database where the results of the simulations are stored.
        It uses the output params file defined by the user to define the schema of the table. All the columns
        representing an output parameter are set as bytea as the results are stored in binary format.

        Returns:
            str: SQL statement containing the query to create the table

    """
    output_params = read_json('data/output_params.json')
    output_params = sorted(list(output_params['params'][0]))

    initial_create_table_sql = 'CREATE TABLE simulation_results("simulation_id" integer ' \
                               'REFERENCES experimentation_config(simulation_id),' \
                               '"sea_id" text,' \
                               '"execution_time" real,' \
 \
        # the dynamic part of the query depends on the output parameters specified by the user
    dynamic_variable_sql = ",".join('"' + variable_name + '" bytea' for variable_name in output_params)

    final_create_table_sql = initial_create_table_sql + dynamic_variable_sql + ', "label" integer)'

    return final_create_table_sql


def generate_create_simulations_failures_registry_table_sql():
    """ Generates an SQL statement to create a table on the database where the the failures occurred during
        the simulations are registered.

        Returns:
            str: SQL statement containing the query to create the table

    """
    create_table_sql = 'CREATE TABLE simulation_failure_registry("simulation_id" integer ' \
                       'REFERENCES experimentation_config(simulation_id),' \
                       '"failure_timestamp" text,' \
                       '"sea_id" text,' \
                       '"failure_description" text)'

    return create_table_sql


def generate_stored_procedure_get_simulation_config():
    """ Generates an SQL statement to create a stored procedure used to obtain the configuration of the next simulation
        to be executed. The stored procedure returns the configuration of the first found non executed simulation,
        if any.

        Returns:
            str: SQL statement containing the query to create the stored procedure

    """
    sql = r"""
        CREATE OR REPLACE FUNCTION get_next_simulation_config() RETURNS SETOF experimentation_config AS $$ 
        DECLARE
            simulation_row experimentation_config%rowtype;
        BEGIN
            SELECT * INTO simulation_row FROM experimentation_config WHERE state = 'Not executed' ORDER BY simulation_id LIMIT 1 FOR UPDATE;
            UPDATE experimentation_config SET timestamp_init= to_char(current_timestamp, 'YYYY/MM/DD HH24:MI:SS'), state='Executing' where simulation_id = simulation_row.simulation_id; 
            RETURN QUERY SELECT * FROM experimentation_config WHERE simulation_id = simulation_row.simulation_id; 
        END;
        $$ LANGUAGE plpgsql;
    """
    return sql


def generate_stored_procedure_search_failed_simulations():
    """ Generates an SQL statement to create a stored procedure used to search for failed simulations. If failed
        simulations are found, they are reset provided that they meet the corresponding requirements. It returns
        True in case any simulation is reset.

        Returns:
            str: SQL statement containing the query to create the stored procedure

    """
    sql = r"""
        CREATE OR REPLACE FUNCTION search_failed_simulations(max_failures_in integer, time_out integer) RETURNS boolean AS $$
        DECLARE
            timestamp_with_delay text;
            n_reset_simulations integer;
        BEGIN
            LOCK TABLE experimentation_config IN ACCESS EXCLUSIVE MODE;
            UPDATE experimentation_config as a 
                SET state='Not executed', timestamp_init = ' '
                WHERE a.state = 'Failed'
                AND (select count(simulation_id) from simulation_failure_registry where simulation_id = a.simulation_id) < max_failures_in;

            SELECT to_char(current_timestamp - (time_out * interval '1 minute'), 'YYYY/MM/DD HH24:MI:SS') INTO timestamp_with_delay;

            UPDATE experimentation_config
                SET state='Not executed', timestamp_init = ' '
                WHERE state = 'Executing'
                AND timestamp_end = ' '
                AND timestamp_init < timestamp_with_delay;

            SELECT COUNT(*) INTO n_reset_simulations FROM experimentation_config WHERE state='Not executed';

            IF n_reset_simulations > 0 THEN
                RETURN True;
            ELSE
                RETURN False;
            END IF;
        END;
        $$ LANGUAGE plpgsql;
    """
    return sql


def main():
    try:
        # create an argument parser
        parser = get_argument_parser()

        # read the arguments
        url, input_params_file, output_params_file, anomalous_params_file, experimentation_config_file = get_args(
            parser)

        # download configuration files
        download_config_files(url, [input_params_file, output_params_file, anomalous_params_file,
                                    experimentation_config_file])

        # load environment variables required for the execution
        db_config_params = load_environment_variables()

        # generate the experimentation set up
        if input_params_file is not None:
            # generate all possible simulation combinations
            experimentation_config = generate_all_simulation_combinations()
            if anomalous_params_file is not None:
                # set label to the simulations
                experimentation_config = set_labels(experimentation_config)
        else:
            experimentation_config = get_experimentation_config_from_csv()

        # create the database
        create_database(db_config_params)

        # get max simulation id to correctly assign the index to new generated simulations
        max_simulation_id = get_max_simulation_id(db_config_params)

        # insert generated simulations into the database
        insert_generated_simulations_into_db(experimentation_config, max_simulation_id, db_config_params)

        # create a SQL table to store simulation results
        create_table_query = generate_create_simulations_result_table_sql()
        execute_query(db_config_params, create_table_query)

        # create a SQL table to register simulation failures
        create_table_query = generate_create_simulations_failures_registry_table_sql()
        execute_query(db_config_params, create_table_query)

        # create stored procedures
        get_simulation_params_query = generate_stored_procedure_get_simulation_config()
        search_failed_simulations_query = generate_stored_procedure_search_failed_simulations()

        # apply the stored procedures
        execute_query(db_config_params, get_simulation_params_query)
        execute_query(db_config_params, search_failed_simulations_query)
    except Exception as error:
        print(error)
    else:
        print('The database has been configured successfully')


if __name__ == '__main__':
    main()
