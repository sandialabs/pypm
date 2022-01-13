# pymp.mip.runmip

import yaml
import pprint
import csv
import sys
from munch import Munch
import pandas as pd
from os.path import join
from pypm.util.load import load_process
from pypm.mip.models import create_model1, create_model2, create_model3, create_model4, create_model5, create_model78
import pyomo.environ as pe
from pyomo.opt import TerminationCondition as tc


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
 

def load_observations(data, timesteps, dirname, index, strict=False):
    observations_ = {}
    header = []
    if type(data) is list:
        datetime=None
        observations = data[index]['observations']
        if type(observations) is list:
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
    else:
        fname = data['filename']
        if not dirname is None:
            fname = join(dirname, fname)
        index = data.get('index','DateTime')
        if fname.endswith(".csv"):
            df = pd.read_csv(fname)
            observations_ = df.to_dict(orient='list')
            header = list(df.columns)
        else:
            raise "Unknown file format"
        datetime = observations_.get(index,None)
        if not datetime is None:
            del observations_[index]
            header.remove(index)
            datetime = dict(zip(range(len(datetime)), datetime))
        
    #
    # Check that dates are strictly increasing
    #
    if not datetime is None:
        prev = datetime[0]
        for i in range(1,len(datetime)):
            assert prev < datetime[i], "Expecting date-time values to be strictly increasing.  The date {} appears before {} in the data set.".format(prev, datetime[i])
            prev = datetime[i]
    #
    # Check that observations are in the interval [0,1]
    #
    for key in observations_:
        for row in range(len(observations_[key])):
            val = observations_[key][row]
            #print(key,row,val)
            if val < 0 or val > 1:
                if strict:
                    print("ERROR: invalid observation value {} (col={}, row={}). Must be in the interval [0,1].".format(val, key, row))
                    sys.exit(1)
                else:
                    if val < 0:
                        print("WARNING: invalid observation value {} (col={}, row={}). Moving value to 0.".format(val, key, row))
                        observations_[key][row] = 0
                    if val > 1:
                        print("WARNING: invalid observation value {} (col={}, row={}). Moving value to 1.".format(val, key, row))
                        observations_[key][row] = 1
    #
    # Get the value of 'timesteps'
    #
    for key in observations_:
        if timesteps is None:
            timesteps = len(observations_[key])
        elif len(observations_[key]) < timesteps:
            timesteps = len(observations_[key])
            print("WARNING: limiting analysis to {} because there are only observations for that many time steps".format(timesteps))

    return Munch(observations=observations_, header=header, timesteps=timesteps, datetime=datetime)


def perform_optimization(*, M, model, solver, options, tee, debug, obs, pm):
    opt = pe.SolverFactory(solver)
    if tee:
        print("-- Solver Output Begins --")
    if options:
        results = opt.solve(M, options=options, tee=tee)
    else:
        results = opt.solve(M, tee=tee)
    if tee:
        print("-- Solver Output Ends --")
    if results.solver.termination_condition not in {tc.optimal, tc.locallyOptimal, tc.feasible}:
        return None
    if debug:           #pragma:nocover
        M.pprint()
        M.display()
    return summarize(model=model, M=M, obs=obs, pm=pm)


def summarize(*, model, M, pm, obs):
    #
    # Summarize optimization results
    #
    variables = variables=get_nonzero_variables(M)
    alignment = summarize_alignment(variables, model, pm, timesteps=obs.timesteps)
    results=dict(objective=pe.value(M.objective), variables=variables, alignment=alignment)
    if not obs.datetime is None:
        datetime_alignment = {key:{} for key in alignment}
        for key,value in alignment.items():
            for k,v in value.items():
                datetime_alignment[key][k] = obs.datetime[v]
            if 'last' in datetime_alignment[key] and v+1 in obs.datetime:
                datetime_alignment[key]['stop'] = obs.datetime[v+1]
        results['datetime_alignment'] = datetime_alignment
    return results


def runmip_from_datafile(*, datafile=None, data=None, index=0, model=None, tee=None, solver=None, dirname=None, debug=False, verbose=None):
    if data is None:
        assert datafile is not None
        with open(datafile, 'r') as INPUT:
            data = yaml.safe_load(INPUT)

    savefile = data['_options'].get('write', None)
    tee = data['_options'].get('tee', False) if tee is None else tee
    verbose = data['_options'].get('verbose', True) if verbose is None else verbose
    model = data['_options'].get('model', 'model3') if model is None else model
    solver = data['_options'].get('solver', 'glpk') if solver is None else solver
    solver_options = data['_options'].get('solver_options', {})
    pm = load_process(data['_options']['process'], dirname=dirname)
    solver_strategy = data['_options'].get('solver_strategy', 'simple')

    obs = load_observations(data['data'], 
                            data['_options'].get('timesteps', None),
                            dirname,
                            index)

    if model in ['model1', 'model3', 'model5', 'model7']:
        #
        # For supervised matching, we can confirm that the observations
        # have the right labels
        #
        tmp1 = set(obs.observations.keys())
        tmp2 = set([name for name in pm.resources])
        assert tmp1.issubset(tmp2), "For supervised process matching, we expect the observations to have labels in the process model.  The following are unknown resource labels: "+str(tmp1-tmp2)

    print("Creating model")
    if model in ['model1', 'model2', 'model3', 'model4', 'model5', 'model7', 'model8']:
        if model == 'model1':
            M = create_model1(observations=obs.observations,
                            pm=pm, 
                            timesteps=obs.timesteps,
                            sigma=data['_options'].get('sigma',None),
                            verbose=verbose)
        elif model == 'model2':
            M = create_model2(observations=obs.observations,
                            pm=pm, 
                            timesteps=obs.timesteps,
                            sigma=data['_options'].get('sigma',None),
                            verbose=verbose)
        elif model == 'model3':
            M = create_model3(observations=obs.observations,
                            pm=pm, 
                            timesteps=obs.timesteps,
                            sigma=data['_options'].get('sigma',None), 
                            gamma=data['_options'].get('gamma',0),
                            max_delay=data['_options'].get('max_delay',0),
                            verbose=verbose)
        elif model == 'model4':
            M = create_model4(observations=obs.observations,
                            pm=pm, 
                            timesteps=obs.timesteps,
                            sigma=data['_options'].get('sigma',None),
                            gamma=data['_options'].get('gamma',0),
                            max_delay=data['_options'].get('max_delay',0),
                            verbose=verbose)
        elif model == 'model5':
            M = create_model5(observations=obs.observations,
                            pm=pm, 
                            timesteps=obs.timesteps,
                            sigma=data['_options'].get('sigma',None), 
                            gamma=data['_options'].get('gamma',0),
                            max_delay=data['_options'].get('max_delay',0),
                            verbose=verbose)
        elif model == 'model7':
            M = create_model78(observations=obs.observations,
                            supervised=True,
                            pm=pm, 
                            timesteps=obs.timesteps,
                            sigma=data['_options'].get('sigma',None), 
                            gamma=data['_options'].get('gamma',0),
                            max_delay=data['_options'].get('max_delay',0),
                            verbose=verbose)
        elif model == 'model8':
            M = create_model78(observations=obs.observations,
                            supervised=False,
                            pm=pm, 
                            timesteps=obs.timesteps,
                            sigma=data['_options'].get('sigma',None), 
                            gamma=data['_options'].get('gamma',0),
                            max_delay=data['_options'].get('max_delay',0),
                            verbose=verbose)

        if savefile:
            print("Writing file:",savefile)
            M.write(savefile, io_options=dict(symbolic_solver_labels=True))
            return dict()

            M.pprint()
            M.display()

        #
        # Setup results YAML data
        #
        res = dict( datafile=datafile,
                    index=index,
                    model=model, 
                    indicators=obs.header,
                    timesteps=obs.timesteps,
                    results=[])
        if not obs.datetime is None:
            res['datetime'] = obs.datetime

        if solver_strategy == 'simple':
            #
            # Perform optimization
            #
            print("Optimizing model")
            results = perform_optimization(M=M, model=model, solver=solver, options=solver_options, tee=tee, debug=debug, obs=obs, pm=pm)

            #
            # Append results to YAML data
            #
            res['results'].append( results )

        elif solver_strategy == 'enum_labelling':
            M.cuts = pe.ConstraintList()
            i = 0
            maxiters = 10
            flag = True
            while flag: 
                #
                # Perform optimization
                #
                print("Optimizing model")
                results = perform_optimization(M=M, model=model, solver=solver, options=solver_options, tee=tee, debug=debug, obs=obs, pm=pm)
                #
                # Break if infeasible
                #
                if results is None:
                    break
                #
                # Add more cuts
                #
                expr = 0
                for v in M.m.values():
                    if pe.value(v) < 0.5:
                        expr += v
                    else:
                        expr += (1-v)
                M.cuts.add( expr >= 1 )
                #
                # Append results to YAML data
                #
                res['results'].append( results )

                i = i+1
                if i == maxiters:
                    break

    return res

