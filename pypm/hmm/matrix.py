# import conin.hmm

# import pprint
# from pypm.util.process_model import (
#    potentially_simultaneous_activities,
#    powerset,
# )
# import pyomo.environ as pe
# import conin
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

# import ast
# import json


class Sparse_Emissions_Matrix:
    """
    This gets around the fact that otherwise the emissions matrix is exponentially large
    Rather than storing the entire matrix, we just store the desired parameters, and then
    compute on the fly
    """

    def __init__(
        self, *, true_positive, false_emission, hidden_states, observed_states=None
    ):
        self._activities = set(a for h in hidden_states for a in h)
        # self._observed_states = observed_states
        if observed_states is None:
            assert (
                type(true_positive) is dict
            ), "true_positive must be a dictionary if observed_states is not specified"
            assert (
                type(false_emission) is dict
            ), "false_emission must be a dictionary if observed_states is not specified"
            self._true_positive = true_positive
            self._false_emission = false_emission
        else:
            assert (
                type(true_positive) is float
            ), "true_positive must be a float if observed_states is specified"
            assert (
                type(false_emission) is float
            ), "false_emission must be a float if observed_states is specified"
            tmp = set(o for state in observed_states for o in state)
            self._true_positive = {
                (a, o): true_positive for a in self._activities for o in tmp
            }
            self._false_emission = {o: false_emission for o in tmp}
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

        for h in hidden_state:
            if h not in self._activities:
                raise ValueError(f"Unexpected hidden state {h}")
        for o in observed_state:
            if o not in self._false_emission:
                raise ValueError(f"Unexpected observed_state state {o}")

        val = 1
        for o, fe in self._false_emission.items():
            temp = 1 - fe
            for h in hidden_state:
                temp *= 1 - self._true_positive.get((h, o), 0)
            if o in observed_state:
                val *= 1 - temp
            else:
                val *= temp
        return val

    def X__iter__(self):
        """
        Allows iteration over the matrix, yielding pairs of indices.
        """
        assert self._observed_states is not None, "Unspecified list of observed states"
        for h in self._hidden_states:
            for o in self._observed_states:
                yield h, o
