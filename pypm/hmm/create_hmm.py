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

from pypm.hmm.estimate_emissions import initial_emission_parameters
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
    *,
    hidden_state_params,
    emission_params,
    observed_states,
    no_zeros=False,
    no_zeros_tol=1e-6
):
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
