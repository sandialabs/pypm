#
# C. Artigues. A note on time-indexed formulations for the resource-constrained 
# project scheduling problem
#
#   https://hal.archives-ouvertes.fr/hal-00833321/document
#
# TODO: Consider whether the discussion on p. 5 allows for a reformulation that is unimodular in x.
#
import pyomo.environ as pe

def add_objective(*, M, J, T, S, K):
    def o_(m):
        return sum(sum(S[j,k]*m.r[j,k,t] for j in J for k in K[j]) for t in T)
    M.o = pe.Objective(sense=pe.maximize, rule=o_)

def add_rdef_constraints_supervised(*, M, JK, T, O):
    def rdef1_(m, j, k, t):
        return m.r[j,k,t] <= m.a[j,t]
    M.rdef1 = pe.Constraint(JK, T, rule=rdef1_)

    def rdef2_(m, j, k, t):
        return m.r[j,k,t] <= O[k][t]
    M.rdef2 = pe.Constraint(JK, T, rule=rdef2_)

def add_rdef_constraints_unsupervised(*, M, K, JK, T, O, U):
    def rdef1_(m, j, k, t):
        return m.r[j,k,t] <= m.a[j,t]
    M.rdef1 = pe.Constraint(JK, T, rule=rdef1_)

    def rdef2_(m, j, k, t):
        return m.r[j,k,t] <= sum(m.m[k,u]*O[u][t] for u in U)
    M.rdef2 = pe.Constraint(JK, T, rule=rdef2_)

    def rdef3_(m, k):
        return sum(m.m[k,u] for u in U) <= 1
    M.rdef3 = pe.Constraint(K, rule=rdef3_)

def add_xdef_constraints(*, M, T, J, p, E):
    def start_once_(m,j):
        return sum(m.x[j,t] for t in T) <= 1
    M.start_once = pe.Constraint(J, rule=start_once_)

    def precedence_(m, i, j):
        return sum(t*m.x[i,t] for t in T) + p[i] <= sum(t*m.x[j,t] for t in T)
    M.precedence = pe.Constraint(E, rule=precedence_)

def add_xydef_constraints(*, M, T, J, p, E, max_delay):
    def start_once_(m,j):
        return sum(m.x[j,t] for t in T) <= 1
    M.start_once = pe.Constraint(J, rule=start_once_)

    def stop_once_(m,j):
        return sum(m.y[j,t] for t in T) <= 1
    M.stop_once = pe.Constraint(J, rule=stop_once_)

    def precedence_(m, i, j):
        return sum(t*m.x[j,t] for t in T) - sum(t*m.y[i,t] for t in T)
    M.precedence = pe.Expression(E, rule=precedence_)

    def precedence_lower_(m, i, j):
        return m.precedence[i,j] >= 1
    M.precedence_lower = pe.Constraint(E, rule=precedence_lower_)

    def precedence_upper_(m, i, j):
        return m.precedence[i,j] <= 1 + max_delay
    M.precedence_upper = pe.Constraint(E, rule=precedence_upper_)

def add_adefx_constraints(*, M, J, T, p):
    def activity_(m, j, t):
        return sum(m.x[j,t-s] for s in range(p[j]) if t-s >= 0) >= m.a[j,t]
    M.activity = pe.Constraint(J, T, rule=activity_)

def add_adefxy_constraints(*, M, J, T, Tmax, p, gamma):
    def activity_start_(m, j, t):
        return sum(m.x[j,t-(s+gamma[j])] for s in range(p[j]) if t-(s+gamma[j]) >= 0) >= m.a[j,t]
    M.activity_start = pe.Constraint(J, T, rule=activity_start_)

    def activity_stop_(m, j, t):
        return sum(m.y[j,t+(s+gamma[j])] for s in range(p[j]) if t+(s+gamma[j]) < Tmax) >= m.a[j,t]
    M.activity_stop = pe.Constraint(J, T, rule=activity_stop_)

def add_fixed_length_activities(*, M, T, J, p):
    def fixed_length_(m, j):
        return sum(m.a[j,t] for t in T) == p[j]
    M.fixed_length = pe.Constraint(J, rule=fixed_length_)

def add_variable_length_activities(*, M, T, J, p, q):
    def length_(m, j):
        return sum(m.a[j,t] for t in T)
    M.length = pe.Expression(J, rule=length_)

    def length_lower_(m, j):
        return m.length[j] >= p[j]
    M.length_lower = pe.Constraint(J, rule=length_lower_)

    def length_upper_(m, j):
        return m.length[j] <= q[j]
    M.length_upper = pe.Constraint(J, rule=length_upper_)

def add_simultenaity_constraints(*, M, J, sigma, T, Kall, count, J_k):
    if not sigma is None:
        def activity_default_(m, t):
            return sum(m.a[j,t] for j in J) <= sigma
        M.activity_default = pe.Constraint(T, rule=activity_default_)

    def parallel_resources_(m, k, t):
        if count[k] is None:
            return pe.Constraint.Skip
        return sum(m.a[j,t] for j in J_k[k]) <= count[k]
    M.parallel_resources = pe.Constraint(Kall, T, rule=parallel_resources_)



def create_pyomo_model1(*, K, Tmax, J, E, p, O, S, count, sigma=None):
    """
    Supervised Process Matching

    Tmax - Number of timesteps
    E - set of (i,j) pairs that represent precedence constraints
    p[j] - The length of activity j
    O[k][t] - The observation data for resource k at time t
    """
    T = list(range(Tmax))
    Kall = list(sorted(count.keys()))
    JK = [(j,k) for j in J for k in K[j]]
    J_k = {k:[] for k in Kall}
    for j in J:
        for k in K[j]:
            J_k[k].append(j)
    
    M = pe.ConcreteModel()

    M.x = pe.Var(J, T, within=pe.Binary)
    M.a = pe.Var(J, T, within=pe.Binary)
    M.r = pe.Var(JK, T, bounds=(0,1))

    add_objective(M=M, J=J, T=T, S=S, K=K)
    add_xdef_constraints(M=M, T=T, p=p, J=J, E=E)
    add_adefx_constraints(M=M, J=J, T=T, p=p)
    add_fixed_length_activities(M=M, T=T, J=J, p=p)
    add_rdef_constraints_supervised(M=M, JK=JK, T=T, O=O)
    add_simultenaity_constraints(M=M, J=J, sigma=sigma, T=T, Kall=Kall, count=count, J_k=J_k)

    return M


def create_model1(*, observations, pm, timesteps, sigma=None):
    # Supervised
    # Fixed-length activities
    # No gaps within or between activities
    E = [(pm[dep]['name'],i) for i in pm for dep in pm[i]['dependencies']]
    p = {j:pm[j]['duration']['min_hours'] for j in pm}
    J = list(sorted(pm))
    K = {j:set(pm[j]['resources']) for j in pm}
    S = {(j,k):1 if k in K[j] else 0 for j in pm for k in observations}
    count = {name:pm.resources.count(name) for name in pm.resources}

    return create_pyomo_model1(K=K, Tmax=timesteps, J=J, 
                               E=E, p=p, O=observations, S=S, sigma=sigma, count=count)


def create_pyomo_model2(*, K, Tmax, J, E, p, U, O, S, count, sigma=None):
    """
    Supervised Process Matching

    Tmax - Number of timesteps
    E - set of (i,j) pairs that represent precedence constraints
    p[j] - The length of activity j
    O[k][t] - The observation data for resource k at time t
    """
    T = list(range(Tmax))
    Kall = list(sorted(count.keys()))
    JK = [(j,k) for j in J for k in K[j]]
    J_k = {k:[] for k in Kall}
    for j in J:
        for k in K[j]:
            J_k[k].append(j)
    
    M = pe.ConcreteModel()

    M.x = pe.Var(J, T, within=pe.Binary)
    M.a = pe.Var(J, T, within=pe.Binary)
    M.r = pe.Var(JK, T, bounds=(0,1))
    M.m = pe.Var(Kall, U, bounds=(0,1))

    add_objective(M=M, J=J, T=T, S=S, K=K)
    add_xdef_constraints(M=M, T=T, p=p, J=J, E=E)
    add_adefx_constraints(M=M, J=J, T=T, p=p)
    add_fixed_length_activities(M=M, T=T, J=J, p=p)
    add_rdef_constraints_unsupervised(M=M, K=Kall, JK=JK, T=T, O=O, U=U)
    add_simultenaity_constraints(M=M, J=J, sigma=sigma, T=T, Kall=Kall, count=count, J_k=J_k)

    return M


def create_model2(*, observations, pm, timesteps, sigma=None):
    # Unsupervised
    # Fixed-length activities
    # No gaps within or between activities
    U = list(sorted(observations.keys()))
    E = [(pm[dep]['name'],i) for i in pm for dep in pm[i]['dependencies']]
    p = {j:pm[j]['duration']['min_hours'] for j in pm}
    J = list(sorted(pm))
    K = {j:set(pm[j]['resources']) for j in pm}
    Kall = set.union(*[v for v in K.values()])
    S = {(j,k):1 if k in K[j] else 0 for j in pm for k in Kall}
    count = {name:pm.resources.count(name) for name in pm.resources}

    return create_pyomo_model2(K=K, Tmax=timesteps, J=J, 
                               E=E, p=p, U=U, O=observations, S=S, sigma=sigma, count=count)


def create_pyomo_model3(*, K, Tmax, J, E, p, q, O, S, count, gamma=0, max_delay=0, sigma=None):
    """
    Extended Supervised Process Matching

    Tmax - Number of timesteps
    E - set of (i,j) pairs that represent precedence constraints
    p[j] - The length of activity j
    O[k][t] - The observation data for resource k at time t
    """
    T = list(range(Tmax))
    Kall = list(sorted(count.keys()))
    JK = [(j,k) for j in J for k in K[j]]
    J_k = {k:[] for k in Kall}
    for j in J:
        for k in K[j]:
            J_k[k].append(j)
    if not type(gamma) is dict:
        gamma = {j:gamma for j in J}
    
    M = pe.ConcreteModel()

    M.x = pe.Var(J, T, within=pe.Binary)
    M.y = pe.Var(J, T, within=pe.Binary)
    M.a = pe.Var(J, T, within=pe.Binary)
    M.r = pe.Var(JK, T, bounds=(0,1))

    add_objective(M=M, J=J, T=T, S=S, K=K)
    add_xydef_constraints(M=M, T=T, p=p, J=J, E=E, max_delay=max_delay)
    add_adefxy_constraints(M=M, J=J, T=T, Tmax=Tmax, p=p, gamma=gamma)
    add_variable_length_activities(M=M, T=T, J=J, p=p, q=q)
    add_rdef_constraints_supervised(M=M, JK=JK, T=T, O=O)
    add_simultenaity_constraints(M=M, J=J, sigma=sigma, T=T, Kall=Kall, count=count, J_k=J_k)

    return M


def create_model3(*, observations, pm, timesteps, sigma=None, gamma=0, max_delay=0):
    # Supervised
    # Fixed-length activities
    # No gaps within or between activities
    E = [(pm[dep]['name'],i) for i in pm for dep in pm[i]['dependencies']]
    p = {j:pm[j]['duration']['min_hours'] for j in pm}
    q = {j:pm[j]['duration']['max_hours'] for j in pm}
    J = list(sorted(pm))
    K = {j:set(pm[j]['resources']) for j in pm}
    S = {(j,k):1 if k in K[j] else 0 for j in pm for k in observations}
    count = {name:pm.resources.count(name) for name in pm.resources}

    return create_pyomo_model3(K=K, Tmax=timesteps, J=J, 
                               E=E, p=p, q=q, O=observations, S=S, sigma=sigma, 
                               count=count, gamma=gamma, max_delay=max_delay)


def create_pyomo_model4(*, K, Tmax, J, E, p, q, U, O, S, count, gamma=0, max_delay=0, sigma=None):
    """
    Supervised Process Matching

    Tmax - Number of timesteps
    E - set of (i,j) pairs that represent precedence constraints
    p[j] - The length of activity j
    O[k][t] - The observation data for resource k at time t
    """
    T = list(range(Tmax))
    Kall = list(sorted(count.keys()))
    JK = [(j,k) for j in J for k in K[j]]
    J_k = {k:[] for k in Kall}
    for j in J:
        for k in K[j]:
            J_k[k].append(j)
    if not type(gamma) is dict:
        gamma = {j:gamma for j in J}
 
    M = pe.ConcreteModel()

    M.x = pe.Var(J, T, within=pe.Binary)
    M.y = pe.Var(J, T, within=pe.Binary)
    M.a = pe.Var(J, T, within=pe.Binary)
    M.r = pe.Var(JK, T, bounds=(0,1))
    M.m = pe.Var(Kall, U, bounds=(0,1))

    add_objective(M=M, J=J, T=T, S=S, K=K)
    add_xydef_constraints(M=M, T=T, p=p, J=J, E=E, max_delay=max_delay)
    add_adefxy_constraints(M=M, J=J, T=T, p=p, gamma=gamma, Tmax=Tmax)
    add_variable_length_activities(M=M, T=T, J=J, p=p, q=q)
    add_rdef_constraints_unsupervised(M=M, K=Kall, JK=JK, T=T, O=O, U=U)
    add_simultenaity_constraints(M=M, J=J, sigma=sigma, T=T, Kall=Kall, count=count, J_k=J_k)

    return M


def create_model4(*, observations, pm, timesteps, sigma=None, gamma=0, max_delay=0):
    # Unsupervised
    # Fixed-length activities
    # No gaps within or between activities
    U = list(sorted(observations.keys()))
    E = [(pm[dep]['name'],i) for i in pm for dep in pm[i]['dependencies']]
    p = {j:pm[j]['duration']['min_hours'] for j in pm}
    q = {j:pm[j]['duration']['max_hours'] for j in pm}
    J = list(sorted(pm))
    K = {j:set(pm[j]['resources']) for j in pm}
    Kall = set.union(*[v for v in K.values()])
    S = {(j,k):1 if k in K[j] else 0 for j in pm for k in Kall}
    count = {name:pm.resources.count(name) for name in pm.resources}

    return create_pyomo_model4(K=K, Tmax=timesteps, J=J, 
                               E=E, p=p, q=q, U=U, O=observations, S=S, sigma=sigma, 
                               count=count, gamma=gamma, max_delay=max_delay)

