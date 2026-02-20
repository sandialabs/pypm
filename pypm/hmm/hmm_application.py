import conin

from pypm.util.process_model import potentially_simultaneous_activities
from pypm.util.run_simian import create_data_wrapper

# import pyomo.environ as pe
# from .matching_models import ProcessModelData, GSF_TotalMatchScore
# from munch import Munch
# from pypm.simian import Simian
# import random
# import contextlib
# import sys
# import copy
# import numpy as np
# from dataclasses import dataclass, field
# from typing import Any
# import time
# import math
# import heapq
# import pandas as pd
# import matplotlib.pyplot as plt
# from conin.util import Util
##import ast
# import json


# TODO the naming conventions are ALL over the place right now
# TODO write tests
# TODO do start probabilities better in simulations. We currently only allow for starting in either no process or all of the first processes allowed.
# TODO I don't think I use delay after timesteps right now


class Data_Wrapper:
    """
    This is used to get info out of data that is passed to the HMM application

    num_time_steps: length of first observation, this may need to change if obervations can be different lengths
    lower_times: array of lower bounds on process times
    upper_times: array of upper bounds on process times
    delays_times: array of delay times after a process has run
    process_names: maps from array index to a process name
    process_parents: array of process dependencies
    index_to_process_names: inverse of process_names
    resources: list of all resources
    observation: alternate representation which is a list of frozensets of resources for each time step
    known_process_features: used to help start emission probs

    Also sets random's seed
    """

    def __init__(self, data):
        self.data = data

        # There are a couple of ways you could do this
        for val in self.data["obs"]["observations"].keys():
            self.num_time_steps = len(self.data["obs"]["observations"][val])

        self.lower_times = []
        self.upper_times = []
        self.delay_times = []
        self.process_names = []
        self.process_parents = []

        for activity in self.data.pm.data()["activities"]:
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

        self.resources = list(self.data["obs"]["observations"].keys())

        unformatted_observation = self.data["obs"]["observations"]
        self.observation = [set() for t in range(self.num_time_steps)]
        for resource, resource_list in unformatted_observation.items():
            for t, val in enumerate(resource_list):
                if val:
                    self.observation[t].add(resource)
        self.observation = [frozenset(val) for val in self.observation]

        if data.known_process_features is not None:
            self.known_process_features = data.known_process_features
        else:
            self.known_process_features = None
        if data.possible_process_features is not None:
            self.possible_process_features = data.known_process_features
        else:
            self.possible_process_features = None

        self.hmm_options = data.hmm_options

        random.seed(self.data.seed)


class BaseHMMApplication(conin.hmm.HMMApplication):

    def initialize(self, config, simulations):
        self._config = config
        self.data_wrapper = create_data_wrapper(config=config)
        self.simulations = simulations

    def _estimate_hidden_states(self, simulations=None):
        if simulations:
            tmp = set()
            for simulation in self.simulations:
                for hidden_state in simulation:
                    tmp.add(hidden_state)
            return list(tmp)

        else:
            return potentially_simultaneous_activities(self._config.pm)

    def run_simulations(
        self, *, num=1, debug=False, with_observations=False, seed=None
    ):
        return run_simian(
            num=num, debug=debug, with_observations=with_observations, seed=seed
        )


def GSF_oracle_constraints(data_wrapper, hidden_states):
    """
    Sets the constraints to be used in a constrained hmm
    """

    def always_appears_before_set(seq, val1, val2):
        """
        Note that here we can't use the common constraint becuase the hidden
        states are sets rather than values. However, it is basically the same
        as that function.

        val1 always appears before val2
        """
        for index1, x1 in enumerate(seq):
            if val2 in x1:
                for index2 in range(index1, len(seq)):
                    if val1 in seq[index2]:
                        return False
                return True
        return True

    def cont(seq):
        """
        This requires that a process occurs without breaks.
        This is certainly not true all the time, but is the model choice we are making right now.
        """
        finished = set()
        for index, X in enumerate(seq):
            if index < len(seq) - 1:
                finishing = X - seq[index + 1]
                if finishing & finished:
                    return False
                else:
                    finished = finished | finishing
        return True

    def length_lb(seq, val, lb):
        """
        Determines that val doesn't appear too many times
        TODO take in the number of time steps
        """

        length = 0
        for X in seq:
            if val in X:
                length += 1
        return length >= lb

    def length_lb_cont(seq, val, lb):
        """
        Use this one if your process is continuous
        Determines that val doesn't appear too many times
        TODO this is hacky, fix it
        """
        if val not in seq[-1]:
            length = 0
            for X in seq:
                if val in X:
                    length += 1
            if length != 0:
                return length >= lb
        return True

    def length_ub(seq, val, ub):
        """
        Determines that val doesn't appear too much
        """
        length = 0
        for X in seq:
            if val in X:
                length += 1
            if length > ub:
                return False
        return True

    def at_least_one(seq):
        """
        Determines that we run at least one process
        """
        for X in seq:
            if X != frozenset():
                return True
        return False

    def all_processes(seq, process_names):
        """
        Requires that all processes are run
        """
        processes = set()
        for X in seq:
            processes = processes.union(X)
        return processes == set(process_names)

    constraints = []

    constraints.append(
        conin.Constraint(func=lambda seq: cont(seq), same_partial_as_func=True)
    )

    for i, name in enumerate(data_wrapper.process_names):

        constraints.append(
            conin.Constraint(
                func=lambda seq, name=name, i=i: length_lb_cont(
                    seq, name, data_wrapper.lower_times[i]
                ),
                same_partial_as_func=True,
            )
        )

        constraints.append(
            conin.Constraint(
                func=lambda seq, name=name, i=i: length_ub(
                    seq, name, data_wrapper.upper_times[i]
                ),
                same_partial_as_func=True,
            )
        )

    for i, name in enumerate(data_wrapper.process_names):
        for j, parent_name in enumerate(data_wrapper.process_parents[i]):
            constraints.append(
                conin.Constraint(
                    func=lambda seq, parent_name=parent_name, name=name: always_appears_before_set(
                        seq, parent_name, name
                    ),
                    same_partial_as_func=True,
                )
            )

    # constraints.append(conin.Constraint(func=lambda seq: at_least_one(seq))

    constraints.append(
        conin.Constraint(
            func=lambda seq, hidden_states=hidden_states: all_processes(
                seq, data_wrapper.process_names
            )
        )
    )

    return constraints


def GSF_pyomo_constraints(data_wrapper, hidden_states):

    @pyomo_constraint_fn
    def constraints(data):
        # TODO HERE
        pass

    return [constraints]


def initialize_hmm_application(data, simulations=None):
    hmm_app = GSF_HMMApplication(data=data, simulations=simulations)
    hmm_app.learn_hmm()
    return hmm_app


class GSF_HMMApplication(BaseHMMApplication):

    def __init__(self, *, data, simulations=None):
        super().__init__(self.__class__.__name__)
        self.initialize(data, simulations)
        self._oracle_constraint_fn = GSF_oracle_constraints
        self._pyomo_constraint_fn = GSF_pyomo_constraints

    def get_oracle_constraints(self):
        return self._oracle_constraint_fn(self.data_wrapper, self._hidden_states)

    def get_pyomo_constraints(self):
        return self._pyomo_constraint_fn(self.data_wrapper, self._hidden_states)


class XPypm_BaseHMMApplication(conin.hmm.HMMApplication):

    def learn_hmm(self, *, with_constraints=False, noisy=True):
        """
        Outputs the learned hmm
        Also updates hmm in the class
        """
        if "hmm_read_in_file" in self.data_wrapper.hmm_options.keys():
            self.hmm = conin.HMM()
            self.read_hmm_from_file(self.data_wrapper.hmm_options["hmm_read_in_file"])
        else:
            self.learned_with_constraints = with_constraints

            if self.simulations is None:
                self._set_simulations()

            self._set_hidden_states()
            print("Finding transition probabilities.")
            if with_constraints:
                self._set_constraints()
            self._set_transition_probs_and_start_probs()
            print("Finding Emission probabilities")
            self._set_emission_probs_dict()

            self._set_hmm(no_zeros=False, no_zeros_tol=1e-6)
            self.write_hmm_to_file("../data/hmm.json")

        # self.print_inference_figs()

    def print_inference_figs(self):
        """
        Prints a Gantt chart which describes the inferred solutions
        If learn_hmm is run without constraints, we do inference both
        with and without constraints.

        TODO add a clear constraints option
        """
        if not self.learned_with_constraints:
            self.save_inferred_solutions_fig("inferred_unconstrained")
            self._set_constraints()
            self.hmm_app.update_constraints(self.constraints)
        self.save_inferred_solutions_fig("inferred_constrained")

    def _set_simulations(self):
        """
        Runs simulations based on simian and then stores the relevant information in
        self.simian_simulation.

        self.simulation is of the form
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
        simName, startTime, endTime, minDelay = (
            "simple_process",
            0,
            self.data_wrapper.num_time_steps
            + 1,  # TODO I think this code is riddled with off by one errors right now
            0.0001,
        )
        simianEngine = Simian(simName, startTime, endTime, minDelay)

        def base_process(this, main, id):
            """
            Process used by Simian
            """
            entity = this.entity
            process_time = random.randrange(main.lower_times[id], main.upper_times[id])
            start_time = str(entity.engine.now)
            main.unfinished_processes.remove(id)
            this.sleep(process_time)
            main.finished_processes.add(id)
            end_time = str(entity.engine.now - 1)
            main.output.append([main.process_names[id], str(start_time), str(end_time)])
            this.sleep(main.delay_times[id])
            main.run()

        class Main(simianEngine.Entity):
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
                self.upper_times = [
                    val + 1 for val in data_wrapper.upper_times
                ]  # TODO is this right???
                self.delay_times = data_wrapper.delay_times

                # Output is the actual run data we get from the simulation
                self.output = []

                self.finished_processes = set()
                self.unfinished_processes = {i for i in range(len(self.process_names))}
                # Running processes are implicity those not in either set
                # CLM: I don't think we have a reason to access them with the current setup

            def run(self, *args):
                to_run = set()
                for id in self.unfinished_processes:
                    if self.process_parents[id].issubset(self.finished_processes):
                        to_run.add(id)

                # TODO make sure this is randomizing the order we run in, otherwise we could underrepresent certain transitions
                for id in to_run:
                    self.createProcess(self.process_names[id], base_process)
                    self.startProcess(self.process_names[id], self, id)

        unformatted_simulations = []
        for i in range(self.num_simulations):
            simianEngine.addEntity("Main", Main, 0, self.data_wrapper)
            start_delay_time = random.randrange(0, 20)
            simianEngine.schedService(start_delay_time, "run", None, "Main", 0)
            with suppress_stdout():  # Don't want all the Simian prints
                simianEngine.run()
            unformatted_simulations.append(simianEngine.entities["Main"][0].output)
            simianEngine.exit()
            simianEngine = Simian(simName, startTime, endTime, minDelay)

        # CLM: This could be faster, but it's fine for now
        self.simulations = []
        for i in range(self.num_simulations):
            simulation = []
            for t in range(self.data_wrapper.num_time_steps):
                process_set = set()
                for process in unformatted_simulations[i]:
                    if (
                        int(process[1]) <= t and int(process[2]) >= t
                    ):  # TODO is this what we want??
                        process_set.add(process[0])
                simulation.append(frozenset(process_set))

            self.simulations.append(simulation)

    def _set_emission_probs_dict(self):
        """
        Creates an vector of emissions matrices indexed by resources
        Uses inference to get the most likely sequence of hidden states
        From this sequence, it updates the parameters of each emission mat while keeping the start probs and transition mat the same
        """
        # TODO figure out a better way to deal with these
        eps = 0.01
        num_solutions = 1
        max_iterations = 100
        # These are used to initalize the matrices
        # They could be more nuanced as well
        false_emission_guess = 0.01
        known_positive_guess = 0.9
        possible_positive_guess = 0.5
        other_positive_guess = 1e-6

        true_positive = {}  # These will uniquely define the emission matrices
        false_emission = {}
        for resource in self.data_wrapper.resources:
            false_emission[resource] = false_emission_guess

        for name in self.data_wrapper.process_names:
            for resource in self.data_wrapper.resources:
                if self.data_wrapper.known_process_features is None:
                    true_positive[(name, resource)] = 0.8

                else:
                    if resource in self.data_wrapper.known_process_features[name]:
                        true_positive[(name, resource)] = known_positive_guess
                    elif resource in self.data_wrapper.possible_process_features[name]:
                        true_positive[(name, resource)] = possible_positive_guess
                    # else:
                    #    true_positive[(name, resource)] = other_positive_guess

        self.hmm_app = Process_Matching_HMM()
        self.hmm_app.initialize(
            start_probs=self.start_probs,
            transition_probs=self.transition_probs,
            constraints=self.constraints,
            true_positive=true_positive,
            false_emission=false_emission,
        )

        num_it = 0
        while num_it < max_iterations:
            num_it += 1

            # Calculate new true_positive, false_emission
            old_false_emission = {
                key: val for key, val in self.hmm_app._false_emission.items()
            }
            old_true_positive = {
                key: val for key, val in self.hmm_app._true_positive.items()
            }
            self.hmm_app.SAEM_step(
                observation=self.data_wrapper.observation,
                num_solutions=num_solutions,
                iteration=num_it,
            )

            # l1 error
            # TODO: l2?
            error = 0
            for o in self.data_wrapper.resources:
                error = max(
                    error,
                    abs(old_false_emission[o] - self.hmm_app._false_emission[o]),
                )
                # if abs(old_false_emission[o] - self.hmm_app._false_emission[o]) > (1 - 1E-3)/num_it:
                #    print(o)
                for h in self.data_wrapper.process_names:
                    if (h, o) in old_true_positive.keys() and (
                        h,
                        o,
                    ) in self.hmm_app._true_positive.keys():
                        error = max(
                            error,
                            abs(
                                old_true_positive[(h, o)]
                                - self.hmm_app._true_positive[(h, o)]
                            ),
                        )
                        # if abs(old_true_positive[(h, o)] - self.hmm_app._true_positive[(h, o)]) > (1 - 1E-3)/num_it:
                        #    print(f"{h}, {o}")
            print(f"Error {error}, iteration {num_it}")
            if error < eps:
                print("Number of iterations: ", num_it)
                self._true_positive = self.hmm_app._true_positive
                self._false_emission = self.hmm_app._false_emission
                break

    def _set_hidden_states(self):
        """
        Just runs through self.simulations and sets self._hidden_states
        which consists of a list of frozen sets
        """
        self._hidden_states = set()
        for simulation in self.simulations:
            for hidden_state in simulation:
                self._hidden_states.add(hidden_state)
        self._hidden_states = list(self._hidden_states)

    def _set_transition_probs_and_start_probs(self):
        """
        Based on self.simulations

        We gives a fake observations vec and then just regard the emissions matrix,
        because that's easier than writing a new function

        Pad out simulations with no tasks at the end
        """
        self.conin_simulations = []
        for i, simulation in enumerate(self.simulations):
            while len(simulation) < self.data_wrapper.num_time_steps:
                simulation.append(frozenset())

            if len(simulation) > self.data_wrapper.num_time_steps:
                raise ValueError("The simulations are too long")

            observations = ["dummy observation"] * len(simulation)
            conin_simulation = Munch(hidden=simulation, observed=observations, index=i)
            self.conin_simulations.append(conin_simulation)
        temp_hmm = conin.supervised_learning(
            simulations=self.conin_simulations,
            hidden_states=self._hidden_states,
            observable_states={"dummy observation"},
            transition_tolerance=0,
            start_tolerance=0,
        )
        self.start_probs = temp_hmm.get_start_probs()
        self.transition_probs = temp_hmm.get_transition_probs()

    def _set_hmm(self, *, no_zeros=False, no_zeros_tol=1e-6):
        """
        This is the output of learn_hmm.
        The observations are only the observations we observe and the observation
        matrix is generated from false emission and true positive. However
        by having an actual observation matrix, we can use it in other things

        no_zeros: If true we run hmm.make_non_zero
        """
        self.hmm = conin.HMM()
        self._observed_states = {x for x in self.data_wrapper.observation}
        sparse_emission_probs = Sparse_Emissions_Matrix(
            true_positive=self._true_positive,
            false_emission=self._false_emission,
            hidden_states=self._hidden_states,
        )
        hmm_emission_probs = {}

        # We have to renormalize since we won't see all of the types of observations
        for h in self._hidden_states:
            sum = 0
            for o in self._observed_states:
                hmm_emission_probs[(h, o)] = sparse_emission_probs[(h, o)]
                sum += sparse_emission_probs[(h, o)]
            for o in self._observed_states:
                hmm_emission_probs[(h, o)] /= sum

        self.start_probs[frozenset()] = 1e-3
        self.start_probs = Util.normalize_dictionary(self.start_probs)

        self.hmm.load_model(
            start_probs=self.start_probs,
            transition_probs=self.transition_probs,
            emission_probs=hmm_emission_probs,
        )
        if no_zeros:
            self.hmm.make_non_zero(no_zeros_tol)

    def save_inferred_solutions_fig(self, file_name):
        hidden_vec = self.hmm_app.oracle_inference(
            observation=self.data_wrapper.observation, num_solutions=1
        )

        data = hidden_vec[0]
        print("Hidden: ", hidden_vec)
        print(
            f"Log probability: {self.hmm.log_probability(self.data_wrapper.observation, hidden_vec[0])}"
        )
        # Convert to a list of tasks with start and end times
        process_data = []
        processes_started = set()
        process_dict = {}

        for i, process_set in enumerate(data):
            for process in process_set:
                if process not in processes_started:
                    process_dict[process] = len(processes_started)
                    processes_started.add(process)
                    process_data.append({"Process": process, "Start": i, "End": -1})

        for t in range(len(data) - 1, -1, -1):
            for process in data[t]:
                if process_data[process_dict[process]]["End"] == -1:
                    process_data[process_dict[process]]["End"] = t + 1

        for process in processes_started:
            if process_data[process_dict[process]]["End"] == -1:
                process_data[process_dict[process]]["End"] = len(data)

        df = pd.DataFrame(process_data)
        print(df.head)

        # Create the Gantt chart
        fig, ax = plt.subplots(figsize=(10, 6))

        # Rotate date labels for better readability
        plt.xticks(rotation=45)

        # Rotate y-axis labels
        ax.tick_params(axis="y", labelrotation=45)

        # Plot each task
        for idx, task in df.iterrows():
            ax.barh(
                task["Process"],
                task["End"] - task["Start"],
                left=task["Start"],
            )

        # Add labels and title
        ax.set_xlabel("Time")
        ax.set_ylabel("Processes")
        ax.set_title("Gantt Chart")

        plt.savefig(file_name + ".png", format="png")  # Save as PNG file

    def write_hmm_to_file(self, file_name):
        """
        Writes the hmm to a file

        Note that here we have to convert frozensets to tuples b/c
        in read_hmm_from_file we use ast.literal_eval which doesn't like
        frozenset(). So, this is copied almost directly from hmm.
        """
        start_probs = self.hmm.get_start_probs()
        transition_probs = self.hmm.get_transition_probs()
        emission_probs = self.hmm.get_emission_probs()

        # Convert tuples to strings for JSON serialization
        # This gets a bit weird b/c hidden states can be strings or not strings whereas the keys for the other two
        # are always pairs
        start_probs_serializable = {str(list(k)): v for k, v in start_probs.items()}
        transition_probs_serializable = {}
        for k, v in transition_probs.items():
            a, b = k
            transition_probs_serializable[str((list(a), list(b)))] = v
        emission_probs_serializable = {}
        for k, v in emission_probs.items():
            a, b = k
            emission_probs_serializable[str((list(a), list(b)))] = v

        # Create a dictionary to hold all the data
        file_data = {
            "start_probs": start_probs_serializable,
            "transition_probs": transition_probs_serializable,
            "emission_probs": emission_probs_serializable,
        }

        with open(file_name, "w") as json_file:
            json.dump(file_data, json_file, indent=4)

    def read_hmm_from_file(self, file_name):
        """
        Reads the hmm from a file and returns the dictionaries.

        Note: This does not work if the states are frozensets b/c
        we would need to do a function call. Not sure how to fix that.

        Parameters:
            file_name: Name of the file we are reading from
        """

        # Read the data from the JSON file
        with open(file_name, "r") as json_file:
            file_data = json.load(json_file)

        # Convert string keys back to tuples
        start_probs = {
            frozenset(ast.literal_eval(k)): v
            for k, v in file_data["start_probs"].items()
        }

        transition_probs = {}
        for k, v in file_data["transition_probs"].items():
            a, b = ast.literal_eval(k)
            transition_probs[(frozenset(a), frozenset(b))] = v

        emission_probs = {}
        for k, v in file_data["emission_probs"].items():
            a, b = ast.literal_eval(k)
            emission_probs[(frozenset(a), frozenset(b))] = v

        self.hmm.load_model(
            start_probs=start_probs,
            transition_probs=transition_probs,
            emission_probs=emission_probs,
        )


class Process_Matching_HMM(conin.hmm.HMMApplication):
    # TODO: Printing

    def __init__(self):
        super().__init__(self.__class__.__name__)

    def initialize(
        self,
        *,
        transition_probs,
        start_probs,
        true_positive,
        false_emission,
        constraints,
    ):
        """
        true_positive is a dict from (activity, resource ) -> probability that an activity outputs that resource
        false_emission is a dict from resource -> probability we get an emission without any reason
        """
        self._observable_states = set(false_emission.keys())
        self._hidden_states = set(start_probs.keys())
        self._start_probs = start_probs
        self._transition_probs = transition_probs
        self._true_positive = true_positive
        self._false_emission = false_emission
        self._constraints = constraints

        self._processes = set()
        for X in self._hidden_states:
            for x in X:
                self._processes.add(x)

        self._set_allowed_transitions()

        self.update_statistical_models(
            true_positive=true_positive, false_emission=false_emission
        )

    def _set_allowed_transitions(self):
        """
        Useful as a sparse representation of
        """
        self._allowed_transitions = {}
        self._reverse_allowed_transitions = {}
        for h1 in self._hidden_states:
            self._allowed_transitions[h1] = set()
            self._reverse_allowed_transitions[h1] = set()
            for h2 in self._hidden_states:
                if self._transition_probs[(h1, h2)] > 0:
                    self._allowed_transitions[h1].add(h2)
                if self._transition_probs[(h2, h1)] > 0:
                    self._reverse_allowed_transitions[h1].add(h2)

    def update_statistical_models(self, *, true_positive=None, false_emission=None):
        """
        Recalculates the emissions matrix based on a new true positive and false emission rates
        Also updates the hmm and oracle_chmm
        """
        if true_positive is not None:
            self._true_positive = true_positive
        if false_emission is not None:
            self._false_emission = false_emission

        self._emission_probs = Sparse_Emissions_Matrix(
            true_positive=self._true_positive,
            false_emission=self._false_emission,
            hidden_states=self._hidden_states,
        )

        self._fake_emission_probs = {
            (h, "YOU SHOULD NOT SEE THIS"): 1 for h in self._hidden_states
        }
        self._fake_hmm = conin.HMM()
        self._fake_hmm.load_model(
            start_probs=self._start_probs,
            transition_probs=self._transition_probs,
            emission_probs=self._fake_emission_probs,
        )
        self._fake_oracle = conin.Oracle_CHMM(
            hmm=self._hmm, constraints=self._constraints
        )

    def update_constraints(self, constraints):
        """
        This also changes the statistical models, so we update those too.
        """
        self._constraints = constraints
        self.update_statistical_models()

    def SAEM_step(self, *, observation, iteration, num_solutions=1):
        """
        A single step of the SAEM algorithm
        Runs inference on observations, and then updates the true_positive and false_emission from that
        NOTE: this does not update the start probs and transition_probs
        This is because we assume they are already well-described by the Simian simulations
        """
        hidden_vec = self.oracle_inference(
            observation=observation, num_solutions=num_solutions
        )
        self._M_step(
            observation=observation, hidden_vec=hidden_vec, iteration=iteration
        )

    def oracle_inference(self, *, observation, num_solutions=1):
        """
        Runs the A* algorithm on self.oracle
        Doesn't necessarily need to be a member function, but I think it's helpful
        Returns a list of list of hidden states. If num_solutions is one, note that it is still a list of a list.

        CLM: This is a bit weird right now. Because we are using a sparse representation of the
        emissions matrix, we can't use the HMM class directly, because of the conversion to
        an internal HMM requires enumerating all the observed states, which is exponential in this
        case. This is copied from viterbi.py

        TODO: There has to be a better way to handle this without copying code...
        """
        max_iterations = None
        max_time = None
        debug = True
        beam_search = False
        beam_size = 1000

        start_time = time.time()

        # Initalize variables
        time_steps = len(observation)
        transition_mat = self._transition_probs
        emission_mat = self._emission_probs

        # Precompute V[t][h] - The log-probability of the shortest path starting at time
        #       t in hidden state h
        V = [{h: 0 for h in self._hidden_states} for t in range(time_steps)]

        # CLM: This is a nice hacky way to enforce that the sequence is finished at the end
        for h in self._hidden_states:
            V[time_steps - 1][h] = np.inf
        V[time_steps - 1][frozenset()] = 0

        print("Running Viterbi step")
        for t in range(time_steps - 2, -1, -1):
            if (time_steps - 2 - t) % 50 == 0:
                print(f"Iteration {time_steps-2-t} out of {time_steps-2}")
            obs = observation[t + 1]
            for h1 in self._hidden_states:
                temp = np.inf
                for h2 in self._allowed_transitions[h1]:
                    if emission_mat[(h2, obs)] != 0:
                        temp = min(
                            temp,
                            V[t + 1][h2]
                            - np.log(transition_mat[(h1, h2)])
                            - np.log(emission_mat[(h2, obs)]),
                        )
                V[t][h1] = temp

        # gScore - tuple hidden sequence -> negative log-probability
        #   Maps sequence of states already visited to negative log-probabilities
        gScore = dict()
        # openSet - heap of [value, seq] pairs, where 'value' is the negative log-probability of sequence 'seq'
        openSet = []

        # Initialize the heap with the starting states
        for h in self._hidden_states:
            tempGScore = np.inf
            if (self._start_probs[h] > 0) and (emission_mat[(h, observation[0])] > 0):
                tempGScore = -np.log(self._start_probs[h]) - np.log(
                    emission_mat[h, observation[0]]
                )
                # Use tuple here b/c Python doesn't hash a list
                gScore[(h,)] = tempGScore
                openSet.append(HeapItem(priority=tempGScore + V[0][h], seq=(h,)))
        heapq.heapify(openSet)

        iteration = 0
        n_infeasible = 0
        termination_condition = "unknown"
        output = []
        while True:
            val, seq = heapq.heappop(openSet)
            t = len(seq)

            if t == time_steps:
                if self._fake_oracle.is_feasible(seq):
                    output.append(Munch(hidden=seq, log_likelihood=-val))
                    if len(output) == num_solutions:
                        termination_condition = "ok"
                        break
                else:
                    n_infeasible += 1

            else:
                h1 = seq[t - 1]
                currentGScore = gScore[seq]
                obs = observation[t]
                for h2 in self._allowed_transitions[h1]:
                    if emission_mat[(h2, obs)] == 0.0:
                        continue
                    if self._fake_oracle.partial_is_feasible(T=time_steps, seq=seq):
                        tempGScore = (
                            currentGScore
                            - np.log(transition_mat[(h1, h2)])
                            - np.log(emission_mat[(h2, obs)])
                        )
                        newSeq = seq + (h2,)
                        gScore[newSeq] = tempGScore
                        heapq.heappush(
                            openSet,
                            HeapItem(priority=tempGScore + V[t][h2], seq=newSeq),
                        )

            iteration += 1

            if beam_search and iteration % beam_size == 0 and len(openSet) > beam_size:
                max_heap = [HeapItem(-item.priority, item.seq) for item in openSet]
                heapq.heapify(max_heap)

                # Remove the largest elements if the heap exceeds the max_size
                while len(max_heap) > beam_size:
                    heapq.heappop(max_heap)

                # Convert the max-heap back to a min-heap
                openSet[:] = [HeapItem(-item.priority, item.seq) for item in max_heap]
                heapq.heapify(openSet)

            if (max_iterations is not None) and (iteration >= max_iterations):
                termination_condition = f"max_iterations: {iteration}"
                break

            curr_time = time.time()
            if (max_time is not None) and ((curr_time - start_time) > max_time):
                termination_condition = f"max_time: {curr_time-start_time}"
                break

            if openSet == []:
                break

            if debug:
                if iteration % beam_size == 0:
                    print(f"  Iteration: {iteration}")
                    print(f"  # Heap:    {len(openSet)}")
                    print(f"  t:         {t}")
                    print(f"  val:       {val}")
                    print(f"  ninfeas:   {n_infeasible}")
                    print(f"  time:      {curr_time-start_time}")
                    # print(f"  sequence:  {seq}")
                    print()

        if len(output) < num_solutions:
            if num_solutions == 1:
                termination_condition = "error: no feasible solutions"
            else:
                termination_condition = "ok"

        ans = Munch(
            observations=observation,
            solutions=output,
            termination_condition=termination_condition,
        )

        print(termination_condition)
        return [output[i].hidden for i in range(len(output))]

    def _M_step(self, *, observation, hidden_vec, iteration):
        """
        Does the maximize step of the SAEM algorithm

        CLM: I pretty strongly believe that we can solve this algebraically,
        but the math is annoying and I can't figure it out right now.
        It's worth thinking about if this will be a computational bottleneck or not.

        CLM: This runs into numerical issues if lb is set to 0. I'm not entirely sure
        why, but every few runs, IPOPT would max out the number of iterations. However,
        if lb = 1/num_time_steps, this is the smallest we could expect a probability to
        be anyway.

        TODO: Bill, look at this and make sure I'm not doing anything terrible.

        TODO: Rounding?
        """
        num_time_steps = len(observation)
        lb = 0
        # lb = 1.0 / num_time_steps
        ub = 1 - lb  # This also seems to matter for some reason?

        model = pe.ConcreteModel()

        model.p = pe.Var(
            set(self._true_positive.keys()),
            initialize=self._true_positive,
            within=pe.NonNegativeReals,
            bounds=(lb, ub),
        )
        model.f = pe.Var(
            self._observable_states,
            initialize=self._false_emission,
            within=pe.NonNegativeReals,
            bounds=(lb, ub),
        )

        def log_prob(m):
            val = 0
            for hidden in hidden_vec:
                for o in self._observable_states:
                    for t in range(num_time_steps):
                        temp = 1 - m.f[o]
                        for h in hidden[t]:
                            if (h, o) in self._true_positive.keys():
                                temp *= 1 - m.p[(h, o)]

                        if o in observation[t]:
                            temp = 1 - temp

                        val += pe.log(temp)
            return val

        model.obj = pe.Objective(rule=log_prob, sense=pe.maximize)
        solver = pe.SolverFactory("ipopt")
        solver.solve(model, tee=True)

        # Could also probably just use
        new_false_emission = {key: -1 for key in self._false_emission.keys()}
        new_true_positive = {key: -1 for key in self._true_positive.keys()}

        for o in self._observable_states:
            if pe.value(model.f[o]) < lb:
                new_false_emission[o] = lb
            else:
                new_false_emission[o] = min(pe.value(model.f[o]), ub)
            for h in self._processes:
                if (h, o) in new_true_positive.keys():
                    if pe.value(model.p[(h, o)]) < lb:
                        new_true_positive[(h, o)] = lb
                    else:
                        new_true_positive[(h, o)] = min(pe.value(model.p[h, o]), ub)

        # Underweight as we go. This makes everything more numerically stable
        for o in self._observable_states:
            new_false_emission[o] = (
                new_false_emission[o] / iteration
                + self._false_emission[o] * (iteration - 1) / iteration
            )
            for h in self._processes:
                if (h, o) in new_true_positive.keys():
                    new_true_positive[(h, o)] = (
                        new_true_positive[(h, o)] / iteration
                        + self._true_positive[(h, o)] * (iteration - 1) / iteration
                    )

        self.update_statistical_models(
            false_emission=new_false_emission, true_positive=new_true_positive
        )


class Sparse_Emissions_Matrix:
    """
    This gets around the fact that otherwise the emissions matrix is exponentially large
    Rather than storing the entire matrix, we just store the desired parameters, and then
    compute on the fly
    """

    def __init__(self, *, true_positive, false_emission, hidden_states):
        self._true_positive = true_positive
        self._false_emission = false_emission
        self._observable_states = false_emission.keys()
        self._hidden_states = hidden_states

    def __getitem__(self, key):
        """
        Allows access to the matrix values using the syntax matrix[i, j].

        :param key: A tuple (i, j) representing the indices of the matrix.
        :return: The value at the specified indices.
        """
        if not isinstance(key, tuple) or len(key) != 2:
            raise KeyError("Key must be a tuple of two elements (i, j).")
        hidden_state = key[0]
        observed_state = key[1]

        val = 1
        for r in self._observable_states:
            temp = 1 - self._false_emission[r]
            for h in hidden_state:
                if (h, r) in self._true_positive.keys():
                    temp *= 1 - self._true_positive[(h, r)]
            if r in observed_state:
                val *= 1 - temp
            else:
                val *= temp
        return val

    def __iter__(self):
        """
        Allows iteration over the matrix, yielding pairs of indices.
        """
        for h in self._hidden_states:
            for o in self._observable_states:
                yield h, o
