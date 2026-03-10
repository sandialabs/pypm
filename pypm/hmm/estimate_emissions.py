import sys
import random
import time
from dataclasses import dataclass, field
from typing import Any
import numpy as np
import heapq
from munch import Munch

import pyomo.environ as pe
import conin.hmm
from pypm.hmm.matrix import Sparse_Emissions_Matrix


def initial_emission_parameters(
    *, data_wrapper, false_emission=0.01, known_positive=0.9, possible_positive=0.5
):
    assert (
        len(data_wrapper.features) > 0
    ), f"Missing 'features' attribute in config data"

    # Setup dictionary of false_emission parameters
    if type(false_emission) is not dict:
        false_emission_guess = false_emission
        false_emission = {}
        for feature in data_wrapper.features:
            false_emission[feature] = false_emission_guess

    known_positive_guess = known_positive
    possible_positive_guess = possible_positive
    true_positive = {}

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
    *,
    observed,
    data_wrapper,
    transition_params,
    emission_params,
    config=None,
    constraints=[],
    max_iterations=None,
    num_solutions_per_step=None,
    num_random_restarts=5,
    debug=False,
    quiet=True,
    seed=None,
):

    if seed:
        random.seed(seed)

    if debug or not quiet:
        print("Estimating emission parameters - START")

    ans = Munch(true_positive=None, value=None)
    for i in range(num_random_restarts):
        if i == 0:
            # Perturb the initial true_positive values
            for k in emission_params.true_positive:
                emission_params.true_positive[k] *= random.uniform(0.9,1.0)
        else:
            # Generate random true_positive values
            for k in emission_params.true_positive:
                emission_params.true_positive[k] = random.random()
        ans_ = _estimate_emission_parameters_iter(
            observed=observed,
            config=config,
            data_wrapper=data_wrapper,
            transition_params=transition_params,
            emission_params=emission_params,
            constraints=constraints,
            max_iterations=max_iterations,
            num_solutions_per_step=num_solutions_per_step,
            quiet=quiet,
        )
        if debug or not quiet:
            print(f"Randomized iteration {i}")
            print(ans.true_positive)
            print(ans.value)
        if ans_.value is None:
            continue
        if ans.value is None or ans_.value > ans.value:
            ans = ans_

    if debug or not quiet:
        print("Estimating emission parameters - STOP")
        print("Final emission parameters")
        print(ans.true_positive)
        print(ans.value)
    return ans


def _estimate_emission_parameters_iter(
    *,
    observed,
    config,
    data_wrapper,
    transition_params,
    emission_params,
    constraints=[],
    max_iterations=None,
    num_solutions_per_step=None,
    debug=False,
    quiet=True,
):
    """
    Creates an vector of emissions matrices indexed by resources
    Uses inference to get the most likely sequence of hidden states
    From this sequence, it updates the parameters of each emission mat while keeping the start probs and transition mat the same
    """
    # TODO figure out a better way to deal with these
    eps = 0.01
    if max_iterations is None:
        max_iterations = 100
    if num_solutions_per_step is None:
        num_solutions_per_step = 1

    true_positive = emission_params.true_positive
    false_emission = emission_params.false_emission

    hmm_app = Process_Matching_HMM()
    hmm_app.initialize(
        start_probs=transition_params.start_probs,
        transition_probs=transition_params.transition_probs,
        constraints=constraints,
        true_positive=true_positive,
        false_emission=false_emission,
    )

    if debug or not quiet:
        print("SAEM START")

    num_it = 0
    while num_it < max_iterations:
        if debug or not quiet:
            print(f"SAEM - Iteration {num_it}")
        num_it += 1

        # Calculate new true_positive, false_emission
        old_true_positive = {key: val for key, val in hmm_app._true_positive.items()}
        status = hmm_app.SAEM_step(
            observation=observed,  # data_wrapper.observation
            config=config,
            num_solutions=num_solutions_per_step,
            iteration=num_it,
            debug=debug,
            quiet=quiet,
        )
        if status.error:
            print("Error running SAEM_step - no solutions generated")
            return Munch(true_positive=None, false_emission=false_emission, value=None)

        # l1 error
        # TODO: l2?
        error = 0
        for o in data_wrapper.features:
            for h in data_wrapper.process_names:
                if (h, o) in old_true_positive and (h, o) in hmm_app._true_positive:
                    error = max(
                        error,
                        abs(old_true_positive[h, o] - hmm_app._true_positive[h, o]),
                    )
        if debug or not quiet:
            print(f"Error {error}, iteration {num_it}")
        if error < eps:
            _true_positive = hmm_app._true_positive
            break

    if debug or not quiet:
        print("SAEM STOP")
        print("Number of iterations: ", num_it)

    return Munch(
        true_positive=_true_positive, false_emission=false_emission, value=status.value
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
                if self._transition_probs[h1, h2] > 0:
                    self._allowed_transitions[h1].add(h2)
                if self._transition_probs[h2, h1] > 0:
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
        self._fake_hmm = conin.hmm.HiddenMarkovModel()
        self._fake_hmm.load_model(
            start_probs=self._start_probs,
            transition_probs=self._transition_probs,
            emission_probs=self._fake_emission_probs,
        )
        self._fake_oracle = conin.hmm.chmm_oracle.Oracle_CHMM(
            hmm=self._fake_hmm.repn,
            constraints=self._constraints,
            hidden_to_external=self._fake_hmm.hidden_to_external,
            make_internal_constraint=False,
        )

    def update_constraints(self, constraints):
        """
        This also changes the statistical models, so we update those too.
        """
        self._constraints = constraints
        self.update_statistical_models()

    def SAEM_step(
        self,
        *,
        observation,
        config,
        iteration,
        num_solutions=1,
        debug=False,
        quiet=True,
    ):
        """
        A single step of the SAEM algorithm
        Runs inference on observations, and then updates the true_positive and false_emission from that
        NOTE: this does not update the start probs and transition_probs
        This is because we assume they are already well-described by the Simian simulations
        """
        if config is None:
            if debug or not quiet:
                print("SAEM_step - Oracle inference")
            hidden_vec = self.oracle_inference(
                observation=observation, num_solutions=num_solutions, debug=debug
            )
        else:
            if debug or not quiet:
                print("SAEM_step - Algebraic inference")
            # Configure the PypmHMMApplication object with the current estimate of true_positive
            config.hmm_app._emission_probs = Munch(
                true_positive=self._true_positive, false_emission=self._false_emission
            )
            # Initialize the HMM in the PypmHMMApplication object
            config.hmm_app._api.create_hmm()
            # Generate a schedule using optimization
            results = config.hmm_app._api.generate_schedule()
            # Collect results
            T = len(results["data"]["datetime"])
            hidden_vec = []
            for res in results["results"]:
                hidden = [set() for _ in range(T)]
                for h,val in res['schedule'].items():
                    if 'pre' in val or 'post' in val:
                        continue
                    for t in range(val['first'], val['last']+1):
                        hidden[t].add(h)
                hidden_vec.append(hidden)

        if len(hidden_vec) == 0:
            return Munch(error=True)
        if debug or not quiet:
            print("SAEM_step - M_step optimization")
        value = self._M_step(
            observation=observation,
            hidden_vec=hidden_vec,
            iteration=iteration,
            debug=debug,
        )
        if debug or not quiet:
            print("SAEM_step - DONE")
        return Munch(error=False, value=value)

    def oracle_inference(
        self,
        *,
        observation,
        num_solutions=1,
        debug=False,
        max_iterations=None,
        max_time=None,
        beam_search=False,
        beam_size=1000,
    ):
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
        start_time = time.time()

        # Initalize variables
        time_steps = len(observation)
        transition_mat = self._transition_probs
        emission_mat = self._emission_probs
        hidden_states = list(sorted(self._hidden_states))

        if debug:
            print("Running Viterbi step")
        #
        # Precompute V[t][h] - The log-probability of the shortest path starting at time
        #       t in hidden state h
        #
        V = [{h: 0 for h in hidden_states} for t in range(time_steps)]
        for t in range(time_steps - 2, -1, -1):
            if debug and (time_steps - 2 - t) % 50 == 0:
                print(f"Iteration {time_steps-2-t} out of {time_steps-2}")
            obs = observation[t + 1]
            for h1 in hidden_states:
                temp = np.inf
                for h2 in self._allowed_transitions[h1]:
                    if emission_mat[h2, obs] != 0:
                        temp = min(
                            temp,
                            V[t + 1][h2]
                            - np.log(transition_mat[h1, h2])
                            - np.log(emission_mat[h2, obs]),
                        )
                V[t][h1] = temp

        # gScore - tuple hidden sequence -> negative log-probability
        #   Maps sequence of states already visited to negative log-probabilities
        gScore = dict()
        # openSet - heap of [value, seq] pairs, where 'value' is the negative log-probability of sequence 'seq'
        openSet = []
        iteration = 0

        #
        # Initialize the heap with the starting states
        #
        for h in hidden_states:
            tempGScore = np.inf
            if (self._start_probs[h] > 0) and (emission_mat[h, observation[0]] > 0):
                seq = (h,)
                if debug:
                    print(
                        f"{iteration=} {time_steps=} {self._fake_oracle.partial_is_feasible(T=time_steps, seq=seq)}"
                    )
                    print(f"    {seq=}")
                    print(f"    {h=}")
                if self._fake_oracle.partial_is_feasible(T=time_steps, seq=seq):
                    tempGScore = -np.log(self._start_probs[h]) - np.log(
                        emission_mat[h, observation[0]]
                    )
                    gScore[seq] = tempGScore
                    heapq.heappush(
                        openSet, HeapItem(priority=tempGScore + V[0][h], seq=seq)
                    )

        n_infeasible = 0
        termination_condition = "unknown"
        output = []
        while len(openSet) > 0:
            iteration += 1
            if debug:
                print()

            val, seq = heapq.heappop(openSet)
            t = len(seq)
            if debug:
                print(f"{iteration=} {float(val)=} {seq=}")

            if t == time_steps:
                if self._fake_oracle.is_feasible(seq):
                    if debug:
                        print("*" * 40)
                        print(
                            f"{iteration=} {time_steps=} {self._fake_oracle.is_feasible(seq)} {len(openSet)}"
                        )
                        print(f"{seq=}")
                        print("*" * 40)
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
                    if emission_mat[h2, obs] == 0.0:
                        continue
                    newSeq = seq + (h2,)
                    if debug:
                        print(f"{h2=}")
                        print(
                            f"    {time_steps=} {emission_mat[h2,obs]=} {self._fake_oracle.partial_is_feasible(T=time_steps, seq=newSeq)} {len(openSet)}"
                        )
                        print(f"    {seq=}")
                        print(f"    {currentGScore=}")
                        print(f"    {newSeq=}")
                        print(f"    {obs=}")
                    if self._fake_oracle.partial_is_feasible(T=time_steps, seq=newSeq):
                        tempGScore = (
                            currentGScore
                            - np.log(transition_mat[h1, h2])
                            - np.log(emission_mat[h2, obs])
                        )
                        gScore[newSeq] = tempGScore
                        if debug:
                            print(
                                f"    {tempGScore=} {V[t][h2]=} {tempGScore + V[t][h2]}"
                            )
                        heapq.heappush(
                            openSet,
                            HeapItem(priority=tempGScore + V[t][h2], seq=newSeq),
                        )

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
                if iteration == 0:
                    print(f"  Iteration: {iteration}")
                    print(f"  # Heap:    {len(openSet)}")
                    print(f"  t:         {t}")
                    print(f"  val:       {val}")
                    print(f"  ninfeas:   {n_infeasible}")
                    print(f"  time:      {curr_time-start_time}")
                    print()

        if len(output) < num_solutions:
            if num_solutions == 1:
                termination_condition = "error: no feasible solutions"
            else:
                termination_condition = "ok"
        if debug:
            print(f"{termination_condition=}")

        # ans = Munch(
        #    observations=observation,
        #    solutions=output,
        #    termination_condition=termination_condition,
        # )

        return [output[i].hidden for i in range(len(output))]

    def _M_step(self, *, observation, hidden_vec, iteration, debug=False):
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
        lb = 1e-6
        # lb = 1.0 / num_time_steps
        ub = 1  # This also seems to matter for some reason?

        if debug:
            print("M_step data")
            print(f"{self._true_positive=}")
            print(f"{self._false_emission=}")
            print(f"{self._observable_states=}")
            print(f"{num_time_steps=}")
            print(f"{hidden_vec=}")

        model = pe.ConcreteModel()

        A = list(sorted(self._true_positive.keys()))
        model.p = pe.Var(
            A,
            initialize=self._true_positive,
            within=pe.NonNegativeReals,
            bounds=(lb, ub),
        )
        B = list(sorted(self._observable_states))

        def log_prob(m):
            val = 0
            for hidden in hidden_vec:
                for t in range(num_time_steps):
                    for o in B:
                        tp = [
                            m.p[h, o]
                            for h in hidden[t]
                            if (h, o) in self._true_positive
                        ]
                        if len(tp) == 0:
                            continue  # Empty list, so this term is constant

                        temp = 1 - self._false_emission[o]
                        for p in tp:
                            temp *= 1 - p
                        if o in observation[t]:
                            temp = 1 - temp

                        val += pe.log(temp)

            # Add terms for true_positive variables that are not added in the log-likelihood
            # This biases their value to 1.0
            tmp = {(h,o) for t in range(num_time_steps) for h in hidden[t] for o in B if (h,o) in self._true_positive}
            val += sum(m.p[h,o] for (h,o) in self._true_positive if (h,o) not in tmp)
            return val

        model.obj = pe.Objective(rule=log_prob, sense=pe.maximize)

        solver = pe.SolverFactory("ipopt")
        solver.solve(model, tee=debug)
        if debug:
            print("Pyomo model information")
            model.pprint()
            model.display()

        # Could also probably just use
        new_true_positive = {key: lb for key in self._true_positive}

        for o in self._observable_states:
            for h in self._processes:
                if (h, o) in new_true_positive:
                    if pe.value(model.p[h, o]) < lb:
                        new_true_positive[h, o] = lb
                    else:
                        new_true_positive[h, o] = min(pe.value(model.p[h, o]), ub)

        # Underweight as we go. This makes everything more numerically stable
        for o in self._observable_states:
            for h in self._processes:
                if (h, o) in new_true_positive:
                    new_true_positive[h, o] = (
                        new_true_positive[h, o] / iteration
                        + self._true_positive[h, o] * (iteration - 1) / iteration
                    )

        self.update_statistical_models(
            false_emission=self._false_emission, true_positive=new_true_positive
        )

        return pe.value(model.obj)


# A data class that only allows comparisons w.r.t. the priority value
@dataclass(order=True)
class HeapItem:
    priority: float
    seq: Any = field(compare=False)

    def __iter__(self):
        yield self.priority
        yield self.seq
