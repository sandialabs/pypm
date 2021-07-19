# pymp.mip.runmip

import yaml
import pprint
from pypm.util.load import load_data
from pypm.mip.models import create_model1
import pyomo.environ as pe


def get_nonzero_variables(M):
    ans = {}
    for v in M.component_objects(pe.Var, active=True):
        ans[v.name] = {}
        for index in v:
            if pe.value(v[index]) > 1e-7:
                ans[v.name][index] = pe.value(v[index])
    return ans

def summarize_alignment(v):
    ans = {}
    a = v['a']
    for key,value in a.items():
        j,t = key
        if not j in ans:
            ans[j] = {'start':t, 'stop':t}
        else:
            if t < ans[j]['start']:
                ans[j]['start'] = t        
            if t > ans[j]['stop']:
                ans[j]['stop'] = t        
    return ans
 
def runmip_from_datafile(*, datafile, index, model=None, tee=None, solver=None):
    with open(datafile, 'r') as INPUT:
        data = yaml.safe_load(INPUT)

    tee = data['_options'].get('tee', False) if tee is None else tee
    model = data['_options'].get('model', 'model1') if model is None else model
    solver = data['_options'].get('solver', 'glpk') if solver is None else solver
    pm = load_data(data['_options']['process'])
    observations = data['data'][index]['observations']

    if model == 'model1':
        M = create_model1(observations=observations,
                            pm=pm, 
                            timesteps=data['_options']['timesteps'],
                            sigma=data['_options'].get('sigma',None))
        opt = pe.SolverFactory(solver)
        results = opt.solve(M, tee=tee)

        variables = variables=get_nonzero_variables(M)
        alignment = summarize_alignment(variables)
        res = dict(datafile=datafile, index=index, model=model, objective=pe.value(M.o), variables=variables, alignment=alignment)

    return res
