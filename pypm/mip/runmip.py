# pymp.mip.runmip

import yaml
import pprint
import csv
import pandas as pd
from os.path import join
from pypm.util.load import load_process
from pypm.mip.models import create_model1, create_model2, create_model3, create_model4
import pyomo.environ as pe


def get_nonzero_variables(M):
    ans = {}
    for v in M.component_objects(pe.Var, active=True):
        ans[v.name] = {}
        for index in v:
            if pe.value(v[index]) > 1e-7:
                ans[v.name][index] = pe.value(v[index])
    return ans

def summarize_alignment(v, model):
    ans = {}
    if model in ['model1', 'model2']:
        a = v['a']
        for key,val in a.items():
            j,t = key
            if not j in ans:
                ans[j] = {'start':t, 'stop':t}
            else:
                if t < ans[j]['start']:
                    ans[j]['start'] = t        
                if t > ans[j]['stop']:
                    ans[j]['stop'] = t        
    else:
        x = v['x']
        y = v['y']
        for key,val in x.items():
            if val < 1-1e-7:
                continue
            j,t = key
            ans[j] = {'start':t}
        for key,val in y.items():
            if val < 1-1e-7:
                continue
            j,t = key
            ans[j]['stop'] = t
    return ans
 
def runmip_from_datafile(*, datafile=None, data=None, index=0, model=None, tee=None, solver=None, dirname=None, debug=False):
    if data is None:
        assert datafile is not None
        with open(datafile, 'r') as INPUT:
            data = yaml.safe_load(INPUT)

    tee = data['_options'].get('tee', False) if tee is None else tee
    model = data['_options'].get('model', 'model3') if model is None else model
    solver = data['_options'].get('solver', 'glpk') if solver is None else solver
    pm = load_process(data['_options']['process'], dirname=dirname)
    observations = data['data'][index]['observations']
    if type(observations) is list:
        observations_ = {}
        for filename in observations:
            fname = filename if dirname is None else join(dirname,filename)
            if fname.endswith(".csv"):
                df = pd.read_csv(fname)
                observations_.update( df.to_dict(orient='list') )
            elif fname.endswith(".yaml"):
                with open(fname, 'r') as INPUT:
                    observations_ = yaml.safe_load(INPUT)
    else:
        assert (type(observations) is dict), "Expected observations to be a dictionary or a list of CSV files"
        observations_ = observations

    print("Creating model")
    if model in ['model1', 'model2', 'model3', 'model4']:
        if model == 'model1':
            M = create_model1(observations=observations_,
                            pm=pm, 
                            timesteps=data['_options']['timesteps'],
                            sigma=data['_options'].get('sigma',None))
        elif model == 'model2':
            M = create_model2(observations=observations_,
                            pm=pm, 
                            timesteps=data['_options']['timesteps'],
                            sigma=data['_options'].get('sigma',None))
        elif model == 'model3':
            M = create_model3(observations=observations_,
                            pm=pm, 
                            timesteps=data['_options']['timesteps'],
                            sigma=data['_options'].get('sigma',None), 
                            gamma=data['_options'].get('gamma',0),
                            max_delay=data['_options'].get('max_delay',0))
        elif model == 'model4':
            M = create_model4(observations=observations_,
                            pm=pm, 
                            timesteps=data['_options']['timesteps'],
                            sigma=data['_options'].get('sigma',None),
                            gamma=data['_options'].get('gamma',0),
                            max_delay=data['_options'].get('max_delay',0))

        print("Optimizing model")
        opt = pe.SolverFactory(solver)
        results = opt.solve(M, tee=tee)
        if debug:           #pragma:nocover
            M.pprint()
            M.display()

        variables = variables=get_nonzero_variables(M)
        alignment = summarize_alignment(variables, model)
        res = dict(datafile=datafile, index=index, model=model, 
                    results=[dict(objective=pe.value(M.o), variables=variables, alignment=alignment)])

    return res

