import conin.hmm

# import pprint
# from pypm.util.process_model import (
#    potentially_simultaneous_activities,
#    powerset,
# )
# import pyomo.environ as pe
# import conin
# from .matching_models import ProcessModelData, GSF_TotalMatchScore
from munch import Munch

# from pypm.simian import Simian
# import random
# import contextlib
# import sys
# import copy
# import numpy as np
from dataclasses import dataclass, field
from typing import Any

# import time
# import math
# import heapq
# import pandas as pd
# import matplotlib.pyplot as plt
from conin.util import Util

# import ast
# import json


def initial_emission_parameters(
    *, data_wrapper, false_emission=0.01, known_positive=0.9, possible_positive=0.5
):
    false_emission_guess = false_emission
    known_positive_guess = known_positive
    possible_positive_guess = possible_positive

    true_positive = {}
    false_emission = {}
    assert (
        len(data_wrapper.features) > 0
    ), f"Missing 'features' attribute in config data"
    for feature in data_wrapper.features:
        false_emission[feature] = false_emission_guess

    if len(data_wrapper.known_process_features) > 0:
        for name in data_wrapper.process_names:
            for feature in data_wrapper.features:
                if feature in data_wrapper.known_process_features.get(name, {}):
                    true_positive[name, feature] = known_positive_guess
                elif feature in data_wrapper.possible_process_features.get(name, {}):
                    true_positive[name, feature] = possible_positive_guess
    else:
        for name in data_wrapper.process_names:
            for feature in data_wrapper.features:
                true_positive[name, feature] = known_positive

    return Munch(true_positive=true_positive, false_emission=false_emission)


def estimate_emission_parameters(
    *, observed, data_wrapper, hidden_state_params, constraints=[]
):
    """
    Creates an vector of emissions matrices indexed by resources
    Uses inference to get the most likely sequence of hidden states
    From this sequence, it updates the parameters of each emission mat while keeping the start probs and transition mat the same
    """
    # TODO figure out a better way to deal with these
    eps = 0.01
    num_solutions = 1
    max_iterations = 100

    initial_params = initial_emission_parameters()
    true_positive = initial_params.true_positive
    false_emission = initial_params.false_emission

    hmm_app = Process_Matching_HMM()
    hmm_app.initialize(
        start_probs=hidden_state_params.start_probs,
        transition_probs=hidden_state_params.transition_probs,
        constraints=constraints,
        true_positive=true_positive,
        false_emission=false_emission,
    )

    num_it = 0
    while num_it < max_iterations:
        num_it += 1

        # Calculate new true_positive, false_emission
        old_false_emission = {key: val for key, val in hmm_app._false_emission.items()}
        old_true_positive = {key: val for key, val in hmm_app._true_positive.items()}
        hmm_app.SAEM_step(
            observation=observed,  # data_wrapper.observation
            num_solutions=num_solutions,
            iteration=num_it,
        )

        # l1 error
        # TODO: l2?
        error = 0
        for o in data_wrapper.resources:
            error = max(
                error,
                abs(old_false_emission[o] - hmm_app._false_emission[o]),
            )
            # if abs(old_false_emission[o] - hmm_app._false_emission[o]) > (1 - 1E-3)/num_it:
            #    print(o)
            for h in data_wrapper.process_names:
                if (h, o) in old_true_positive.keys() and (
                    h,
                    o,
                ) in hmm_app._true_positive.keys():
                    error = max(
                        error,
                        abs(old_true_positive[(h, o)] - hmm_app._true_positive[(h, o)]),
                    )
                    # if abs(old_true_positive[(h, o)] - hmm_app._true_positive[(h, o)]) > (1 - 1E-3)/num_it:
                    #    print(f"{h}, {o}")
        print(f"Error {error}, iteration {num_it}")
        if error < eps:
            print("Number of iterations: ", num_it)
            _true_positive = hmm_app._true_positive
            _false_emission = hmm_app._false_emission
            break

    return Munch(true_positive=_true_positive, false_positive=_false_positive)


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

    def __init__(
        self, *, true_positive, false_emission, hidden_states, observed_states=None
    ):
        if observed_states is None:
            self._true_positive = true_positive
            self._false_emission = false_emission
        else:
            assert type(true_positive) is float
            assert type(false_emission) is float
            self._true_positive = {
                (h, o): true_positive for h in hidden_states for o in observed_states
            }
            self._false_emission = {o: false_emission for o in observed_states}
        self._hidden_states = hidden_states

    def __getitem__(self, key):
        """
        Allows access to the matrix values using the syntax matrix[i, j].

        :param key: A tuple (i, j) representing the indices of the matrix.
        :return: The value at the specified indices.
        """
        if not isinstance(key, tuple) or len(key) != 2:
            raise KeyError("Key must be a tuple of two elements (i, j).")
        hidden_state, observed_state = key

        val = 1
        for o in self._false_emission:
            temp = 1 - self._false_emission[o]
            for h in hidden_state:
                if (h, o) in self._true_positive:
                    temp *= 1 - self._true_positive[h, o]
            if o in observed_state:
                val *= 1 - temp
            else:
                val *= temp
        return val

    def __iter__(self):
        """
        Allows iteration over the matrix, yielding pairs of indices.
        """
        for h in self._hidden_states:
            for o in self._false_emission:
                yield h, o


# A data class that only allows comparisons w.r.t. the priority value
@dataclass(order=True)
class HeapItem:
    priority: float
    seq: Any = field(compare=False)

    def __iter__(self):
        yield self.priority
        yield self.seq
