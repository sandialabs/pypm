# pymp.mip.runmip

import yaml
import pprint
import csv
import pandas as pd
from os.path import join
from pypm.util.load import load_process
from pypm.mip.models import create_model1, create_model2, create_model3, create_model4, create_model5, create_model78
import pyomo.environ as pe


def get_nonzero_variables(M):
    ans = {}
    for v in M.component_objects(pe.Var, active=True):
        ans[v.name] = {}
        for index in v:
            if pe.value(v[index]) > 1e-7:
                ans[v.name][index] = pe.value(v[index])
    return ans

def summarize_alignment(v, model, pm, timesteps=None):
    ans = {}
    if model in ['model1', 'model2']:
        a = v['a']
        for key,val in a.items():
            j,t = key
            if not j in ans:
                ans[j] = {'first':t, 'last':t}
            else:
                if t < ans[j]['first']:
                    ans[j]['first'] = t        
                if t > ans[j]['last']:
                    ans[j]['last'] = t        
    elif model in ['model3', 'model4']:
        x = v['x']
        y = v['y']
        for key,val in x.items():
            if val < 1-1e-7:
                continue
            j,t = key
            ans[j] = {'first':t}
        for key,val in y.items():
            if val < 1-1e-7:
                continue
            j,t = key
            ans[j]['last'] = t
    elif model in ['model5', 'model6']:
        z = v['z']
        for key,val in z.items():
            if val < 1-1e-7:
                continue
            j,t = key
            if j in ans:
                continue
            ans[j] = {'first':t, 'last':None}
        w = v['w']
        for key,val in w.items():
            if val < 1-1e-7:
                continue
            j,t = key
            if j in ans:
                if ans[j]['last'] is None:
                    ans[j]['last'] = t
    elif model in ['model7', 'model8']:
        z = v['z']
        for key,val in z.items():
            if val < 1-1e-7:
                continue
            j,t = key
            if j in ans:
                continue
            if t == -1:
                ans[j] = {'pre':True}
                continue
            if t == timesteps:
                ans[j] = {'post':True}
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
 
def runmip_from_datafile(*, datafile=None, data=None, index=0, model=None, tee=None, solver=None, dirname=None, debug=False, verbose=None):
    if data is None:
        assert datafile is not None
        with open(datafile, 'r') as INPUT:
            data = yaml.safe_load(INPUT)

    savefile = data['_options'].get('write', None)
    timesteps=data['_options'].get('timesteps', None)
    tee = data['_options'].get('tee', False) if tee is None else tee
    verbose = data['_options'].get('verbose', True) if verbose is None else verbose
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

    for key in observations_:
        if timesteps is None:
            timesteps = len(observations_[key])
        elif len(observations_[key]) < timesteps:
            timesteps = len(observations_[key])
            print("WARNING: limiting analysis to {} because there are only observations for that many time steps".format(timesteps))

    if model in ['model1', 'model3', 'model5', 'model7']:
        #
        # For supervised matching, we can confirm that the observations
        # have the right labels
        #
        tmp1 = set(observations_.keys())
        tmp2 = set([name for name in pm.resources])
        assert tmp1.issubset(tmp2), "For supervised process matching, we expect the observations to have labels in the process model.  The following are unknown resource labels: "+str(tmp1-tmp2)

    print("Creating model")
    if model in ['model1', 'model2', 'model3', 'model4', 'model5', 'model7', 'model8']:
        if model == 'model1':
            M = create_model1(observations=observations_,
                            pm=pm, 
                            timesteps=timesteps,
                            sigma=data['_options'].get('sigma',None),
                            verbose=verbose)
        elif model == 'model2':
            M = create_model2(observations=observations_,
                            pm=pm, 
                            timesteps=timesteps,
                            sigma=data['_options'].get('sigma',None),
                            verbose=verbose)
        elif model == 'model3':
            M = create_model3(observations=observations_,
                            pm=pm, 
                            timesteps=timesteps,
                            sigma=data['_options'].get('sigma',None), 
                            gamma=data['_options'].get('gamma',0),
                            max_delay=data['_options'].get('max_delay',0),
                            verbose=verbose)
        elif model == 'model4':
            M = create_model4(observations=observations_,
                            pm=pm, 
                            timesteps=timesteps,
                            sigma=data['_options'].get('sigma',None),
                            gamma=data['_options'].get('gamma',0),
                            max_delay=data['_options'].get('max_delay',0),
                            verbose=verbose)
        elif model == 'model5':
            M = create_model5(observations=observations_,
                            pm=pm, 
                            timesteps=timesteps,
                            sigma=data['_options'].get('sigma',None), 
                            gamma=data['_options'].get('gamma',0),
                            max_delay=data['_options'].get('max_delay',0),
                            verbose=verbose)
        elif model == 'model7':
            M = create_model78(observations=observations_,
                            supervised=True,
                            pm=pm, 
                            timesteps=timesteps,
                            sigma=data['_options'].get('sigma',None), 
                            gamma=data['_options'].get('gamma',0),
                            max_delay=data['_options'].get('max_delay',0),
                            verbose=verbose)
        elif model == 'model8':
            M = create_model78(observations=observations_,
                            supervised=False,
                            pm=pm, 
                            timesteps=timesteps,
                            sigma=data['_options'].get('sigma',None), 
                            gamma=data['_options'].get('gamma',0),
                            max_delay=data['_options'].get('max_delay',0),
                            verbose=verbose)

        if savefile:
            print("Writing file:",savefile)
            M.write(savefile, io_options=dict(symbolic_solver_labels=True))
            return dict()

        print("Optimizing model")
        opt = pe.SolverFactory(solver)
        if tee:
            print("-- Solver Output Begins --")
        results = opt.solve(M, tee=tee)
        if tee:
            print("-- Solver Output Ends --")
        if debug:           #pragma:nocover
            M.pprint()
            M.display()

        variables = variables=get_nonzero_variables(M)
        alignment = summarize_alignment(variables, model, pm, timesteps=timesteps)
        res = dict(datafile=datafile, index=index, model=model, 
                    timesteps=timesteps,
                    results=[dict(objective=pe.value(M.o), variables=variables, alignment=alignment)])

    return res

