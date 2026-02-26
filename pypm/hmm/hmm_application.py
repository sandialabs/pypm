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

    def learn_transition_parameters(
        self,
        *,
        num_simulations,
        seed,
        num_time_steps=None,
        max_delay_before=0,
        quiet=False,
        debug=False,
    ):
        if num_time_steps is None:
            num_time_steps = self.data_wrapper.num_time_steps

        self.simulations = run_simian(
            data_wrapper=self.data_wrapper,
            num_simulations=num_simulations,
            num_time_steps=num_time_steps,
            seed=seed,
            max_delay_before=max_delay_before,
            quiet=quiet,
        )
        self.transition_params = estimate_transition_parameters(
            simulations=self.simulations
        )
        self.data.options_learn_transition_parameters = dict(
            num_simulations=num_simulations,
            num_time_steps=num_time_steps,
            max_delay_before=max_delay_before,
            debug=debug,
        )

    def learn_emission_parameters(
        self,
        *,
        observed,
        constrained=True,
        max_iterations=None,
        num_solutions_per_step=None,
        debug=False,
    ):
        constraints = [] if not constrained else self.oracle_constraints()

        self.emission_params = estimate_emission_parameters(
            observed=observed,
            data_wrapper=self.data_wrapper,
            emission_params=self.emission_params,
            transition_params=self.transition_params,
            constraints=constraints,
            max_iterations=max_iterations,
            num_solutions_per_step=num_solutions_per_step,
            debug=debug,
        )

    def create_hmm(self, observed_states=None, no_zeros=False, no_zeros_tol=1e-6):
        assert (
            self.transition_params is not None
        ), "ERROR: must learn transition parameters before creating the HMM"
        if observed_states is None:
            assert hasattr(
                self.data_wrapper, "observed_states"
            ), "If observed_states is not specified, then data observations must be included in the config object"
            observed_states = self.data_wrapper.observed_states

        if self.emission_params is None:
            self.emission_params = initial_emission_parameters(
                data_wrapper=self.data_wrapper
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

    def oracle_constraints(self):
        return GSF_oracle_constraints(
            self.data_wrapper, self.transition_params.hidden_states
        )


def GSF_oracle_constraints(data_wrapper, hidden_states):
    """
    Returns a list of constraints that define a GSF HMM model
    """

    #
    # Define functions used to create oracle constraints
    #

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
            if X != ():
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

    #
    # Return a list of oracle constraints
    #

    constraints = []

    constraints.append(
        conin.OracleConstraint(func=lambda seq: cont(seq), same_partial_as_func=True)
    )

    for i, name in enumerate(data_wrapper.process_names):

        constraints.append(
            conin.OracleConstraint(
                func=lambda seq, name=name, i=i: length_lb_cont(
                    seq, name, data_wrapper.lower_times[i]
                ),
                same_partial_as_func=True,
            )
        )

        constraints.append(
            conin.OracleConstraint(
                func=lambda seq, name=name, i=i: length_ub(
                    seq, name, data_wrapper.upper_times[i]
                ),
                same_partial_as_func=True,
            )
        )

    for i, name in enumerate(data_wrapper.process_names):
        for j, parent_name in enumerate(data_wrapper.process_parents[i]):
            constraints.append(
                conin.OracleConstraint(
                    func=lambda seq, parent_name=parent_name, name=name: always_appears_before_set(
                        seq, parent_name, name
                    ),
                    same_partial_as_func=True,
                )
            )

    # constraints.append(conin.OracleConstraint(func=lambda seq: at_least_one(seq))

    constraints.append(
        conin.OracleConstraint(
            func=lambda seq, hidden_states=hidden_states: all_processes(
                seq, data_wrapper.process_names
            )
        )
    )

    return constraints
