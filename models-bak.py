import pyomo.environ as pe

def create_model1(Tmax, Jmax, E, p, O):
    """
    Simple model with fixed-length jobs

    Tmax - Number of timesteps
    Jmax - Number of activities
    E - set of (i,j) pairs that represent precedence constraints
    p[j] - The length of activity j
    O(j,t) - Value of predicting activity j at time t
        j == Jmax indicates no activity predicted
    """
    T = list(range(Tmax))
    J = list(range(Jmax))
    J1 = list(range(Jmax+1))
    
    M = pe.ConcreteModel()

    M.x = pe.Var(J, T, within=pe.Binary)
    M.a = pe.Var(J1, T, bounds=(0,1))

    def o_(m):
        return sum(O(j,t)*m.a[j,t] for j in J1 for t in T)
    M.o = pe.Objective(sense=pe.maximize, rule=o_)

    def start_once_(m,j):
        return sum(m.x[j,t] for t in T) == 1
    M.start_once = pe.Constraint(J, rule=start_once_)

    #
    # C. Artigues. A note on time-indexed formulations for theresource-constrained project scheduling problem
    # https://hal.archives-ouvertes.fr/hal-00833321/document
    #
    # TODO: Consider whether the discussion on p. 5 allows for a reformulation that is unimodular in x.
    #
    def precedence_(m, i, j):
        return sum(t*m.x[i,t] for t in T) + p[i] <= sum(t*m.x[j,t] for t in T)
    M.precedence = pe.Constraint(E, rule=precedence_)

    def activity_(m, j, t):
        return sum(m.x[j,t-s] for s in range(p[j]) if t-s >= 0) >= m.a[j,t]
    M.activity = pe.Constraint(J, T, rule=activity_)

    def activity_default_(m, t):
        return sum(m.a[j,t] for j in J1) == 1
    M.activity_default = pe.Constraint(T, rule=activity_default_)

    M.solns = pe.ConstraintList()

    return M


def create_model2(Tmax, Jmax, E, pmin, pmax, O):
    """
    Tmax - Number of timesteps
    Jmax - Number of activities
    E - set of (i,j) pairs that represent precedence constraints
    pmin[j] - The minimum length of activity j
    pmax[j] - The maximum length of activity j
    O(j,t) - Value of predicting activity j at time t
        j == Jmax indicates no activity predicted
    """
    T = list(range(Tmax))
    J = list(range(Jmax))
    J1 = list(range(Jmax+1))
    
    M = pe.ConcreteModel()

    M.x = pe.Var(J, T, within=pe.Binary)
    M.a = pe.Var(J1, T, bounds=(0,1))

    def o_(m):
        return sum(O(j,t)*m.a[j,t] for j in J1 for t in T)
    M.o = pe.Objective(sense=pe.maximize, rule=o_)

    def start_once_(m,j):
        return sum(m.x[j,t] for t in T) == 1
    M.start_once = pe.Constraint(J, rule=start_once_)

    #
    # C. Artigues. A note on time-indexed formulations for theresource-constrained project scheduling problem
    # https://hal.archives-ouvertes.fr/hal-00833321/document
    #
    # TODO: Consider whether the discussion on p. 5 allows for a reformulation that is unimodular in x.
    #
    def precedence_(m, i, j):
        return sum(t*m.x[i,t] for t in T) + pmin[i] <= sum(t*m.x[j,t] for t in T)
    M.precedence = pe.Constraint(E, rule=precedence_)

    def activity_(m, j, t):
        return sum(m.x[j,t-s] for s in range(pmax[j]) if t-s >= 0) >= m.a[j,t]
    M.activity = pe.Constraint(J, T, rule=activity_)

    def activity_default_(m, t):
        return sum(m.a[j,t] for j in J1) == 1
    M.activity_default = pe.Constraint(T, rule=activity_default_)

    M.activity_succ = pe.ConstraintList()
    for i,j in E:
        num = pmax[i] - pmin[i]
        if num > 0:
            for t in T:
                for s in range(num):
                    if t+s < Tmax:
                        M.activity_succ.add( 1 - M.x[j,t] >= M.a[i,t+s] )

    return M


if __name__ == "__main__":
    def Ofn(j, t):
        if j == 0 and t >= 100 and t < 102:
            return 1
        elif j == 1 and t >= 112 and t < 115:
            return 2
        elif j == 2 and t >= 115 and t < 120:
            return 3
        elif j == 3 and t >= 120 and t < 127:
            return 4
        elif j == 4 and t >= 127 and t < 138:
            return 5
        return 0
       
    Jmax = 5
    pmin = [2,3,5,7,11]
    M = create_model1(200, Jmax, [(0,1), (1,2), (2,3), (3,4)], pmin, Ofn)
    opt = pe.SolverFactory('glpk')
    res = opt.solve(M, tee=True)
    print(res)
    for j,t in M.x:
        if M.x[j,t].value > 0.1:
            print('x', j,t, M.x[j,t].value)
    #for j,t in M.a:
    #    if j == Jmax:
    #        continue
    #    if M.a[j,t].value > 0.1:
    #        print('a', j,t, M.a[j,t].value)

    for i in range(10):
        M.solns.add( sum(M.x[j,t] for j,t in M.x if M.x[j,t].value > 0.9) <= Jmax - 1 )
        res = opt.solve(M, tee=True)
        print(res)
        for j,t in M.x:
            if M.x[j,t].value > 0.1:
                print('x', j,t, M.x[j,t].value)
    
if False:
    pmin = [2,3,5,7,11]
    pmax = [4,5,7,9,13]
    M = create_model2(200, Jmax, [(0,1), (1,2), (2,3), (3,4)], pmin, pmax, Ofn)
    opt = pe.SolverFactory('glpk')
    res = opt.solve(M, tee=True)
    print(res)
    for j,t in M.x:
        if M.x[j,t].value > 0.1:
            print('x', j,t, M.x[j,t].value)
    for j,t in M.a:
        if j == Jmax:
            continue
        if M.a[j,t].value > 0.1:
            print('a', j,t, M.a[j,t].value)
