from conin.hmm import ConstrainedHiddenMarkovModel
import pyomo.environ as pe
from .matching_models import BaseModel, Z_Repn_Model, GSF_UnrestrictedMatches_VariableLengthActivities_constraints, fracval

# ====================================================================================
# HMM models
#
# GSF_HMM - unrestricted or compact matches, variable length activities
# XSF_HMM - unrestricted or compact matches, fixed length activities
# ====================================================================================


class GSF_HMM(Z_Repn_Model):
    def __init__(self, *, gaps_allowed=False, compact=False):
        self.gaps_allowed = gaps_allowed
        self.compact = compact
        if gaps_allowed:
            self.name = "HMM_UnrestrictedMatches_VariableLengthActivities_GapsAllowed"
            self.description = (
                "Supervised process matching maximizing log-likelihood, allowing gaps"
            )
        else:
            if compact:
                self.name = "HMM_CompactMatches_VariableLengthActivities"
                self.description = "Supervised process matching maximizing log-likelihood with compactness constraint"
            else:
                self.name = "HMM_UnrestrictedMatches_VariableLengthActivities"
                self.description = "Supervised process matching maximizing log-likelihood"

    def summarize(self):
        results = BaseModel.summarize(self)
        #
        if hasattr(self.M, "activity_length"):
            obs = {}
            for k in self.config.obs.observations:
                obs[k] = set()
            for j in self.config.pm:
                for k in self.config.pm[j]["resources"]:
                    for t in range(self.data.Tmax):
                        if self.M.a[j, t].value > 1 - 1e-7:
                            obs[k].add(t)

            feature_total = {}
            feature_len = {}
            separation = {}
            for k in self.config.obs.observations:
                feature_total = sum(
                    self.config.obs.observations[k][t]
                    for t in range(self.data.Tmax)
                    if t not in obs[k]
                )
                feature_len = self.data.Tmax - len(obs[k])
                activity_total = sum(self.config.obs.observations[k][t] for t in obs[k])
                activity_len = len(obs[k])
                # print(k, activity_total, activity_len, feature_total, feature_len)
                separation[k] = max(
                    0,
                    fracval(activity_total, activity_len)
                    - fracval(feature_total, feature_len),
                )
            results["goals"]["separation"] = separation

            results["goals"]["total_separation"] = sum(
                val for val in results["goals"]["separation"].values()
            )
        #
        #results["goals"]["match"] = {}
        #for activity, value in results["variables"]["o"].items():
        #    results["goals"]["match"][activity] = value
        #results["goals"]["total_match"] = sum(
        #    val for val in results["goals"]["match"].values()
        #)
        #
        return results

    def __call__(self, config, constraints=[]):
        self.config = config
        d = self.data = self.create_data(config, constraints)
        self.constraints = constraints

        Gamma = d.Gamma if self.gaps_allowed else {j: 0 for j in d.J}
        if self.compact:
            if Gamma != 0:
                print(
                    "Warning: Gamma is set to zero in CompactMatches_VariableLengthActivities"
                )
            Gamma = {j: 0 for j in d.J}

        self.M = self.create_model(
            objective=config.objective,
            J=d.J,
            T=d.T,
            S=d.S,
            K=d.K,
            O=d.O,
            P=d.P,
            Q=d.Q,
            E=d.E,
            Gamma=Gamma,
            Tmax=d.Tmax,
            Upsilon=d.Upsilon,
            tprev=d.tprev,
            verbose=config.verbose,
            debug=config.debug,
        )

        self.enforce_constraints(self.M, constraints, verbose=config.verbose)

    def create_model(
        self,
        *,
        objective,
        T,
        J,
        K,
        S,
        O,
        P,
        Q,
        E,
        Gamma,
        Tmax,
        Upsilon,
        tprev,
        verbose,
        debug
    ):
        if verbose:
            print("")
            print("Model Options")
            if type(self.config.options.get("Gamma", None)) is dict:
                print("  Gamma", Gamma)
            else:
                print("  Gamma", self.config.options.get("Gamma", None))
            print("  Upsilon", Upsilon)

        assert (
            objective == "log_likelihood"
        ), "GSF_HMM can not optimize the goal {}".format(objective)

        assert hasattr(self.config.hmm_app, "hmm"), f"You need to create an HMM before generating a schedule with GSF_HMM."
        chmm = ConstrainedHiddenMarkovModel(hmm=self.config.hmm_app.hmm)
        chmm.initialize_chmm("pyomo")
        M = chmm.chmm.generate_unconstrained_model(observed=self.config.hmm_app.data_wrapper.observation)

        tmp = M.hmm.o
        M.hmm.del_component("o")
        M.objective = tmp

        M.a = pe.Var(J, T, within=pe.Binary)

        # M.a[j,t] may be one if the active state at time t constains activity j
        M.a_con = pe.ConstraintList()
        for t,internal_state in M.hmm.x:
            state = self.config.hmm_app.hmm.hidden_to_external[internal_state]
            for j in J:
                if j in state:
                    M.a_con.add( M.a[j,t] <= M.hmm.x[t,internal_state] )

        M = GSF_UnrestrictedMatches_VariableLengthActivities_constraints(
            M=M,
            objective=objective,
            J=J,
            T=T,
            S=S,
            K=K,
            O=O,
            P=P,
            Q=Q,
            E=E,
            Gamma=Gamma,
            Tmax=Tmax,
            Upsilon=Upsilon,
            tprev=tprev,
            verbose=verbose,
            debug=debug,
        )
        if self.compact:
            M = GSF_CompactMatches_constraints(
                M=M,
                objective=objective,
                J=J,
                T=T,
                S=S,
                K=K,
                O=O,
                P=P,
                Q=Q,
                E=E,
                Tmax=Tmax,
                Upsilon=Upsilon,
                tprev=tprev,
                verbose=verbose,
                debug=debug,
            )

        return M


class XSF_HMM(Z_Repn_Model):
    def __init__(self, compact=False):
        self.compact = compact
        if compact:
            self.name = "HMM_CompactMatches_FixedLengthActivities"
            self.description = "Supervised process matching maximizing log-likelihood with compactness constraints"
        else:
            self.name = "HMM_UnrestrictedMatches_FixedLengthActivities"
            self.description = "Supervised process matching maximizing log-likelihood"

    def summarize(self):
        results = BaseModel.summarize(self)
        #
        obs = {}
        for k in self.config.obs.observations:
            obs[k] = set()
        for j in self.config.pm:
            for k in self.config.pm[j]["resources"]:
                for t in range(self.data.Tmax):
                    if (
                        self.M.z[j, t].value > 1 - 1e-7
                        and self.M.z[j, t - 1].value < 1e-7
                        and t + self.data.P[j] - 1 < self.data.Tmax
                    ):
                        for i in range(self.data.P[j]):
                            obs[k].add(t + i)

        feature_total = {}
        feature_len = {}
        separation = {}
        for k in self.config.obs.observations:
            feature_total = sum(
                self.config.obs.observations[k][t]
                for t in range(self.data.Tmax)
                if t not in obs[k]
            )
            feature_len = self.data.Tmax - len(obs[k])
            activity_total = sum(self.config.obs.observations[k][t] for t in obs[k])
            activity_len = len(obs[k])
            # print(k, activity_total, activity_len, feature_total, feature_len)
            separation[k] = max(
                0,
                fracval(activity_total, activity_len)
                - fracval(feature_total, feature_len),
            )
        results["goals"]["separation"] = separation

        results["goals"]["total_separation"] = sum(
            val for val in results["goals"]["separation"].values()
        )
        #
        results["goals"]["match"] = {}
        for activity, value in results["variables"]["o"].items():
            results["goals"]["match"][activity] = value
        results["goals"]["total_match"] = sum(
            val for val in results["goals"]["match"].values()
        )
        #
        return results

    def summarize_alignment(self, v):
        ans = {j: {"post": True} for j in self.config.pm}
        z = v["z"]
        for key, val in z.items():
            j, t = key
            if val < 1 - 1e-7:
                continue
            if j in ans and "post" not in ans[j]:
                continue
            if t == -1:
                ans[j] = {"pre": True}
                continue
            if t + self.data.P[j] - 1 < self.data.Tmax:
                ans[j] = {"first": t, "last": t + self.data.P[j] - 1}
        return ans

    def __call__(self, config, constraints=[]):
        self.config = config
        d = self.data = self.create_data(config, constraints)
        self.constraints = constraints

        self.M = self.create_model(
            objective=config.objective,
            J=d.J,
            T=d.T,
            S=d.S,
            K=d.K,
            O=d.O,
            P=d.P,
            Q=d.Q,
            E=d.E,
            Tmax=d.Tmax,
            Upsilon=d.Upsilon,
            tprev=d.tprev,
            verbose=config.verbose,
            debug=config.debug,
        )

        self.enforce_constraints(self.M, constraints, verbose=config.verbose)

    def create_model(
        self, *, objective, T, J, K, S, O, P, Q, E, Tmax, Upsilon, tprev, verbose, debug
    ):
        if verbose:
            print("")
            print("Model Options")
            print("  Upsilon", Upsilon)

        assert (
            objective == "total_match_score"
        ), "XSF can not optimize the goal {}".format(objective)

        M = pe.ConcreteModel()
        M.z = pe.Var(J, [-1] + T, within=pe.Binary)
        M.o = pe.Var(J, bounds=(0, None))

        # Objective

        def objective_(m):
            return sum(m.o[j] for j in J)

        M.objective = pe.Objective(sense=pe.maximize, rule=objective_)

        def odef_(m, j):
            total = 0
            for t in T:
                end = t + P[j] - 1
                if end not in T:
                    continue
                match_score = sum(
                    S[j, k] * sum(O[k][t + i] for i in range(P[j])) for k in K[j]
                )
                total += match_score * (m.z[j, t] - m.z[j, t - 1])
            return m.o[j] == total

        M.odef = pe.Constraint(J, rule=odef_)

        M = XSF_UnrestrictedMatches_FixedLengthActivities_constraints(
            M=M,
            objective=objective,
            J=J,
            T=T,
            S=S,
            K=K,
            O=O,
            P=P,
            Q=Q,
            E=E,
            Tmax=Tmax,
            Upsilon=Upsilon,
            tprev=tprev,
            verbose=verbose,
        )
        if self.compact:
            M = XSF_CompactMatches_constraints(
                M=M,
                objective=objective,
                J=J,
                T=T,
                S=S,
                K=K,
                O=O,
                P=P,
                Q=Q,
                E=E,
                Tmax=Tmax,
                Upsilon=Upsilon,
                tprev=tprev,
                verbose=verbose,
                debug=debug,
            )

        return M

