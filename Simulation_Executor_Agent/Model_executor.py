import numpy as np


def simulate_model(model, **kwargs):
    """
    Creates a dictionary with the requested measurements, using the defined
    model and parameters.

    Parameters

        model
        FMU. FMU containing the model of the system to be monitored. (In python->
        model=load_fmu('path_to_FMU')).

        user_parameters ({})
        Dictionary. Dictionary with the parameters of the model to be set by the user
        and their value.

        initialState ([])
        np.array. Array with the initial states.

        final_time (5)
        final time of the simulation

    """
    defaults = {'initialState': [], 'final_time': 0.0, 'user_parameters': {}}

    defaults.update(kwargs)

    initial_state = np.array(defaults['initialState'])

    if not bool(defaults['final_time']):
        defaults['final_time'] = 5.0

    # Simulation options
    opts = model.simulate_options()
    opts['initialize'] = False
    opts['result_handling'] = 'memory'

    # set up model for the beginning of the simulation
    model.reset()
    model.setup_experiment()
    for sss in defaults['user_parameters']:
        model.set(sss, defaults['user_parameters'][sss])

    # initialize model
    model.initialize()
    if initial_state.size > 0:
        model.continuous_states = initial_state
    model.event_update()
    model.enter_continuous_time_mode()

    # simulate
    simulation_result = model.simulate(start_time=0.0, final_time=defaults['final_time'], options=opts)

    return simulation_result
