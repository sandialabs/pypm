#
# C. Artigues. A note on time-indexed formulations for theresource-constrained project scheduling problem
# https://hal.archives-ouvertes.fr/hal-00833321/document
#
# TODO: Consider whether the discussion on p. 5 allows for a reformulation that is unimodular in x.
#
import pyomo.environ as pe

def add_objective(*, M, J, T, S, K):
    def o_(m):
        return sum(sum(S[j,k]*m.r[j,k,t] for j in J for k in K[j]) for t in T)
    M.o = pe.Objective(sense=pe.maximize, rule=o_)

def add_rdef_constraints_supervised(*, M, J_K, T, O):
    def rdef1_(m, j, k, t):
        return m.r[j,k,t] <= m.a[j,t]
    M.rdef1 = pe.Constraint(J_K, T, rule=rdef1_)

    def rdef2_(m, j, k, t):
        return m.r[j,k,t] <= O[k][t]
    M.rdef2 = pe.Constraint(J_K, T, rule=rdef2_)

def add_rdef_constraints_unsupervised(*, M, K, J_K, T, O, U):
    def rdef1_(m, j, k, t):
        return m.r[j,k,t] <= m.a[j,t]
    M.rdef1 = pe.Constraint(J_K, T, rule=rdef1_)

    def rdef2_(m, j, k, t):
        return m.r[j,k,t] <= sum(m.m[k,u]*O[u][t] for u in U)
    M.rdef2 = pe.Constraint(J_K, T, rule=rdef2_)

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

def add_adef_constraints(*, M, J, T, p):
    def activity_(m, j, t):
        return sum(m.x[j,t-s] for s in range(p[j]) if t-s >= 0) >= m.a[j,t]
    M.activity = pe.Constraint(J, T, rule=activity_)

def add_fixed_length_tasks(*, M, T, J, p):
    def fixed_length_(m, j):
        return sum(m.a[j,t] for t in T) == p[j]
    M.fixed_length = pe.Constraint(J, rule=fixed_length_)

def add_simultenaity_constraints(*, M, J, sigma, T):
    def activity_default_(m, t):
        return sum(m.a[j,t] for j in J) <= sigma
    M.activity_default = pe.Constraint(T, rule=activity_default_)




def create_pyomo_model1(*, K, Tmax, Jmax, E, p, O, S, sigma=None):
    """
    Supervised Process Matching

    Tmax - Number of timesteps
    Jmax - Number of activities
    Kmax - Number of resources
    E - set of (i,j) pairs that represent precedence constraints
    p[j] - The length of activity j
    O[k][t] - The observation data for resource k at time t
    """
    T = list(range(Tmax))
    J = list(range(Jmax))
    J_K = [(j,k) for j in J for k in K[j]]
    
    M = pe.ConcreteModel()

    M.x = pe.Var(J, T, within=pe.Binary)
    M.a = pe.Var(J, T, within=pe.Binary)
    M.r = pe.Var(J_K, T, bounds=(0,1))

    add_objective(M=M, J=J, T=T, S=S, K=K)
    add_xdef_constraints(M=M, T=T, p=p, J=J, E=E)
    add_adef_constraints(M=M, J=J, T=T, p=p)
    add_fixed_length_tasks(M=M, T=T, J=J, p=p)
    add_rdef_constraints_supervised(M=M, J_K=J_K, T=T, O=O)
    if not sigma is None:
        add_simultenaity_constraints(M=M, J=J, sigma=sigma, T=T)

    #M.solns = pe.ConstraintList()

    return M


def create_model1(*, observations, pm, timesteps, sigma=None):
    # Supervised
    # Fixed-length activities
    # No gaps within or between activities
    E = [(pm[dep]['id'],i) for i in pm for dep in pm[i]['dependencies']]
    p = {j:pm[j]['duration']['min_hours'] for j in pm}
    K = {j:set(pm[j]['resources']) for j in pm}
    S = {(j,k):1 if k in K[j] else 0 for j in pm for k in observations}

    return create_pyomo_model1(K=K, Tmax=timesteps, Jmax=len(pm), 
                               E=E, p=p, O=observations, S=S, sigma=sigma)


def create_pyomo_model2(*, K, Tmax, Jmax, E, p, U, O, S, sigma=None):
    """
    Supervised Process Matching

    Tmax - Number of timesteps
    Jmax - Number of activities
    Kmax - Number of resources
    E - set of (i,j) pairs that represent precedence constraints
    p[j] - The length of activity j
    O[k][t] - The observation data for resource k at time t
    """
    T = list(range(Tmax))
    J = list(range(Jmax))
    Kall = []
    for Kj in K.values():
        Kall += Kj
    Kall = list(sorted(set(Kall)))
    J_K = [(j,k) for j in J for k in K[j]]
    
    M = pe.ConcreteModel()

    M.x = pe.Var(J, T, within=pe.Binary)
    M.a = pe.Var(J, T, within=pe.Binary)
    M.r = pe.Var(J_K, T, bounds=(0,1))
    M.m = pe.Var(Kall, U, bounds=(0,1))

    add_objective(M=M, J=J, T=T, S=S, K=K)
    add_xdef_constraints(M=M, T=T, p=p, J=J, E=E)
    add_adef_constraints(M=M, J=J, T=T, p=p)
    add_fixed_length_tasks(M=M, T=T, J=J, p=p)
    add_rdef_constraints_unsupervised(M=M, K=Kall, J_K=J_K, T=T, O=O, U=U)
    if not sigma is None:
        add_simultenaity_constraints(M=M, J=J, sigma=sigma, T=T)

    #M.solns = pe.ConstraintList()

    return M


def create_model2(*, observations, pm, timesteps, sigma=None):
    # Unsupervised
    # Fixed-length activities
    # No gaps within or between activities
    U = list(sorted(observations.keys()))
    E = [(pm[dep]['id'],i) for i in pm for dep in pm[i]['dependencies']]
    p = {j:pm[j]['duration']['min_hours'] for j in pm}
    K = {j:set(pm[j]['resources']) for j in pm}
    Kall = set.union(*[v for v in K.values()])
    S = {(j,k):1 if k in K[j] else 0 for j in pm for k in Kall}

    return create_pyomo_model2(K=K, Tmax=timesteps, Jmax=len(pm), 
                               E=E, p=p, U=U, O=observations, S=S, sigma=sigma)


