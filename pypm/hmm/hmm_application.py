import json
import munch
import conin.hmm

from pypm.hmm.create_hmm import estimate_hidden_state_parameters, create_hmm
from pypm.hmm.estimate_emissions import initial_emission_parameters
from pypm.util.run_simian import create_data_wrapper, run_simian


def initialize_hmm_application(name):
    return PypmHMMApplication(config)


class PypmHMMApplication:

    def initialize(self, config):
        self._config = config
        self.data_wrapper = create_data_wrapper(config=config)
        self.data_wrapper.features = config.features
        self.hidden_state_params = None
        self.emission_params = None
        self.simulations = None
        self.data = munch.Munch()

    def learn_hidden_state_parameters(
        self,
        *,
        num_simulations,
        num_time_steps,
        seed,
        max_delay_before=0,
        quiet=False,
        debug=False
    ):
        self.simulations = run_simian(
            data_wrapper=self.data_wrapper,
            num_simulations=num_simulations,
            num_time_steps=num_time_steps,
            seed=seed,
            max_delay_before=max_delay_before,
            quiet=quiet,
        )
        self.hidden_state_params = estimate_hidden_state_parameters(
            simulations=self.simulations
        )
        self.data.options_learn_hidden_state_parameters = dict(
            num_simulations=num_simulations,
            num_time_steps=num_time_steps,
            max_delay_before=max_delay_before,
        )

    def learn_emission_parameters(self, **kwds):
        # self.data.options_learn_emission_parameters = kwds
        pass

    def create_hmm(self, observed_states, no_zeros=False, no_zeros_tol=1e-6):
        assert (
            self.hidden_state_params is not None
        ), "ERROR: must learn hidden state parameters before creating the HMM"
        if self.emission_params is None:
            self.emission_params = initial_emission_parameters(
                data_wrapper=self.data_wrapper
            )

        self.hmm = create_hmm(
            hidden_state_params=self.hidden_state_params,
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
            hidden_state_params=dict(
                hidden_states=self.hidden_state_params.hidden_states,
                start_probs=list(sorted(self.hidden_state_params.start_probs.items())),
                transition_probs=list(
                    sorted(self.hidden_state_params.transition_probs.items())
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

            # hidden state parameters
            self.hidden_state_params = munch.Munch()
            self.hidden_state_params.start_probs = {
                tuple(k): v for k, v in tmp.hidden_state_params.start_probs
            }
            self.hidden_state_params.transition_probs = {
                (tuple(k[0]), tuple(k[1])): v
                for k, v in tmp.hidden_state_params.transition_probs
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
