import json
import munch
import conin.hmm

from pypm.hmm.create_hmm import estimate_transition_parameters, create_hmm
from pypm.hmm.estimate_emissions import (
    initial_emission_parameters,
    estimate_emission_parameters,
)
from pypm.util.run_simian import create_data_wrapper, run_simian


def initialize_hmm_application(name):
    # TODO - Customize this for XSF?
    return PypmHMMApplication()


class PypmHMMApplication:

    def initialize(self, config):
        self._config = config
        self.data_wrapper = create_data_wrapper(config=config)
        if hasattr(config, "features"):
            self.data_wrapper.features = getattr(config, "features", {})
        self.transition_params = None
        self.emission_params = None
        self.simulations = None
        self.data = munch.Munch()
        self.false_emission_probability = 1e-3

    def learn_transition_parameters(
        self,
        *,
        num_simulations,
        seed,
        max_delay_before=5,
        quiet=True,
        debug=False,
    ):
        self.simulations = run_simian(
            data_wrapper=self.data_wrapper,
            num_simulations=num_simulations,
            seed=seed,
            max_delay_before=max_delay_before,
            quiet=quiet,
        )
        self.transition_params = estimate_transition_parameters(
            simulations=self.simulations
        )
        self.data.options_learn_transition_parameters = dict(
            num_simulations=num_simulations,
            max_delay_before=max_delay_before,
            debug=debug,
        )

    def learn_emission_parameters(
        self,
        *,
        observed,
        false_emission_probability=1e-3,
        constrained=True,
        schedule_all_activities=True,
        num_random_restarts=3,
        max_iterations=None,
        num_solutions_per_step=None,
        debug=False,
        quiet=True,
        seed=None,
    ):
        constraints = (
            [] if not constrained else self.oracle_constraints(schedule_all_activities)
        )

        if self.emission_params is None:
            self.emission_params = initial_emission_parameters(
                data_wrapper=self.data_wrapper,
                false_emission=false_emission_probability,
            )

        API = getattr(self, "_api", None)
        config = None if API is None else API.config

        self.emission_params = estimate_emission_parameters(
            config=config,
            observed=observed,
            data_wrapper=self.data_wrapper,
            emission_params=self.emission_params,
            transition_params=self.transition_params,
            num_random_restarts=num_random_restarts,
            constraints=constraints,
            max_iterations=max_iterations,
            num_solutions_per_step=num_solutions_per_step,
            debug=debug,
            quiet=quiet,
            seed=seed,
        )

    def create_hmm(self, observed_states=None, no_zeros=False, no_zeros_tol=1e-6):
        assert (
            self.transition_params is not None
        ), "ERROR: must learn transition parameters before creating the HMM"
        if observed_states is None:
            assert (
                hasattr(self.data_wrapper, "observed_states")
                and self.data_wrapper.observed_states is not None
            ), "If observed_states is not specified, then data observations must be included in the config object"
            observed_states = self.data_wrapper.observed_states

        if self.emission_params is None:
            self.emission_params = initial_emission_parameters(
                data_wrapper=self.data_wrapper,
                false_emission=self.false_emission_probability,
            )

        self.hmm = create_hmm(
            transition_params=self.transition_params,
            emission_params=self.emission_params,
            observed_states=observed_states,
            no_zeros=no_zeros,
            no_zeros_tol=1e-6,
        )
        self.observed_states = observed_states
        self.data.options_create_hmm = dict(
            no_zeros=no_zeros, no_zeros_tol=no_zeros_tol
        )

    def write(self, filename):
        tmp = munch.Munch(
            transition_params=dict(
                hidden_states=self.transition_params.hidden_states,
                start_probs=list(sorted(self.transition_params.start_probs.items())),
                transition_probs=list(
                    sorted(self.transition_params.transition_probs.items())
                ),
            ),
            emission_params=dict(
                false_emission=list(
                    sorted(self.emission_params.false_emission.items())
                ),
                true_positive=list(sorted(self.emission_params.true_positive.items())),
            ),
            data=self.data,
            simulations=self.simulations,
            hmm=self.hmm.to_dict(),
        )
        with open(filename, "w") as OUTPUT:
            json.dump(tmp.toDict(), OUTPUT, indent=4)

    def read(self, filename):
        with open(filename, "r") as INPUT:
            tmp = json.load(INPUT)
            tmp = munch.DefaultMunch.fromDict(tmp, None)
            self.data = tmp.data

            # simulations
            self.simulations = [
                [(t, tuple(val)) for t, val in sim] for sim in tmp.simulations
            ]

            # transition parameters
            self.transition_params = munch.Munch()
            self.transition_params.start_probs = {
                tuple(k): v for k, v in tmp.transition_params.start_probs
            }
            self.transition_params.transition_probs = {
                (tuple(k[0]), tuple(k[1])): v
                for k, v in tmp.transition_params.transition_probs
            }

            # emission parameters
            self.emission_params = munch.Munch()
            self.emission_params.false_emission = {
                k: v for k, v in tmp.emission_params.false_emission
            }
            self.emission_params.true_positive = {
                tuple(k): v for k, v in tmp.emission_params.true_positive
            }

            # hmm parameters
            self.hmm = conin.hmm.HiddenMarkovModel()
            self.hmm.load_model(
                start_probs={tuple(k): v for k, v in tmp.hmm.start_probs},
                transition_probs={
                    (tuple(k[0]), tuple(k[1])): v for k, v in tmp.hmm.transition_probs
                },
                emission_probs={
                    (tuple(k[0]), tuple(k[1])): v for k, v in tmp.hmm.emission_probs
                },
            )

    def oracle_constraints(self, schedule_all_activities):
        return GSF_oracle_constraints(
            self.data_wrapper,
            self.transition_params.hidden_states,
            schedule_all_activities,
        )


def GSF_oracle_constraints(data_wrapper, hidden_states, schedule_all_activities):
    """
    Returns a list of constraints that define a GSF HMM model

    TODO - Add logic for constraints associated with 'delay_after_hours' > 0
    """

    #
    # Define functions used to create oracle constraints
    #

    def always_appears_before_set(seq, val1, val2):
        """
        Note that here we can't use the common constraint because the hidden
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

    def must_appear_before(seq, val1, val2, offset):
        """
        val1 must appear before val2, offset time steps in advance
        """
        last_val1_index = None
        for index1, x1 in enumerate(seq):
            if val1 in x1:
                last_val1_index = index1
            if val2 in x1:
                if last_val1_index is None:
                    return False
                return index1 - last_val1_index > offset
        return True

    def cont(seq):
        """
        This requires that a process occurs without breaks.
        This is certainly not true all the time, but is the model choice we are making right now.
        """
        finished = set()
        for index, X in enumerate(seq):
            if index < len(seq) - 1:
                finishing = set(X) - set(seq[index + 1])
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
            length = sum(val in X for X in seq)
            if length != 0:
                return length >= lb
        return True

    def length_ub(seq, val, ub):
        """
        Determines that val doesn't appear too much
        """
        length = sum(val in X for X in seq)
        return length <= ub

    def at_least_one(seq):
        """
        Determines that we run at least one process
        """
        for X in seq:
            if X != ():
                return True
        return False

    def all_processes(seq, process_names):
        """
        Requires that all processes are run
        """
        processes = {p for X in seq for p in X}
        return processes == set(process_names)

    #
    # Return a list of oracle constraints
    #

    constraints = []

    # constraints.append(
    #    conin.OracleConstraint(func=lambda seq: cont(seq), same_partial_as_func=True)
    # )

    for i, name in enumerate(data_wrapper.process_names):

        constraints.append(
            conin.OracleConstraint(
                func=lambda seq, name=name, i=i, lb=data_wrapper.lower_times[
                    i
                ]: length_lb_cont(seq, name, lb),
                same_partial_as_func=True,
            )
        )

        constraints.append(
            conin.OracleConstraint(
                func=lambda seq, name=name, i=i, ub=data_wrapper.upper_times[
                    i
                ]: length_ub(seq, name, ub),
                same_partial_as_func=True,
            )
        )

    for i, name in enumerate(data_wrapper.process_names):
        for j, parent_name in enumerate(data_wrapper.process_parents[i]):
            constraints.append(
                conin.OracleConstraint(
                    func=lambda seq, parent_name=parent_name, name=name, delay=data_wrapper.delay_times[
                        i - 1
                    ]: must_appear_before(
                        seq, parent_name, name, delay
                    ),
                    same_partial_as_func=True,
                )
            )

    if schedule_all_activities:
        constraints.append(
            conin.OracleConstraint(
                func=lambda seq, hidden_states=hidden_states, process_names=data_wrapper.process_names: all_processes(
                    seq, process_names
                )
            )
        )

    return constraints
