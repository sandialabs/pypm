import os
import munch
import random

from pypm.util.simian import Simian, Entity
from pypm.util.context_manager import suppress_stdout

"""
CLM: Some thoughts on parameterizing the transition matrix. We currently don't do this
even though we do parameterize the observation matrix. For instance you could parameterize 
each process by its expected length and the probability it starts. I don't think this is
a good idea. First, with Simian, we might see that two processes have heavy overlap in when
they are running. With this parameterization, we wouldn't be able to see that. Second, if two
processes are running, it might make both of them take longer, and parameterizing it
wouldn't account for that. I don't think Simian does currently account for it either, but 
we could, in theory, have a model that reflected this in the future, with a different simulation
generator (or a rework of Simian).
"""

# TODO the naming conventions are ALL over the place right now
# TODO write tests
# TODO do start probabilities better in simulations. We currently only allow for starting in either no process or all of the first processes allowed.
# TODO I don't think I use delay after timesteps right now


def create_data_wrapper(**kwds):

    class Data_Wrapper:
        """
        This is used to get info out of data that is passed to the HMM application

        num_time_steps: length of first observations
        lower_times: array of lower bounds on process times
        upper_times: array of upper bounds on process times
        delays_times: array of delay times after a process has run
        process_names: maps from array index to a process name
        process_parents: array of process dependencies
        index_to_process_names: inverse of process_names
        features: list of all features
        observation: a list of frozensets of features for each time step
        known_process_features: used to help start emission probs

        Also sets random's seed
        """

        def __init__(
            self, *, num_time_steps=None, config=None, pm=None, seed=None, features=None
        ):
            if config is None:
                config = munch.DefaultMunch(None, pm=pm)
            self.data = config

            self.lower_times = []
            self.upper_times = []
            self.delay_times = []
            self.process_names = []
            self.process_parents = []

            for activity in config.pm.data()["activities"]:
                if activity["duration"]["min_timesteps"] is not None:
                    self.lower_times.append(activity["duration"]["min_timesteps"])
                if activity["duration"]["max_timesteps"] is not None:
                    self.upper_times.append(
                        activity["duration"]["max_timesteps"]
                        # TODO is a plus 1 necessary?
                    )
                # Simian and pypm are off by one on upper_times which is very annoying
                if activity["delay_after_timesteps"] is not None:
                    self.delay_times.append(activity["delay_after_timesteps"])
                else:
                    self.delay_times.append(0)
                self.process_names.append(activity["name"])
                self.process_parents.append(set(activity["dependencies"]))

            self.index_to_process_names = {}
            for i in range(len(self.process_names)):
                self.index_to_process_names[self.process_names[i]] = i

            if "obs" in config:
                # There are a couple of ways you could do this
                for val in config["obs"]["observations"].keys():
                    self.num_time_steps = len(config["obs"]["observations"][val])

                self.features = list(config["obs"]["observations"].keys())

                unformatted_observation = config["obs"]["observations"]
                self.observation = [set() for t in range(self.num_time_steps)]
                for feature, feature_list in unformatted_observation.items():
                    for t, val in enumerate(feature_list):
                        if val:
                            self.observation[t].add(feature)
                self.observation = [frozenset(val) for val in self.observation]
            else:
                features = [] if features is None else features
                self.features = list(sorted(features))

            if num_time_steps is not None:
                self.num_time_steps = num_time_steps

            if config.known_process_features is not None:
                self.known_process_features = config.known_process_features
            else:
                self.known_process_features = {}
            if config.possible_process_features is not None:
                self.possible_process_features = config.possible_process_features
            else:
                self.possible_process_features = {}

            self.hmm_options = config.hmm_options

            if seed is not None:
                config.seed = seed

    return Data_Wrapper(**kwds)


def run_simian(
    *,
    data_wrapper=None,
    pm=None,
    num_simulations=1,
    num_time_steps,
    seed=None,
    max_delay_before=0,
    quiet=True,
):
    """
    Runs simulations based on simian and then stores the relevant information in
    simian_simulation.

    simulation is of the form
    [[(run0 ->) frozen set of processes running at time 0, frozen set of processes running at time 1, ... ]
    (run1 ->) frozen set of processes running at time 0, frozen set of processes running at time 1, ...]
    ,...]
    Note that the order of process_names might be permuted in different runs

    Start_time and end_time are inclusive, e.g. the process was actually running at that time
    CLM: I'm a bit confused on what exactly pypm is doing, so this will likely change at some point.
    TODO: Inclusive start and end times?

    TODO: Figure out how to deal with start_delay_time

    TODO: endTime for simianEngine
    """
    if pm is not None:
        data_wrapper = create_data_wrapper(
            pm=pm, num_time_steps=num_time_steps, seed=seed
        )
    else:
        data_wrapper.num_time_steps = num_time_steps

    if seed is not None:
        data_wrapper.data.seed = seed
    if data_wrapper.data.seed is not None:
        random.seed(data_wrapper.data.seed)

    def base_process(this, main, id):
        """
        Process used by Simian
        """
        entity = this.entity
        process_time = random.randrange(main.lower_times[id], main.upper_times[id] + 1)
        delay_before = (
            random.randrange(0, max_delay_before + 1) if max_delay_before > 0 else 0
        )
        start_time = entity.engine.now + delay_before
        main.unfinished_processes.remove(id)
        delay_after = main.delay_times[id]
        this.sleep(process_time + delay_before + delay_after)
        main.finished_processes.add(id)
        end_time = entity.engine.now - 1 - delay_after
        main.output.append(
            dict(name=main.process_names[id], start=start_time, end=end_time)
        )
        main.run()

    class Main(Entity):
        """
        Class to get Simian to work
        """

        def __init__(self, baseInfo, *args):
            super(Main, self).__init__(baseInfo)
            data_wrapper = args[0]
            self.process_names = data_wrapper.process_names
            self._name_to_index = {
                self.process_names[i]: i for i in range(len(self.process_names))
            }
            self.process_parents = [
                {self._name_to_index[name] for name in name_set}
                for name_set in data_wrapper.process_parents
            ]
            self.lower_times = data_wrapper.lower_times
            self.upper_times = data_wrapper.upper_times
            self.delay_times = data_wrapper.delay_times

            # Output is the actual run data we get from the simulation
            self.output = []

            self.finished_processes = set()
            self.unfinished_processes = {i for i in range(len(self.process_names))}
            # Running processes are implicity those not in either set
            # CLM: I don't think we have a reason to access them with the current setup

        def run(self, *args):
            to_run = [
                i
                for i in self.unfinished_processes
                if self.process_parents[i].issubset(self.finished_processes)
            ]

            random.shuffle(to_run)
            for i in to_run:
                self.createProcess(self.process_names[i], base_process)
                self.startProcess(self.process_names[i], self, i)

    #
    # Run simulations
    #
    simName = "simple_process"
    startTime = 0
    endTime = data_wrapper.num_time_steps + 1
    minDelay = 0.0001

    unformatted_simulations = []
    for i in range(num_simulations):
        simianEngine = Simian(simName, startTime, endTime, minDelay)
        simianEngine.addEntity("Main", Main, 0, data_wrapper)
        simianEngine.schedService(0, "run", None, "Main", 0)
        if quiet:
            with suppress_stdout():
                simianEngine.run()
        else:
            simianEngine.run()
            print(f"{simianEngine.entities['Main'][0].output}")
        unformatted_simulations.append(simianEngine.entities["Main"][0].output)
        simianEngine.exit()
    if os.path.exists(f"{simName}.0.out"):
        os.remove(f"{simName}.0.out")

    #
    # Collect tuples at each time step that show the activities being executed
    #
    simulations = []
    for i in range(num_simulations):
        simulation = [set() for _ in range(data_wrapper.num_time_steps)]
        for process in unformatted_simulations[i]:
            for t in range(process["start"], process["end"] + 1):
                if t == data_wrapper.num_time_steps:
                    break
                simulation[t].add(process["name"])
        simulations.append(
            list(enumerate(tuple(sorted(state)) for state in simulation))
        )

    return simulations
