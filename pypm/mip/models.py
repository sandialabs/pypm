import datetime
import pprint
import pyomo.environ as pe


#
# Collect all of the nonzero variables in a Pyomo model
#
def get_nonzero_variables(M):
    ans = {}
    for v in M.component_objects(pe.Var, active=True):
        ans[v.name] = {}
        for index in v:
            if pe.value(v[index]) > 1e-7:
                ans[v.name][index] = pe.value(v[index])
    return ans


#
# Compute the fraction, returning 0 if the denominator is zero
#
def fracval(num, denom):
    if denom != 0:
        return num / denom
    return 0


class ProcessModelData(object):
    def __init__(self, data, constraints=None):
        pm = data.pm
        Kall = list(sorted(name for name in pm.resources))

        self.Tmax = data.obs.timesteps
        self.T = list(range(self.Tmax))

        self.O = data.obs.observations
        self.E = [(pm[dep]["name"], i) for i in pm for dep in pm[i]["dependencies"]]
        self.P = {j: pm[j]["duration"]["min_timesteps"] for j in pm}
        self.Q = {j: pm[j]["duration"]["max_timesteps"] for j in pm}
        hours_per_timestep = pm.hours_per_timestep

        self.J = list(sorted(pm))
        self.K = {j: set(pm[j]["resources"].keys()) for j in pm}
        self.JK = [(j, k) for j in self.J for k in self.K[j]]

        if "Gamma" in data.options and type(data.options["Gamma"]) is dict:
            self.Gamma = data.options["Gamma"]
        else:
            self.Gamma = {j: data.options.get("Gamma", None) for j in self.J}
        self.Upsilon = data.options.get("Upsilon", None)

        self.S = {(j, k): 1 if k in self.K[j] else 0 for j in pm for k in Kall}
        self.C = {(j, k): pm[j]["resources"][k] for j in pm for k in pm[j]["resources"]}

        if constraints:
            for con in constraints:
                if con is None:
                    continue
                if con.constraint == "activity_duration":
                    j = con.activity
                    self.P[j] = con.minval
                    self.Q[j] = con.maxval

        #
        # Omega[j] is the delay_after value for activity j, in 'timesteps' units
        #
        self.Omega = {
            j: 0
            if pm[j]["delay_after_timesteps"] is None
            else pm[j]["delay_after_timesteps"]
            for j in pm
        }
        #
        # tprev[j,t] is the latest time that activity can start and complete before time step t
        #
        tprev = {}
        #
        # Loop over activities j
        #
        for j in pm:
            #
            # Loop over t = 0 ... Tmax
            #
            for t in list(self.T) + [self.Tmax]:
                #
                # For (j,t), we loop for tau = t-1 ... -1
                #
                for tau in reversed(range(-1, t - 1)):
                    #
                    # If we start at tau, then
                    #       tau + P[j] - 1 is the last time step that the activity is executed
                    #       tau + P[j] - 1 + Omega[j] is the last time step after the delay
                    # We continue to decrement tau if this value is not less than tau
                    #
                    if tau + self.P[j] - 1 + self.Omega[j] >= t:
                        continue
                    tprev[j, t] = tau
                    break
        self.tprev = tprev


class BaseModel(object):
    def summarize(self):
        variables = variables = get_nonzero_variables(self.M)
        alignment = self.summarize_alignment(variables)
        results = dict(
            objective=pe.value(self.M.objective),
            variables=variables,
            schedule=alignment,
            goals=dict(),
        )

        if not self.config.obs.datetime is None:
            obs = self.config.obs
            datetime_alignment = {key: {} for key in alignment}
            lastv = max(v for v in obs.datetime)
            for key, value in alignment.items():
                for k, v in value.items():
                    if k == "pre":
                        datetime_alignment[key][k] = obs.datetime[0]
                    elif k == "post":
                        datetime_alignment[key][k] = obs.datetime[lastv]
                    else:
                        # if v > lastv:
                        #    print("HERE",key,k,v,lastv)
                        # else:
                        #    datetime_alignment[key][k] = obs.datetime[v]
                        datetime_alignment[key][k] = obs.datetime[v]
                if "last" in datetime_alignment[key] and v + 1 in obs.datetime:
                    datetime_alignment[key]["stop"] = obs.datetime[v + 1]
                # elif 'first' in datetime_alignment[key] and 'last' not in datetime_alignment[key]:
                #    print("HERE",key,value,datetime_alignment[key])
                #    raise IOError("Bad date?")
            results["datetime_schedule"] = datetime_alignment

        return results

    def check_labels(self):
        """
        For supervised models, we confirm that the observations have the right labels
        """
        tmp1 = set(self.config.obs.observations.keys())
        tmp2 = set([name for name in self.config.pm.resources])
        assert tmp1.issubset(tmp2), (
            "For supervised process matching, we expect the observations to have labels in the process model.  The following are unknown resource labels: "
            + str(tmp1 - tmp2)
        )


class Z_Repn_Model(BaseModel):
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
            ans[j] = {"first": t, "last": -1}
        a = v["a"]
        for key, val in a.items():
            j, t = key
            if "pre" in ans[j] or "post" in ans[j]:
                continue
            if t > ans[j]["last"]:
                ans[j]["last"] = t
        return ans

    def enforce_constraints(self, M, constraints, verbose=False):
        if self.config.obs.datetime is None:
            invdatetime = {}
        else:
            invdatetime = {
                datetime.datetime.fromisoformat(v): k
                for k, v in self.config.obs.datetime.items()
            }
        #
        # Set constraints by fixing variables in the model
        #
        for con in constraints:
            if con is None:
                continue

            j = con.activity
            if con.constraint == "include":
                M.z[j, -1].fix(0)
                # TODO - Make this stronger by fixing the latest feasible start-time for which the
                #        the activity ends before the end of the time horizon
                M.z[j, self.data.Tmax - 1].fix(1)

            elif con.constraint == "earliest_start":
                if len(invdatetime) == 0:
                    print(
                        "WARNING: attemping to apply fix_start constraint with data that does not specify datetime values."
                    )
                    continue
                start = con.startdate
                if isinstance(start, str):
                    start = datetime.datetime.fromisoformat(start)

                for dd, tt in invdatetime.items():
                    diff = dd - start
                    if diff.total_seconds() < 0:
                        M.z[j, tt].fix(0)

            elif con.constraint == "latest_start":
                if len(invdatetime) == 0:
                    print(
                        "WARNING: attemping to apply fix_start constraint with data that does not specify datetime values."
                    )
                    continue
                start = con.startdate
                if isinstance(start, str):
                    start = datetime.datetime.fromisoformat(start)

                for dd, tt in invdatetime.items():
                    diff = dd - start
                    if diff.total_seconds() >= 0:
                        M.z[j, tt].fix(1)

            elif con.constraint == "fix_start":
                if len(invdatetime) == 0:
                    print(
                        "WARNING: attemping to apply fix_start constraint with data that does not specify datetime values."
                    )
                    continue
                start = con.startdate
                if isinstance(start, str):
                    start = datetime.datetime.fromisoformat(start)
                t = invdatetime.get(start, None)

                if t is not None:
                    M.z[j, t].fix(1)
                    M.z[j, t - 1].fix(0)
                else:
                    print(
                        "WARNING: the fix_start constraint for activity {} specifies the date {} that is not in the time window.".format(
                            j, con.startdate
                        )
                    )
                    mindiff = float("inf")
                    nextd = None
                    for dd, tt in invdatetime.items():
                        diff = dd - start
                        if diff.total_seconds() > 0:
                            if nextd is None or diff.total_seconds() < mindiff:
                                mindiff = diff.total_seconds()
                                nextd = dd
                    if nextd is None:
                        print(
                            "\tThe startdate is after the process matching time window."
                        )
                    else:
                        print("\tThe next valid startdate is {}".format(nextd))

            elif con.constraint == "relax":
                M.z[j, -1].unfix()
                M.z[j, self.data.Tmax - 1].unfix()
                for t in self.data.T:
                    M.z[j, t].unfix()

            elif con.constraint == "relax_start":
                for t in self.data.T:
                    M.z[j, t].unfix()

        if verbose:
            print("Summary of fixed variables")
            flag = False
            if "a" in M:
                for j, t in M.a:
                    if M.a[j, t].fixed:
                        print(" ", M.a[j, t], M.a[j, t].value)
                        flag = True
            for j, t in M.z:
                if M.z[j, t].fixed:
                    print(" ", M.z[j, t], M.z[j, t].value)
                    flag = True
            if not flag:
                print(" None")


#
# This is the GSF model in Figure 3.2
#
class GSF_TotalMatchScore(Z_Repn_Model):
    def __init__(self, *, gaps_allowed):
        self.gaps_allowed = gaps_allowed
        if gaps_allowed:
            self.name = "UnrestrictedMatches_VariableLengthActivities_GapsAllowed"
        else:
            self.name = "UnrestrictedMatches_VariableLengthActivities"
        self.description = "Supervised process matching maximizing match score"

    def __call__(self, config, constraints=[]):
        self.config = config
        d = self.data = ProcessModelData(config, constraints)
        self.constraints = constraints

        Gamma = d.Gamma if self.gaps_allowed else {j: 0 for j in d.J}
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
            objective == "total_match_score"
        ), "Model11 can not optimize the goal {}".format(objective)

        M = pe.ConcreteModel()

        M.z = pe.Var(J, [-1] + T, within=pe.Binary)
        M.a = pe.Var(J, T, within=pe.Binary)
        M.o = pe.Var(J, bounds=(0, None))

        # Objective

        def objective_(m):
            return sum(m.o[j] for j in J)

        M.objective = pe.Objective(sense=pe.maximize, rule=objective_)

        def odef_(m, j):
            return m.o[j] == sum(
                sum((S[j, k] * O[k][t]) * m.a[j, t] for k in K[j]) for t in T
            )

        M.odef = pe.Constraint(J, rule=odef_)

        # Simultenaity constraints

        if not Upsilon is None:

            def activity_limit_(m, t):
                return sum(m.a[j, t] for j in J) <= Upsilon

            M.activity_limit = pe.Constraint(T, rule=activity_limit_)

        # Z constraints

        def zstep_(m, j, t):
            return m.z[j, t] - m.z[j, t - 1] >= 0

        M.zstep = pe.Constraint(J, T, rule=zstep_)

        def precedence_lb_(m, i, j, t):
            tau = tprev.get((i, t), -1)
            return m.z[i, tau] - m.z[j, t] >= 0

        M.precedence_lb = pe.Constraint(E, T, rule=precedence_lb_)

        def activity_stop_(m, i, j, t):
            return 1 - m.z[j, t] >= m.a[i, t]

        M.activity_stop = pe.Constraint(E, T, rule=activity_stop_)

        def firsta_(m, j, t):
            return m.z[j, t] - m.z[j, t - 1] <= m.a[j, t]

        M.firsta = pe.Constraint(J, T, rule=firsta_)

        def length_lower_(m, j):
            return sum(m.a[j, t] for t in T) >= P[j] * (m.z[j, Tmax - 1] - M.z[j, -1])

        M.length_lower = pe.Constraint(J, rule=length_lower_)

        def length_upper_(m, j):
            return sum(m.a[j, t] for t in T) <= Q[j] * (m.z[j, Tmax - 1] - M.z[j, -1])

        M.length_upper = pe.Constraint(J, rule=length_upper_)

        def activity_start_(m, j, t):
            if Gamma[j] is None:
                tau = -1
            else:
                tau = max(t - (Q[j] + Gamma[j]), -1)
            return m.z[j, t] - m.z[j, tau] >= m.a[j, t]

        M.activity_start = pe.Constraint(J, T, rule=activity_start_)

        # Auxilliary computed values

        def activity_length_(m, j):
            return sum(m.a[j, t] for t in T)

        M.activity_length = pe.Expression(J, rule=activity_length_)

        def weighted_activity_length_(m, j):
            return sum(O[k][t] * m.a[j, t] for k in K[j] for t in T)

        M.weighted_activity_length = pe.Expression(J, rule=weighted_activity_length_)

        def nonactivity_length_(m, j):
            return sum((1 - m.a[j, t]) for t in T)

        M.nonactivity_length = pe.Expression(J, rule=nonactivity_length_)

        def weighted_nonactivity_length_(m, j):
            return sum(O[k][t] * (1 - m.a[j, t]) for k in K[j] for t in T)

        M.weighted_nonactivity_length = pe.Expression(
            J, rule=weighted_nonactivity_length_
        )

        return M


#
# This is the GSF-ED model in Figure 4.1
#
class GSFED_TotalMatchScore(Z_Repn_Model):
    def __init__(self):
        self.name = "GSF-ED"
        self.description = "Supervised process matching maximizing match score, including both continuous and count data"

    def __call__(self, config, constraints=[]):
        self.config = config
        d = self.data = ProcessModelData(config)
        self.constraints = constraints

        self.M = self.create_model(
            objective=config.objective,
            J=d.J,
            T=d.T,
            S=d.S,
            K=d.K,
            JK=d.JK,
            O=d.O,
            P=d.P,
            Q=d.Q,
            E=d.E,
            Gamma=d.Gamma,
            Tmax=d.Tmax,
            Upsilon=d.Upsilon,
            C=d.C,
            count_data=config.count_data,
            tprev=d.tprev,
            verbose=config.verbose,
        )

        self.enforce_constraints(self.M, constraints, verbose=config.verbose)

    def create_model(
        self,
        *,
        objective,
        T,
        J,
        K,
        JK,
        S,
        O,
        P,
        Q,
        E,
        Gamma,
        Tmax,
        Upsilon,
        count_data,
        C,
        tprev,
        verbose
    ):
        assert (
            objective == "total_match_score"
        ), "Model11 can not optimize the goal {}".format(objective)

        M = pe.ConcreteModel()

        M.z = pe.Var(J, [-1] + T, within=pe.Binary)
        M.a = pe.Var(J, T, within=pe.Binary)
        M.o = pe.Var(J, bounds=(0, None))
        if len(count_data) > 0:
            M.r = pe.Var([(j, k) for (j, k) in JK if k in count_data], T, bounds=(0, 1))

        # Objective

        def objective_(m):
            return sum(m.o[j] for j in J)

        M.objective = pe.Objective(sense=pe.maximize, rule=objective_)

        def odef_(m, j):
            if len(count_data) == 0:
                return m.o[j] == sum(
                    sum((S[j, k] * O[k][t]) * m.a[j, t] for k in K[j]) for t in T
                )
            else:
                e1 = sum(
                    sum(
                        (S[j, k] * O[k][t]) * m.a[j, t]
                        for k in K[j].difference(count_data)
                    )
                    for t in T
                )
                e2 = sum(
                    sum(S[j, k] * m.r[j, k, t] for k in K[j].intersection(count_data))
                    for t in T
                )
                return m.o[j] == e1 + e2

        M.odef = pe.Constraint(J, rule=odef_)

        # Limit the max value of r_jkt

        def maxr_a_(m, j, k, t):
            if k in count_data:
                return m.r[j, k, t] <= m.a[j, t]
            return pe.Constraint.Skip

        M.maxr_a = pe.Constraint(JK, T, rule=maxr_a_)

        def maxr_O_(m, k, t):
            return (
                sum(
                    C[j, k] * M.r[j, k, t]
                    for j in J
                    if (j, k) in JK and k in count_data
                )
                <= O[k][t]
            )

        M.maxr_O = pe.Constraint(count_data, T, rule=maxr_O_)

        # Simultenaity constraints

        if not Upsilon is None:

            def activity_limit_(m, t):
                return sum(m.a[j, t] for j in J) <= Upsilon

            M.activity_limit = pe.Constraint(T, rule=activity_limit_)

        # Z constraints

        def zstep_(m, j, t):
            return m.z[j, t] - m.z[j, t - 1] >= 0

        M.zstep = pe.Constraint(J, T, rule=zstep_)

        def firsta_(m, j, t):
            return m.z[j, t] - m.z[j, t - 1] <= m.a[j, t]

        M.firsta = pe.Constraint(J, T, rule=firsta_)

        def activity_start_(m, j, t):
            if Gamma[j] is None:
                tau = -1
            else:
                tau = max(t - (Q[j] + Gamma[j]), -1)
            return m.z[j, t] - m.z[j, tau] >= m.a[j, t]

        M.activity_start = pe.Constraint(J, T, rule=activity_start_)

        def length_lower_(m, j):
            return sum(m.a[j, t] for t in T) >= P[j] * (m.z[j, Tmax - 1] - M.z[j, -1])

        M.length_lower = pe.Constraint(J, rule=length_lower_)

        def length_upper_(m, j):
            return sum(m.a[j, t] for t in T) <= Q[j] * (m.z[j, Tmax - 1] - M.z[j, -1])

        M.length_upper = pe.Constraint(J, rule=length_upper_)

        def precedence_lb_(m, i, j, t):
            tau = tprev.get((i, t), -1)
            return m.z[i, tau] - m.z[j, t] >= 0

        M.precedence_lb = pe.Constraint(E, T, rule=precedence_lb_)

        def activity_stop_(m, i, j, t):
            return 1 - m.z[j, t] >= m.a[i, t]

        M.activity_stop = pe.Constraint(E, T, rule=activity_stop_)

        # Auxilliary computed values

        def activity_length_(m, j):
            return sum(m.a[j, t] for t in T)

        M.activity_length = pe.Expression(J, rule=activity_length_)

        def weighted_activity_length_(m, j):
            return sum(O[k][t] * m.a[j, t] for k in K[j] for t in T)

        M.weighted_activity_length = pe.Expression(J, rule=weighted_activity_length_)

        def nonactivity_length_(m, j):
            return sum((1 - m.a[j, t]) for t in T)

        M.nonactivity_length = pe.Expression(J, rule=nonactivity_length_)

        def weighted_nonactivity_length_(m, j):
            return sum(O[k][t] * (1 - m.a[j, t]) for k in K[j] for t in T)

        M.weighted_nonactivity_length = pe.Expression(
            J, rule=weighted_nonactivity_length_
        )

        return M


class UPM_ProcessModelData(object):
    def __init__(self, data, constraints=None):
        ProcessModelData.__init__(self, data, constraints)

        self.K_count = set()
        for r in data.pm.resources:
            count = data.pm.resources.count(r)
            if count is not None and count > 1:
                self.K_count.add(count)

        self.Kall = set(name for name in data.pm.resources)
        self.U = set(self.O.keys())

        self.Delta = data.options.get("Delta", 0)
        self.Xi = data.options.get("Xi", 0)


#
# This is the UPM model in Figure 2-1
#
# WEH: This model is closely related to model12 and model14, but I haven't tried to confirm that it's exactly
#           equivalent.
#
class UPM_TotalMatchScore(Z_Repn_Model):
    def __init__(self):
        self.name = "UPM"
        self.description = "Unsupervised process matching maximizing match score, including both continuous and count data"

    def summarize(self):
        results = Z_Repn_Model.summarize(self)

        results["feature_label"] = {}
        for k, u in self.M.m:
            if pe.value(self.M.m[k, u]) > 1 - 1e-7:
                results["feature_label"][u] = k

        Delta = self.data.Delta
        if Delta == 0:
            rmap = {}
            for u in results["feature_label"]:
                k = results["feature_label"][u]
                if k not in rmap:
                    rmap[k] = set()
                rmap[k].add(u)

            obs = {}
            for col in results["feature_label"]:
                obs[col] = set()
            for j in self.config.pm:
                for k in self.config.pm[j]["resources"]:
                    for col in rmap.get(k, []):
                        for t in range(self.data.Tmax):
                            if self.M.a[j, t].value > 1 - 1e-7:
                                obs[col].add(t)

            feature_total = {}
            feature_len = {}
            separation = {}
            for k in obs:
                feature_total = sum(
                    self.config.obs.observations[k][t]
                    for t in range(self.data.Tmax)
                    if t not in obs[k]
                )
                feature_len = self.data.Tmax - len(obs[k])
                activity_total = sum(self.config.obs.observations[k][t] for t in obs[k])
                activity_len = len(obs[k])
                separation[k] = max(
                    0,
                    fracval(activity_total, activity_len)
                    - fracval(feature_total, feature_len),
                )

            # activity_length = {}
            # for j in self.M.o:
            #    activity_length[j] = sum(self.M.a[j,t].value for t in self.M.T)
            # nonactivity_length = {}
            # for j in self.M.o:
            #    nonactivity_length[j] = len(self.M.T) - activity_length[j]

            # separation = {}
            # for j in activity_length:
            #    separation[j] = 0
            #    for k in self.config.pm[j]['resources']:
            #        if len(rmap.get(k,[])) > 0:
            #            activity    = sum(max(self.config.obs.observations[col][t] * self.M.a[j,t].value     for col in rmap.get(k,[])) for t in self.M.T)
            #            nonactivity = sum(max(self.config.obs.observations[col][t] * (1-self.M.a[j,t].value) for col in rmap.get(k,[])) for t in self.M.T)
            #        else:
            #            activity = 0
            #            nonactivity = 0
            #        separation[j] += max(0, fracval(activity,activity_length[j]) - fracval(nonactivity,nonactivity_length[j]))

            results["goals"]["separation"] = separation
            results["goals"]["total_separation"] = sum(
                val for val in separation.values()
            )
        else:
            print("WARNING: Cannot compute separation with unknown resources (yet)")

        return results

    def __call__(self, config, constraints=[]):
        self.config = config
        d = self.data = UPM_ProcessModelData(config)
        self.constraints = constraints

        self.M = self.create_model(
            objective=config.objective,
            J=d.J,
            T=d.T,
            S=d.S,
            K=d.K,
            JK=d.JK,
            O=d.O,
            P=d.P,
            Q=d.Q,
            E=d.E,
            Gamma=d.Gamma,
            Tmax=d.Tmax,
            Upsilon=d.Upsilon,
            C=d.C,
            U=d.U,
            U_count=config.count_data,
            Kall=d.Kall,
            K_count=d.K_count,
            Delta=d.Delta,
            Xi=d.Xi,
            tprev=d.tprev,
            verbose=config.verbose,
        )

        self.enforce_constraints(self.M, constraints, verbose=config.verbose)

    def create_model(
        self,
        *,
        objective,
        T,
        J,
        K,
        JK,
        S,
        O,
        P,
        Q,
        E,
        Gamma,
        Tmax,
        Upsilon,
        C,
        Delta,
        Xi,
        U,
        U_count,
        Kall,
        K_count,
        tprev,
        verbose
    ):
        assert (
            objective == "total_match_score"
        ), "UPM can not optimize the goal {}".format(objective)

        if verbose:
            print("")
            print("Model Options")
            print("  Delta", Delta)
            print("  Gamma", Gamma)
            print("  Xi", Xi)
            print("  Upsilon", Upsilon)

        #
        # If Delta>0, then we add 2*Delta unknown resources to each activity.  The
        # model is more flexible than this, but it's unclear how many resources to add and to which activities.
        #
        # Note that we always add one continuous and one count resource
        #
        H = set()
        for i in range(2 * Delta):
            # Continuous resource
            k = len(Kall)
            H.add(k)
            Kall.add(k)
            for j in J:
                JK.add((j, k))
                K[j].add(k)
            # Count resource
            k = len(Kall)
            H.add(k)
            Kall.add(k)
            for j in J:
                JK.add((j, k))
                K[j].add(k)
            K_count.add(k)

        M = pe.ConcreteModel()
        M.T = T

        M.z = pe.Var(J, [-1] + T, within=pe.Binary)
        M.a = pe.Var(J, T, within=pe.Binary)
        M.o = pe.Var(J, bounds=(0, None))
        M.r = pe.Var(JK, T, bounds=(0, 1))
        M.m = pe.Var(Kall, U, bounds=(0, 1), within=pe.Binary)
        if Delta > 0:
            M.delta = pe.Var(J, H, within=pe.Binary)

        # Objective

        def objective_(m):
            return sum(m.o[j] for j in J)

        M.objective = pe.Objective(sense=pe.maximize, rule=objective_)

        def odef_(m, j):
            return m.o[j] == sum(sum(S[j, k] * m.r[j, k, t] for k in K[j]) for t in T)

        M.odef = pe.Constraint(J, rule=odef_)

        # Define m

        def mdef_label_(m, u):
            return sum(m.m[k, u] for k in Kall) <= 1

        M.mdef_label = pe.Constraint(U, rule=mdef_label_)

        for k in Kall.difference(K_count):
            for u in U_count:
                M.m[k, u].fix(0)
        for k in K_count:
            for u in U.difference(U_count):
                M.m[k, u].fix(0)

        def w_(m, k, t):
            return sum(m.m[k, u] * O[u][t] for u in U)

        M.w = pe.Expression(Kall, T, rule=w_)

        def mdef_mean_(m, k):
            return sum(m.m[k, u] for u in U) <= 1

        M.mdef_mean = pe.Constraint(Kall, rule=mdef_mean_)

        # Limit the max value of r_jkt

        def rmax_a_(m, j, k, t):
            return m.r[j, k, t] <= m.a[j, t]

        M.rmax_a = pe.Constraint(JK, T, rule=rmax_a_)

        M.rmax_w = pe.ConstraintList()
        for j, k in JK:
            if k in K_count:
                continue
            for t in T:
                M.rmax_w.add(M.r[j, k, t] <= M.w[k, t])

        if len(K_count) > 0:
            M.rmax_count = pe.ConstraintList()
            for k in K_count:
                for t in T:
                    M.rmax_count.add(
                        sum(C[j, k] * M.r[j, k, t] for j in J if (j, k) in JK)
                        <= M.w[k, t]
                    )

        if Delta > 0:

            def rmax_delta_(m, k, j, t):
                return m.r[j, k, t] <= m.delta[j, k]

            m.r_delta = pe.Constraint(H, J, T, rule=r_delta_)

            def Delta_(m, j):
                return sum(m.delta[j, k] for k in H) <= Delta

            m.Delta = pe.Constraint(J, rule=delta1_)

            def Xi_(m, j):
                return sum(m.delta[j, k] for j in J) <= Xi

            m.Xi = pe.Constraint(H, rule=Xi_)

        # Simultenaity constraints

        if not Upsilon is None:

            def activity_limit_(m, t):
                return sum(m.a[j, t] for j in J) <= Upsilon

            M.activity_limit = pe.Constraint(T, rule=activity_limit_)

        # Z constraints

        def zstep_(m, j, t):
            return m.z[j, t] - m.z[j, t - 1] >= 0

        M.zstep = pe.Constraint(J, T, rule=zstep_)

        def firsta_(m, j, t):
            return m.z[j, t] - m.z[j, t - 1] <= m.a[j, t]

        M.firsta = pe.Constraint(J, T, rule=firsta_)

        def activity_start_(m, j, t):
            if Gamma[j] is None:
                tau = -1
            else:
                tau = max(t - (Q[j] + Gamma[j]), -1)
            return m.z[j, t] - m.z[j, tau] >= m.a[j, t]

        M.activity_start = pe.Constraint(J, T, rule=activity_start_)

        def length_lower_(m, j):
            return sum(m.a[j, t] for t in T) >= P[j] * (m.z[j, Tmax - 1] - M.z[j, -1])

        M.length_lower = pe.Constraint(J, rule=length_lower_)

        def length_upper_(m, j):
            return sum(m.a[j, t] for t in T) <= Q[j] * (m.z[j, Tmax - 1] - M.z[j, -1])

        M.length_upper = pe.Constraint(J, rule=length_upper_)

        def precedence_lb_(m, i, j, t):
            tau = tprev.get((i, t), -1)
            return m.z[i, tau] - m.z[j, t] >= 0

        M.precedence_lb = pe.Constraint(E, T, rule=precedence_lb_)

        def activity_stop_(m, i, j, t):
            return 1 - m.z[j, t] >= m.a[i, t]

        M.activity_stop = pe.Constraint(E, T, rule=activity_stop_)

        # Auxilliary computed values

        # def activity_length_(m, j):
        #    return sum(m.a[j,t] for t in T)
        # M.activity_length = pe.Expression(J, rule=activity_length_)

        # def weighted_activity_length_(m, j):
        #    return sum(m.r[j,k,t] for k in K[j] for t in T)
        # M.weighted_activity_length = pe.Expression(J, rule=weighted_activity_length_)

        # def nonactivity_length_(m, j):
        #    return sum( 1-m.a[j,t] for t in T)
        # M.nonactivity_length = pe.Expression(J, rule=nonactivity_length_)

        # def weighted_nonactivity_length_(m, j):
        #    return sum( 1- m.r[j,k,t] for k in K[j] for t in T)
        # M.weighted_nonactivity_length = pe.Expression(J, rule=weighted_nonactivity_length_)

        return M


#
# A variant of GSF without a variables
#
class XSF_TotalMatchScore(Z_Repn_Model):
    def __init__(self):
        self.name = "UnrestrictedMatches_FixedLengthActivities"
        self.description = "Supervised process matching maximizing match score"

    def __call__(self, config, constraints=[]):
        self.config = config
        d = self.data = ProcessModelData(config, constraints)
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
        )

        self.enforce_constraints(self.M, constraints, verbose=config.verbose)

    def create_model(
        self, *, objective, T, J, K, S, O, P, Q, E, Tmax, Upsilon, tprev, verbose
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

        # Simultenaity constraints

        if not Upsilon is None:

            def activity_limit_(m, t):
                # return sum(m.a[j,t] for j in J) <= Upsilon
                return sum(m.z[j, t] - m.z[j, t - 1] for j in J) <= Upsilon

            M.activity_limit = pe.Constraint(T, rule=activity_limit_)

        # Z constraints

        def zstep_(m, j, t):
            return m.z[j, t] - m.z[j, t - 1] >= 0

        M.zstep = pe.Constraint(J, T, rule=zstep_)

        def precedence_lb_(m, i, j, t):
            tau = tprev.get((i, t), -1)
            return m.z[i, tau] - m.z[j, t] >= 0

        M.precedence_lb = pe.Constraint(E, T, rule=precedence_lb_)

        def activity_feasibility_(m, j, t):
            tau = tprev.get((j, Tmax), -1)
            if t > tau:
                # WEH - This is the old logic, which is weaker than the new logic b.c. it
                #       doesn't account for the additional information that is encoded in the
                #       tprev values.
                # if t + P[j] - 1 >= Tmax:
                return m.z[j, t] == m.z[j, Tmax - 1]
            return pe.Constraint.Skip

        M.activity_feasibility = pe.Constraint(J, T, rule=activity_feasibility_)

        # M.pprint()
        # M.display()
        return M

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


#
# Minimize makespan
#
class GSF_Makespan(Z_Repn_Model):
    def __init__(self):
        self.name = "GSF-makespan"
        self.description = "Supervised process matching minimizing makespan"

    def __call__(self, config, constraints=[]):
        self.config = config
        d = self.data = ProcessModelData(config, constraints)
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
            Gamma=d.Gamma,
            Tmax=d.Tmax,
            Upsilon=d.Upsilon,
            tprev=d.tprev,
            verbose=config.verbose,
        )

        self.enforce_constraints(self.M, constraints, verbose=config.verbose)

    def create_model(
        self, *, objective, T, J, K, S, O, P, Q, E, Gamma, Tmax, Upsilon, tprev, verbose
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
            objective == "minimize_makespan"
        ), "GSF_Makespan can not optimize the goal {}".format(objective)

        M = pe.ConcreteModel()

        M.z = pe.Var(J, [-1] + T, within=pe.Binary)
        M.a = pe.Var(J, T, within=pe.Binary)
        M.o = pe.Var(J, bounds=(0, None))
        M.O = pe.Var()

        # Objective

        M.objective = pe.Objective(
            sense=pe.minimize, expr=M.O + (1e-3) * sum(M.o[j] for j in J)
        )

        def omax_(m, j):
            return M.o[j] <= M.O

        M.omax = pe.Constraint(J, rule=omax_)

        def odef_(m, j):
            return m.o[j] == sum(t * (m.z[j, t] - m.z[j, t - 1]) for t in T) + (
                Tmax - 1
            ) * (1 - m.z[j, Tmax - 1])

        M.odef = pe.Constraint(J, rule=odef_)

        # Simultenaity constraints

        if not Upsilon is None:

            def activity_limit_(m, t):
                return sum(m.a[j, t] for j in J) <= Upsilon

            M.activity_limit = pe.Constraint(T, rule=activity_limit_)

        # Z constraints

        def zstep_(m, j, t):
            return m.z[j, t] - m.z[j, t - 1] >= 0

        M.zstep = pe.Constraint(J, T, rule=zstep_)

        def firsta_(m, j, t):
            return m.z[j, t] - m.z[j, t - 1] <= m.a[j, t]

        M.firsta = pe.Constraint(J, T, rule=firsta_)

        def activity_start_(m, j, t):
            if Gamma[j] is None:
                tau = -1
            else:
                tau = max(t - (Q[j] + Gamma[j]), -1)
            return m.z[j, t] - m.z[j, tau] >= m.a[j, t]

        M.activity_start = pe.Constraint(J, T, rule=activity_start_)

        def length_lower_(m, j):
            return sum(m.a[j, t] for t in T) >= P[j] * (m.z[j, Tmax - 1] - M.z[j, -1])

        M.length_lower = pe.Constraint(J, rule=length_lower_)

        def length_upper_(m, j):
            return sum(m.a[j, t] for t in T) <= Q[j] * (m.z[j, Tmax - 1] - M.z[j, -1])

        M.length_upper = pe.Constraint(J, rule=length_upper_)

        def precedence_lb_(m, i, j, t):
            tau = tprev.get((i, t), -1)
            return m.z[i, tau] - m.z[j, t] >= 0

        M.precedence_lb = pe.Constraint(E, T, rule=precedence_lb_)

        def activity_stop_(m, i, j, t):
            return 1 - m.z[j, t] >= m.a[i, t]

        M.activity_stop = pe.Constraint(E, T, rule=activity_stop_)

        # Auxilliary computed values

        def activity_length_(m, j):
            return sum(m.a[j, t] for t in T)

        M.activity_length = pe.Expression(J, rule=activity_length_)

        def weighted_activity_length_(m, j):
            return sum(O[k][t] * m.a[j, t] for k in K[j] for t in T)

        M.weighted_activity_length = pe.Expression(J, rule=weighted_activity_length_)

        def nonactivity_length_(m, j):
            return sum((1 - m.a[j, t]) for t in T)

        M.nonactivity_length = pe.Expression(J, rule=nonactivity_length_)

        def weighted_nonactivity_length_(m, j):
            return sum(O[k][t] * (1 - m.a[j, t]) for k in K[j] for t in T)

        M.weighted_nonactivity_length = pe.Expression(
            J, rule=weighted_nonactivity_length_
        )

        return M


#
# This is the GSF model, annotated to enforce compactness constraints
#
class GSF_TotalMatchScore_Compact(GSF_TotalMatchScore):
    def __init__(self):
        super().__init__(gaps_allowed=False)
        self.name = "CompactMatches_VariableLengthActivities"
        self.description = "Supervised process matching maximizing match score with compactness constraint"

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
        if Gamma != 0:
            print(
                "Warning: Gamma is set to zero in CompactMatches_VariableLengthActivities"
            )
        Gamma = {j: 0 for j in J}
        M = GSF_TotalMatchScore.create_model(
            self,
            objective=objective,
            T=T,
            J=J,
            K=K,
            S=S,
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

        M.z_pre = pe.Var(J, within=pe.Binary, initialize=0)

        def compact_(m, j, t):
            #
            # If we are at time step 0, then there are no precedesors in the
            # time window.
            #
            if t == 0:
                return pe.Constraint.Skip

            e = 0
            skip = True
            for i, j_ in E:
                if j_ == j:
                    tau = tprev.get((i, t), None)
                    #
                    # Skip if latest time that activity i can start is before the time window.
                    #
                    if tau == None or tau < 0:
                        continue
                    tau = tau + P[i] - 1
                    if (i, tau) not in m.a:
                        # WEH - Can this ever happen?
                        print(
                            "BUG in compact formulation? ({},{}) precedence, tprev={} tau={} t={}",
                            i,
                            j,
                            tprev.get((i, t)),
                            tau,
                            t,
                        )
                        return pe.Constraint.Skip
                    skip = False
                    e += m.a[i, tau]
            #
            # If no predecessor activites, then skip this constraint.
            #
            if skip:
                return pe.Constraint.Skip
            #
            # We cannot start activity j at time step if the last time steps
            # that the predecessor activities could be executed are all
            # not active.
            #
            return e + m.z_pre[j] >= m.z[j, t] - m.z[j, t - 1]

        M.compact = pe.Constraint(J, T, rule=compact_)

        def compact_z_(m, i, j):
            return m.z[i, -1] >= m.z_pre[j]

        M.compact_z = pe.Constraint(E, rule=compact_z_)

        return M


#
# This is the XSF model, annotated to enforce compactness constraints
#
class XSF_TotalMatchScore_Compact(XSF_TotalMatchScore):
    def __init__(self):
        self.name = "CompactMatches_FixedLengthActivities"
        self.description = "Supervised process matching maximizing match score with compactness constraints"

    def create_model(
        self, *, objective, T, J, K, S, O, P, Q, E, Tmax, Upsilon, tprev, verbose
    ):
        M = XSF_TotalMatchScore.create_model(
            self,
            objective=objective,
            T=T,
            J=J,
            K=K,
            S=S,
            O=O,
            P=P,
            Q=Q,
            E=E,
            Tmax=Tmax,
            Upsilon=Upsilon,
            tprev=tprev,
            verbose=verbose,
        )

        M.z_pre = pe.Var(J, within=pe.Binary, initialize=0)

        def compact_(m, j, t):
            #
            # If we are at time step 0, then there are no precedesors in the
            # time window.
            #
            if t == 0:
                return pe.Constraint.Skip

            e = 0
            skip = True
            for i, j_ in E:
                if j_ == j:
                    tau = tprev.get((i, t), None)
                    #
                    # Skip if latest time that activity i can start is before the time window.
                    #
                    if tau == None or tau < 0:
                        continue
                    #
                    # NOTE:  Since we consider fixed-length activities,
                    #           the activity is executed at time tau + P[i]-1 if it is
                    #           executed at time tau.  Hence, we don't adjust tau here,
                    #           but instead test the value z[i,tau]-z[i,tau-1] to detect
                    #           if the activity is executed at time tau+P[i]-1.
                    #
                    if (i, tau) not in m.z:
                        # WEH - Can this ever happen?
                        print(
                            "BUG in compact formulation? ({},{}) precedence, tprev={} tau={} t={}",
                            i,
                            j,
                            tprev.get((i, t)),
                            tau,
                            t,
                        )
                        return pe.Constraint.Skip
                    skip = False
                    e += m.z[i, tau] - m.z[i, tau - 1]
            #
            # If no predecessor activites, then skip this constraint.
            #
            if skip:
                return pe.Constraint.Skip

            return e + m.z_pre[j] >= m.z[j, t] - m.z[j, t - 1]

        M.compact = pe.Constraint(J, T, rule=compact_)

        def compact_z_(m, i, j):
            return m.z[i, -1] >= m.z_pre[j]

        M.compact_z = pe.Constraint(E, rule=compact_z_)

        return M


def create_model(name):
    if (
        name == "model11"
        or name == "GSF"
        or name == "UnrestrictedMatches_VariableLengthActivities_GapsAllowed"
    ):
        return GSF_TotalMatchScore(gaps_allowed=True)

    elif name == "UnrestrictedMatches_VariableLengthActivities":
        return GSF_TotalMatchScore(gaps_allowed=False)

    elif (
        name == "GSF-compact"
        or name == "GSFC"
        or name == "CompactMatches_VariableLengthActivities"
    ):
        return GSF_TotalMatchScore_Compact()

    elif name == "model13" or name == "GSF-ED":
        return GSFED_TotalMatchScore()

    elif name == "GSF-makespan":
        return GSF_Makespan()

    elif name == "XSF" or name == "UnrestrictedMatches_FixedLengthActivities":
        return XSF_TotalMatchScore()

    elif (
        name == "XSF-compact"
        or name == "XSFC"
        or name == "CompactMatches_FixedLengthActivities"
    ):
        return XSF_TotalMatchScore_Compact()

    elif name == "model12" or name == "model14" or name == "UPM":
        return UPM_TotalMatchScore()
