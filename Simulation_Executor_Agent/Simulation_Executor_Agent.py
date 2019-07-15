import time
import signal
import datetime
import urllib.request
import shutil
import string
from random import *
from argparse import ArgumentParser
from pyfmi import load_fmu
from DB_Manager import *
from Config_Loader import load_environment_variables
from Model_executor import simulate_model


def time_out_signal_handler(signum, frame):
    """ It is triggered when a time out signal is caught. It throws a TimeoutError exception

        Args:
            signum (int): identifier of the alarm type
            frame (str): represent execution frames. They may occur in traceback objects
    """
    print("This simulation is Timed Out!")
    raise TimeoutError


def kill_program_signal_handler(signum, frame):
    """ It is triggered when the program is killed by the user. It throws a InterruptedError exception

        Args:
            signum (int): identifier of the alarm type
            frame (str): represent execution frames. They may occur in traceback objects
    """
    print("The program is being killed!")
    raise InterruptedError


def key_interrupt_signal_handler(signum, frame):
    """ It is triggered when the program is interrupted by the user. It throws a InterruptedError exception

        Args:
            signum (int): identifier of the alarm type
            frame (str): represent execution frames. They may occur in traceback objects
    """
    print("The program is being interrupted by de user!")
    raise InterruptedError


def get_argument_parser():
    """ Defines the arguments to be read by the application

        Returns:
            ArgumentParser: parser containing the input arguments of the application

    """
    parser = ArgumentParser()
    parser.add_argument("-m", "--model_path", help="URL of the file containing the model")

    return parser


def get_argsv(parser):
    """ Reads the input arguments of the application

        Args:
            parser (ArgumentParser): argument parser containing the input parameters to be read

        Returns:
            ArgumentParser: parser containing the input arguments of the application

    """
    args = parser.parse_args()

    path_to_model = args.model_path

    if path_to_model is not None:
        return path_to_model
    else:
        print('Not all arguments have been set. Use -h or --help flags to show help details')
        raise SystemExit(0)


def download_config_files(path_to_model_remote, path_to_model_local):
    """ Downloads the required files

        Args:
            path_to_model_remote (str): remote directory of the file to be downloaded
            path_to_model_local (str): local directory where the downloaded file is stored

    """
    # download simulation parameters file
    print("Downloading files...")
    print("\t", path_to_model_remote)
    with urllib.request.urlopen(path_to_model_remote) as response, open(path_to_model_local, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)
    print("Download completed")


def main():
    # create an argument parser
    parser = get_argument_parser()

    # read the arguments
    model_path_remote = get_argsv(parser)
    model_path_local = 'model/' + model_path_remote.split('/')[-1]

    # download configuration files
    download_config_files(model_path_remote, model_path_local)

    # load the model
    model = load_fmu(model_path_local)

    # load environment variables required for the execution
    db_config_params, simulation_environment_variables = load_environment_variables()

    # get the name of output variables
    output_params_names = get_output_params_names(db_config_params)

    # register signals
    signal.signal(signal.SIGALRM, time_out_signal_handler)  # signal to handel time outs
    signal.signal(signal.SIGINT, key_interrupt_signal_handler)  # signal to detect when the user presses CTRL+C
    signal.signal(signal.SIGHUP, kill_program_signal_handler)  # signal to detect when the program is killed

    # set time out in seconds
    time_out_period = 60 * int(simulation_environment_variables['time_out'])

    # generate a unique alphanumeric ID for the simulation executor agent
    id_length = 8
    all_char = string.ascii_letters + string.digits
    sea_id = "".join(choice(all_char) for x in range(id_length))

    while True:
        simulation_id = None
        try:
            start_time_get_config = time.time()
            # get next simulation parameters from db
            current_simulation_config = get_next_simulation_config(db_config_params)

            # check whether we have finished the simulation
            if current_simulation_config is None:
                if check_failed_simulations(db_config_params, simulation_environment_variables):
                    print(
                        "One or more failed simulations are found. They have been reset and they will be executed again")
                    continue
                else:
                    break
            get_config_execution_time = round((time.time() - start_time_get_config), 3)

            # start time out signal for a given period of time (seconds)
            signal.alarm(time_out_period)

            # start crono to calculate execution time
            start_time = time.time()
            timestamp = datetime.datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')

            # get simulation id and label
            simulation_id = current_simulation_config['simulation_id']
            label = current_simulation_config['label']

            # remove columns not required as model's input data
            del current_simulation_config['simulation_id']
            del current_simulation_config['timestamp_init']
            del current_simulation_config['timestamp_end']
            del current_simulation_config['state']
            del current_simulation_config['label']

            print("{0}: Executing simulation {1} with parameters:".format(timestamp, simulation_id))
            for key, value in current_simulation_config.items():
                print('\t\t\t\t\t\t', key, ':', value)

            # perform simulation
            simulation_output = simulate_model(model, user_parameters=current_simulation_config)

            # measure execution time in seconds
            execution_time = round((time.time() - start_time), 3)

            start_time_insert = time.time()
            # persist simulation results in the database
            insert_simulation_results(db_config_params, simulation_id, sea_id, execution_time,
                                      output_params_names, simulation_output, label)
            insert_time = round((time.time() - start_time_insert), 3)

            print('Execution time for getting the simulation configuration: {0}'.format(get_config_execution_time))
            print('Execution time for inserting the simulation results: {0}'.format(insert_time))
            # stop the alarm
            signal.alarm(0)

        except TimeoutError as error:
            print(error)
            print("This simulation exceeded the maximum execution time. Thus, it is aborted and marked as 'Failed'")
            rollback_simulation_state(db_config_params, simulation_id, sea_id, 'Time Out')

        except psycopg2.IntegrityError as error:
            print(error)
            print("This simulation was already done")
            update_simulation_state(db_config_params, simulation_id, 'Executed')

        except psycopg2.DatabaseError as error:
            print(error)
            rollback_simulation_state(db_config_params, simulation_id, sea_id, 'Database Error')

        except psycopg2.Error as error:
            rollback_simulation_state(db_config_params, simulation_id, sea_id, 'Database Error')
            print("psycopg2.Error: Execution aborted as a result of an irreversible error:\n\t{0}".format(error))
            break

        except KeyboardInterrupt:
            rollback_simulation_state(db_config_params, simulation_id, sea_id, 'User aborted')
            break

        except KeyError as error:
            print("KeyError: Execution aborted as a result of an irreversible error:\n\t{0}".format(error))
            break

        except Exception as error:
            # known issue: when a timeout signal is sent to the child process, it is not returned as such to the parent
            # process. In contrast, it is returned as a generic error. Thus, we assume that any general error caused
            # once the timeout period is exceeded is due to a timeout error.
            if (time.time() - start_time) > time_out_period:
                print("This simulation exceeded the maximum execution time. Thus, it is aborted and marked as 'Failed'")
                rollback_simulation_state(db_config_params, simulation_id, sea_id, 'Time Out')
            else:
                rollback_simulation_state(db_config_params, simulation_id, sea_id, 'Unknown')
                print("UnknownException: Execution aborted as a result of an irreversible error:\n\t{0}".format(error))
                break

        else:
            print('\nSimulation {0} finished!'.format(simulation_id))
            update_simulation_state(db_config_params, simulation_id, 'Executed')

    print('\n\nSIMULATION FINISHED')


if __name__ == '__main__':
    main()
