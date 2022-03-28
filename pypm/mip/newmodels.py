import datetime
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
def fracval(num,denom):
    if denom != 0:
        return num/denom
    return 0


class ProcessModelData(object):

    def __init__(self, data):
        pm = data.pm
        Kall = list(sorted(name for name in pm.resources))

        self.Tmax = data.obs.timesteps
        self.T = list(range(self.Tmax))

        self.O = data.obs.observations
        #self.U = list(sorted(self.O.keys()))
        self.E = [(pm[dep]['name'],i) for i in pm for dep in pm[i]['dependencies']]
        self.P = {j:pm[j]['duration']['min_hours'] for j in pm}
        self.Q = {j:pm[j]['duration']['max_hours'] for j in pm}
        self.Omega = {j:0 if pm[j]['max_delay'] is None else pm[j]['max_delay'] for j in pm}
        #self.count = {name:pm.resources.count(name) for name in pm.resources}

        self.J = list(sorted(pm))
        self.K = {j:set(pm[j]['resources'].keys()) for j in pm}
        #self.Kall = list(sorted(self.count.keys()))
        self.JK = [(j,k) for j in self.J for k in self.K[j]]
        #self.J_k = {k:[] for k in Kall}
        #for j in self.J:
        #    for k in self.K[j]:
        #        self.J_k[k].append(j)

        if hasattr(data,'gamma') and type(data.gamma) is dict:
            self.Gamma = data.gamma
        else:
            self.Gamma = {j:data.get('gamma',0) for j in self.J}
        self.Upsilon = data.get('sigma',None)
        self.S = {(j,k):1 if k in self.K[j] else 0 for j in pm for k in Kall}


class BaseModel(object):

    def summarize(self):
        variables = variables=get_nonzero_variables(self.M)
        alignment = self.summarize_alignment(variables)
        results=dict(objective=pe.value(self.M.objective), variables=variables, schedule=alignment, goals=dict())

        if not self.config.obs.datetime is None:
            obs = self.config.obs
            datetime_alignment = {key:{} for key in alignment}
            lastv = max(v for v in self.config.obs.datetime)
            for key,value in alignment.items():
                for k,v in value.items():
                    if k == 'pre':
                        datetime_alignment[key][k] = obs.datetime[0]
                    elif k == 'post':
                        datetime_alignment[key][k] = obs.datetime[lastv]
                    else:
                        datetime_alignment[key][k] = obs.datetime[v]
                if 'last' in datetime_alignment[key] and v+1 in obs.datetime:
                    datetime_alignment[key]['stop'] = obs.datetime[v+1]
            results['datetime_schedule'] = datetime_alignment

        return results

    def check_labels(self):
        """
        For supervised models, we confirm that the observations have the right labels
        """
        tmp1 = set(self.config.obs.observations.keys())
        tmp2 = set([name for name in self.config.pm.resources])
        assert tmp1.issubset(tmp2), "For supervised process matching, we expect the observations to have labels in the    process model.  The following are unknown resource labels: "+str(tmp1-tmp2)


class Z_Repn_Model(BaseModel):

    def summarize(self):
        results = BaseModel.summarize(self)
        #
        results['goals']['separation'] = {}
        for i in self.M.activity_length:
            if results['schedule'][i].get('pre',False) or results['schedule'][i].get('post',False):
                results['goals']['separation'][i] = 0
            else:
                activity = fracval(pe.value(self.M.weighted_activity_length[i]),pe.value(self.M.activity_length[i]))
                nonactivity = fracval(pe.value(self.M.weighted_nonactivity_length[i]),pe.value(self.M.nonactivity_length[i]))
                results['goals']['separation'][i] = max(0, activity - nonactivity)
        results['goals']['total_separation'] = sum(val for val in results['goals']['separation'].values())
        #
        results['goals']['match'] = {}
        for activity, value in results['variables']['o'].items():
            results['goals']['match'][activity] = value
        results['goals']['total_match'] = sum(val for val in results['goals']['match'].values())
        #
        return results

    def summarize_alignment(self, v):
        ans = {j:{'post':True} for j in self.config.pm}
        z = v['z']
        for key,val in z.items():
            j,t = key
            if val < 1-1e-7:
                continue
            if j in ans and 'post' not in ans[j]:
                continue
            if t == -1:
                ans[j] = {'pre':True}
                continue
            ans[j] = {'first':t, 'last':-1}
        a = v['a']
        for key,val in a.items():
            j,t = key
            if 'pre' in ans[j] or 'post' in ans[j]:
                continue
            if t > ans[j]['last']:
                ans[j]['last'] = t
        return ans

    def enforce_constraints(self, M, constraints, verbose=False):
        if self.config.obs.datetime is None:
            invdatetime = {}
        else:
            invdatetime = {datetime.datetime.fromisoformat(v):k for k,v in self.config.obs.datetime.items()}
        #
        # Set constraints by fixing variables in the model
        #
        for con in constraints:
            if con is None:
                continue

            j = con.activity
            if con.constraint == 'include':
                M.z[j,-1].fix(0)
                M.z[j,self.data.Tmax-1].fix(1)

            elif con.constraint == 'earliest_start':
                if len(invdatetime) == 0:
                    print("WARNING: attemping to apply fix_start constraint with data that does not specify datetime values.")
                    continue
                start = con.startdate
                if isinstance(start, str):
                    start = datetime.datetime.fromisoformat(start)

                for dd,tt in invdatetime.items():
                    diff = dd - start
                    if diff.total_seconds() < 0:
                        M.z[j,tt].fix(0)

            elif con.constraint == 'latest_start':
                if len(invdatetime) == 0:
                    print("WARNING: attemping to apply fix_start constraint with data that does not specify datetime values.")
                    continue
                start = con.startdate
                if isinstance(start, str):
                    start = datetime.datetime.fromisoformat(start)

                for dd,tt in invdatetime.items():
                    diff = dd - start
                    if diff.total_seconds() >= 0:
                        M.z[j,tt].fix(1)

            elif con.constraint == 'fix_start':
                if len(invdatetime) == 0:
                    print("WARNING: attemping to apply fix_start constraint with data that does not specify datetime values.")
                    continue
                start = con.startdate
                if isinstance(start, str):
                    start = datetime.datetime.fromisoformat(start)
                t = invdatetime.get(start,None)

                if t is not None:
                    M.z[j,t].fix(1)
                    M.z[j,t-1].fix(0)
                else:
                    print("WARNING: the fix_start constraint for activity {} specifies the date {} that is not in the time window.".format(activity, con.startdate))
                    mindiff = float('inf')
                    nextd = None
                    for dd,tt in invdatetime.items():
                        diff = dd - start
                        if diff.total_seconds() > 0:
                            if nextd is None or diff.total_seconds() < mindiff:
                                mindiff = diff.total_seconds()
                                nextd = dd
                    if nextd is None:
                        print("\tThe startdate is after the process matching time window.")
                    else:
                        print("\tThe next valid startdate is {}".format(nextd))

            elif con.constraint == 'relax':
                M.z[j,-1].unfix()
                M.z[j,self.data.Tmax-1].unfix()
                for t in self.data.T:
                    M.z[j,t].unfix()

            elif con.constraint == 'relax_start':
                for t in self.data.T:
                    M.z[j,t].unfix()

        if verbose:
            print("Summary of fixed variables")
            for j,t in M.a:
                if M.a[j,t].fixed:
                    print(" ",M.a[j,t], M.a[j,t].value)
            for j,t in M.z:
                if M.z[j,t].fixed:
                    print(" ",M.z[j,t], M.z[j,t].value)



#
# This is the GSF model in Figure 3.2
#
class Model11(Z_Repn_Model):

    def __init__(self):
        self.name = 'model11'
        self.description = 'Supervised process matching maximizing match score'

    def __call__(self, config, constraints=[]):
        self.config = config
        d = self.data = ProcessModelData(config)
        self.constraints = constraints

        self.M = self.create_model(objective=config.objective,
                                J=d.J, T=d.T, S=d.S, K=d.K, 
                                O=d.O, P=d.P, Q=d.Q, E=d.E, Omega=d.Omega, 
                                Gamma=d.Gamma, Tmax=d.Tmax, Upsilon=d.Upsilon, 
                                verbose=config.verbose)

        self.enforce_constraints(self.M, constraints, verbose=config.verbose)

    def create_model(self, *, objective, T, J, K, S, O, P, Q, E, Omega, Gamma, Tmax, Upsilon, verbose):

        assert objective == 'total_match_score', "Model11 can not optimize the goal {}".format(objective)

        M = pe.ConcreteModel()

        M.z = pe.Var(J, [-1]+T, within=pe.Binary)
        M.a = pe.Var(J, T, within=pe.Binary)
        M.o = pe.Var(J, bounds=(0,None))

        # Objective

        def objective_(m):
            return sum(m.o[j] for j in J)
        M.objective = pe.Objective(sense=pe.maximize, rule=objective_)

        def odef_(m, j):
            return m.o[j] == sum(sum((S[j,k]*O[k][t])*m.a[j,t] for k in K[j]) for t in T)
        M.odef = pe.Constraint(J, rule=odef_)

        # Simultenaity constraints

        if not Upsilon is None:
            def activity_limit_(m, t):
                return sum(m.a[j,t] for j in J) <= Upsilon
            M.activity_limit = pe.Constraint(T, rule=activity_limit_)

        # Z constraints

        def zstep_(m, j, t):
            return m.z[j,t] - m.z[j, t-1] >= 0
        M.zstep = pe.Constraint(J, T, rule=zstep_)

        def firsta_(m, j, t):
            return m.z[j,t] - m.z[j,t-1] <= m.a[j,t]
        M.firsta = pe.Constraint(J, T, rule=firsta_)

        def activity_start_(m, j, t):
            #tprev = max(t- (Q[j]+Gamma[j]+Omega[j]), -1)
            tprev = max(t- (Q[j]+Gamma[j]), -1)
            return m.z[j,t] - m.z[j,tprev] >= m.a[j,t]
        M.activity_start = pe.Constraint(J, T, rule=activity_start_)

        def length_lower_(m, j):
            return sum(m.a[j,t] for t in T) >= P[j] * (m.z[j,Tmax-1] - M.z[j,-1])
        M.length_lower = pe.Constraint(J, rule=length_lower_)

        def length_upper_(m, j):
            return sum(m.a[j,t] for t in T) <= Q[j] * (m.z[j,Tmax-1] - M.z[j,-1])
        M.length_upper = pe.Constraint(J, rule=length_upper_)

        def precedence_lb_(m, i, j, t):
            tprev = max(t- (P[i]+Omega[i]), -1)
            return m.z[i,tprev] - m.z[j,t] >= 0
        M.precedence_lb = pe.Constraint(E, T, rule=precedence_lb_)

        def activity_stop_(m, i, j, t):
            return 1 - m.z[j,t] >= m.a[i,t]
        M.activity_stop = pe.Constraint(E, T, rule=activity_stop_)

        # Auxilliary computed values

        def activity_length_(m, j):
            return sum(m.a[j,t] for t in T)
        M.activity_length = pe.Expression(J, rule=activity_length_)

        def weighted_activity_length_(m, j):
            return sum(O[k][t] * m.a[j,t] for k in K[j] for t in T)
        M.weighted_activity_length = pe.Expression(J, rule=weighted_activity_length_)

        def nonactivity_length_(m, j):
            return sum( (1-m.a[j,t]) for t in T)
        M.nonactivity_length = pe.Expression(J, rule=nonactivity_length_)

        def weighted_nonactivity_length_(m, j):
            return sum(O[k][t] * (1-m.a[j,t]) for k in K[j] for t in T)
        M.weighted_nonactivity_length = pe.Expression(J, rule=weighted_nonactivity_length_)

        return M



def create_model(name):
    if name == 'model11':
        return Model11()
    elif name == 'GSF':
        return Model11()

