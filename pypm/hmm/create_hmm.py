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

from pypm.hmm import initial_emission_parameters
from pypm.hmm.matrix import Sparse_Emissions_Matrix


def _esimate_transition_and_start_probabilities(hidden_states, simulations):
    """
    Use simulations to estimate the transition and start probabilities.

    This uses supervised learning in conin, with dummy observations
    """
    conin_simulations = [
        Munch(hidden=sim, observed=[None] * len(sim), index=i)
        for i, sim in enumerate(simulations)
    ]

    hmm = conin.hmm.supervised_learning(
        simulations=conin_simulations,
        hidden_states=hidden_states,
        observable_states=[None],
        transition_tolerance=0,
        start_tolerance=0,
    )

    # Ensure that we have a non-zero probability of starting with an empty observation
    start_probs = hmm.get_start_probs()
    if start_probs[()] == 0.0:
        start_probs[()] = 1e-3
        start_probs = Util.normalize_dictionary(start_probs)

    return start_probs, hmm.get_transition_probs()


def estimate_hidden_state_parameters(*, simulations):
    #
    # Normalize simian simulations to only contain the states
    #
    simulations = [[state[1] for state in sim] for sim in simulations]
    #
    # Collect the states from the simulations, and keep them in an ordered list
    #
    # Ensure that the empty state, (), is included
    #
    _hidden_states = set({state for sim in simulations for state in sim})
    _hidden_states.add(())
    hidden_states = list(sorted(_hidden_states))

    start_probs, transition_probs = _esimate_transition_and_start_probabilities(
        hidden_states, simulations
    )

    return Munch(
        hidden_states=hidden_states,
        start_probs=start_probs,
        transition_probs=transition_probs,
    )


def create_hmm(
    *, observed, hidden_state_params, emission_params, no_zeros=False, no_zeros_tol=1e-6
):
    """
    The observations are only the observations we observe and the observation
    matrix is generated from false emission and true positive. However
    by having an actual observation matrix, we can use it in other things

    no_zeros: If true we run hmm.make_non_zero
    """
    observed_states = {x for x in observed}
    sparse_emission_probs = Sparse_Emissions_Matrix(
        true_positive=emission_params.true_positive,
        false_emission=emission_params.false_emission,
        hidden_states=hidden_state_params.hidden_states,
    )
    #
    # Create a dense emission matrix
    #
    # We have to renormalize since the observed sequence may not include all possible observed states
    #
    emission_probs = {}
    for h in hidden_state_params.hidden_states:
        total = 0
        for o in observed_states:
            tmp = emission_probs[h, o] = sparse_emission_probs[h, o]
            total += tmp
        for o in observed_states:
            emission_probs[h, o] /= total

    hmm = conin.hmm.HiddenMarkovModel()
    hmm.load_model(
        start_probs=hidden_state_params.start_probs,
        transition_probs=hidden_state_params.transition_probs,
        emission_probs=emission_probs,
    )
    if no_zeros:
        hmm.make_non_zero(no_zeros_tol)

    return hmm


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
        frozenset(ast.literal_eval(k)): v for k, v in file_data["start_probs"].items()
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


def initialize_hmm_application(data, simulations=None):
    hmm_app = Pypm_HMMApplication(data=data, simulations=simulations)
    hmm_app.learn_hmm()
    return hmm_app


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
