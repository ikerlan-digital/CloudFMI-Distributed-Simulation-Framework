from kubernetes import client, config
from DB_Manager import truncate_database, execute_vacuum
from Config_Loader import load_environment_variables_aws
import yaml
import time
from pprint import pprint


def main():
    config_file_path = 'data/simulation_executor-agent-job.yaml'
    root_db_name = 'experimentation'
    agents_scalability_test = [32, 16, 8, 4, 2, 1]
    status_check_interval = 5
    max_iterations = 10
    db_config_params = load_environment_variables_aws()

    # config.load_kube_config()
    # k8s_client = client.BatchV1Api()
    # k8s_log_client = client.CoreV1Api()

    with open(config_file_path) as f:
        config_file_dict = yaml.safe_load(f)
        env_list = config_file_dict['spec']['template']['spec']['containers'][0]['env']

    try:

        for agents_number in agents_scalability_test:
            for iteration in range(1, max_iterations + 1):

                print('{0} agents on iteration {1}'.format(agents_number, iteration))
                # load connection configuration from kube config
                config.load_kube_config()

                # create a client for each API version
                k8s_client = client.BatchV1Api()
                k8s_log_client = client.CoreV1Api()

                # modify the configuration file according to the current scenario
                index = None

                for i in range(len(env_list)):
                    if env_list[i]['name'] == 'POSTGRESQL_DB_NAME':
                        index = i
                        break

                # we use a different database for each experiment
                db_name = '{0}_agents_{1}_iteration_{2}'.format(root_db_name, agents_number, iteration)
                job_name = 'experimentation-agents-{0}-iteration-{1}'.format(agents_number, iteration)
                namespace = 'default'

                config_file_dict['spec']['template']['spec']['containers'][0]['env'][index]['value'] = db_name
                config_file_dict['metadata']['name'] = job_name
                config_file_dict['spec']['parallelism'] = agents_number

                db_config_params['database'] = db_name

                # launch the job in Kubernetes
                response = k8s_client.create_namespaced_job(namespace, config_file_dict)
                print('Job launched:{0}'.format(job_name))
                # pprint(response)

                number_agents_finished = 0

                # wait until the job finishes. Status.Succeeded denotes the number of agents that finished the job
                # note that the connection to the API must be continuosly renewed due to the fact that the session
                # expires every few minutes
                while number_agents_finished is not agents_number:
                    config.load_kube_config()
                    k8s_client = client.BatchV1Api()
                    k8s_log_client = client.CoreV1Api()
                    time.sleep(status_check_interval)
                    response = k8s_client.read_namespaced_job_status(job_name, namespace)
                    number_agents_finished = response.status.to_dict()['succeeded']
                    # pprint(response.status)

                print('Job {0} finished'.format(job_name))

                # download agent's logs
                pod_list_response = k8s_log_client.list_namespaced_pod(namespace)
                pod_list_response_dict = pod_list_response.to_dict()
                print('Downloading logs...')
                for i in range(len(pod_list_response_dict['items'])):
                    pod_name = pod_list_response_dict['items'][i]['metadata']['name']
                    pod_log = k8s_log_client.read_namespaced_pod_log(pod_name, namespace)

                    with open('logs/{0}/agents-{1}/iteration-{2}/{3}.out'.format(root_db_name, agents_number, iteration, pod_name), 'w+') as f:
                        print('\t', pod_name)
                        f.write(pod_log)

                print('Logs downloaded')

                # delete pods
                print('Deleting pods...')
                del_pods_response = k8s_log_client.delete_collection_namespaced_pod(namespace)
                print('Pods deleted')
                # pprint(del_pods_response)

                # delete the job once is completed
                print('Deleting job...')
                del_job_response = k8s_client.delete_namespaced_job(job_name, namespace)
                print('Job deleted')
                # pprint(del_job_response)

                # remove all the results as we are executing the same simulations repeatedly. In this experimentation,
                # the results of the simulations are not important. We only care about execution time
                print('Truncating database {0} to remove simulation results...'.format(db_config_params['database']))
                truncate_database(db_config_params)
                print('Database truncated')
                print('\n\n')

    except Exception as error:
        print(error)
        k8s_log_client.delete_collection_namespaced_pod(namespace)
        k8s_client.delete_namespaced_job(job_name, namespace)


if __name__ == '__main__':
    main()

