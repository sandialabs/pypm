# pymp.mip.runmip


import yaml
import pprint
import csv
import sys
from munch import Munch
import pandas as pd
from os.path import join
import os.path
from pypm.util.load import load_process
from pypm.mip.models import create_model1, create_model2, create_model3, create_model4, create_model5, create_model78, create_model10, create_model11_12, create_model13_14
from pypm.mip.newmodels import create_model
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
    elif model in ['model7', 'model8', 'model10', 'model11', 'model12', 'model13', 'model14']:
        ans = {j:{'post':True} for j in pm}
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


def new_perform_optimization(*, M, solver, options, tee, debug):
    opt = pe.SolverFactory(solver)
    if tee:
        print("-- Solver Output Begins --")
    if options:
        results = opt.solve(M.M, options=options, tee=tee)
    else:
        results = opt.solve(M.M, tee=tee)
    if tee:
        print("-- Solver Output Ends --")
    if results.solver.termination_condition not in {tc.optimal, tc.locallyOptimal, tc.feasible}:
        return None
    if debug:           #pragma:nocover
        M.M.pprint()
        M.M.display()
    return M.summarize()


def fracval(num,denom):
    if denom != 0:
        return num/denom
    return 0


def summarize(*, model, M, pm, obs):
    #
    # Summarize optimization results
    #
    variables = variables=get_nonzero_variables(M)
    alignment = summarize_alignment(variables, model, pm, timesteps=obs.timesteps)
    results=dict(objective=pe.value(M.objective), variables=variables, schedule=alignment, goals=dict())
    #
    if not obs.datetime is None:
        datetime_alignment = {key:{} for key in alignment}
        lastv = max(v for v in obs.datetime)
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
    #
    if hasattr(M, 'activity_length'):
        results['goals']['separation'] = {}
        for i in M.activity_length:
            if alignment[i].get('pre',False) or alignment[i].get('post',False):
                results['goals']['separation'][i] = 0
            else:
                activity = fracval(pe.value(M.weighted_activity_length[i]),pe.value(M.activity_length[i]))
                nonactivity = fracval(pe.value(M.weighted_nonactivity_length[i]),pe.value(M.nonactivity_length[i]))
                results['goals']['separation'][i] = max(0, activity - nonactivity)
        results['goals']['total_separation'] = sum(val for val in results['goals']['separation'].values())
    #
    if 'o' in variables:
        results['goals']['match'] = {}
        for activity, value in variables['o'].items():
            results['goals']['match'][activity] = value
        results['goals']['total_match'] = sum(val for val in results['goals']['match'].values())
    #
    return results


def runmip_from_datafile(*, datafile=None, data=None, index=0, model=None, tee=None, solver=None, dirname=None, debug=False, verbose=None):
    configdata = load_config(datafile=datafile, data=data, index=index, tee=tee, model=model, solver=solver, dirname=dirname, debug=debug, verbose=verbose)
    return runmip(configdata)


def load_config(*, datafile=None, data=None, index=0, model=None, tee=None, solver=None, dirname=None, debug=False,          verbose=None, seed=123456789237498):
    if data is None:
        assert datafile is not None
        with open(datafile, 'r') as INPUT:
            data = yaml.safe_load(INPUT)

    options = data['_options']
    savefile = options.get('write', None)
    tee = options.get('tee', False) if tee is None else tee
    seed = options.get('seed', False) if seed is None else seed
    verbose = options.get('verbose', True) if verbose is None else verbose
    model = options.get('model', None) if model is None else model
    solver = options.get('solver', 'glpk') if solver is None else solver
    solver_options = options.get('solver_options', {})
    if dirname is None and datafile is not None:
        dirname = os.path.dirname(os.path.abspath(datafile))
    pm = load_process(options['process'], dirname=dirname)
    search_strategy = options.get('search_strategy', 'mip')

    obs = load_observations(data['data'], 
                            options.get('timesteps', None),
                            dirname,
                            index)

    if model in ['model1', 'model3', 'model5', 'model7', 'model11', 'model13']:
        #
        # For supervised matching, we can confirm that the observations
        # have the right labels
        #
        tmp1 = set(obs.observations.keys())
        tmp2 = set([name for name in pm.resources])
        assert tmp1.issubset(tmp2), "For supervised process matching, we expect the observations to have labels in the process model.  The following are unknown resource labels: "+str(tmp1-tmp2)

    return Munch(savefile=savefile, tee=tee, verbose=verbose, model=model, solver=solver, solver_options=solver_options,
                    pm=pm, search_strategy=search_strategy, obs=obs,
                    options=options, datafile=datafile, index=index, debug=debug, seed=seed, process=options['process'])


def runmip(config, constraints=[]):
    print("Creating model")
    M = create_model(config.model)
    if M is None:
        return old_runmip(config)
    
    M(config, constraints=constraints)

    if config.savefile:
        print("Writing file:",config.savefile)
        M.M.write(config.savefile, io_options=dict(symbolic_solver_labels=True))
        #M.pprint()
        #M.display()
        return dict()

    #
    # Setup results YAML data
    #
    res = dict( solver=dict(search_strategy=config.search_strategy, model=dict(name=config.model)), 
                data=dict(  datafile=config.datafile,
                            timesteps=config.obs.timesteps,
                            indicators=config.obs.header,
                            index=config.index),
                results=[])
    res['data']['datetime'] = config.obs.datetime

    if config.search_strategy == 'mip':
        #
        # Perform optimization
        #
        print("Optimizing model")
        results = new_perform_optimization(M=M, solver=config.solver, options=config.solver_options, tee=config.tee, debug=config.debug)

        #
        # Append results to YAML data
        #
        res['results'].append( results )

    return res


def old_runmip(config):
    if config.model in ['model1', 'model2', 'model3', 'model4', 'model5', 'model7', 'model8', 'model10', 'model11', 'model12', 'model13', 'model14']:
        if config.model == 'model1':
            M = create_model1(observations=config.obs.observations,
                            pm=config.pm, 
                            timesteps=config.obs.timesteps,
                            sigma=config.options.get('sigma',None),
                            verbose=config.verbose)
        elif config.model == 'model2':
            M = create_model2(observations=config.obs.observations,
                            pm=config.pm, 
                            timesteps=config.obs.timesteps,
                            sigma=config.options.get('sigma',None),
                            verbose=config.verbose)
        elif config.model == 'model3':
            M = create_model3(observations=config.obs.observations,
                            pm=config.pm, 
                            timesteps=config.obs.timesteps,
                            sigma=config.options.get('sigma',None), 
                            gamma=config.options.get('gamma',0),
                            max_delay=config.options.get('max_delay',0),
                            verbose=config.verbose)
        elif config.model == 'model4':
            M = create_model4(observations=config.obs.observations,
                            pm=config.pm, 
                            timesteps=config.obs.timesteps,
                            sigma=config.options.get('sigma',None),
                            gamma=config.options.get('gamma',0),
                            max_delay=config.options.get('max_delay',0),
                            verbose=config.verbose)
        elif config.model == 'model5':
            M = create_model5(observations=config.obs.observations,
                            pm=config.pm, 
                            timesteps=config.obs.timesteps,
                            sigma=config.options.get('sigma',None), 
                            gamma=config.options.get('gamma',0),
                            max_delay=config.options.get('max_delay',0),
                            verbose=config.verbose)
        elif config.model == 'model7':
            M = create_model78(observations=config.obs.observations,
                            supervised=True,
                            pm=config.pm, 
                            timesteps=config.obs.timesteps,
                            sigma=config.options.get('sigma',None), 
                            gamma=config.options.get('gamma',0),
                            max_delay=config.options.get('max_delay',0),
                            verbose=config.verbose)
        elif config.model == 'model8':
            M = create_model78(observations=config.obs.observations,
                            supervised=False,
                            pm=config.pm, 
                            timesteps=config.obs.timesteps,
                            sigma=config.options.get('sigma',None), 
                            gamma=config.options.get('gamma',0),
                            max_delay=config.options.get('max_delay',0),
                            verbose=config.verbose)
        elif config.model == 'model10':
            M = create_model10(observations=config.obs.observations,
                            supervised=False,
                            pm=config.pm, 
                            timesteps=config.obs.timesteps,
                            sigma=config.options.get('sigma',None), 
                            gamma=config.options.get('gamma',0),
                            max_delay=config.options.get('max_delay',0),
                            verbose=config.verbose)
        elif config.model == 'model11':
            assert 'max_delay' not in config.options
            M = create_model11_12(observations=config.obs.observations,
                            supervised=True,
                            pm=config.pm, 
                            timesteps=config.obs.timesteps,
                            sigma=config.options.get('sigma',None), 
                            gamma=config.options.get('gamma',0),
                            verbose=config.verbose)
        elif config.model == 'model12':
            assert 'max_delay' not in config.options
            M = create_model11_12(observations=config.obs.observations,
                            supervised=False,
                            pm=config.pm, 
                            timesteps=config.obs.timesteps,
                            sigma=config.options.get('sigma',None), 
                            gamma=config.options.get('gamma',0),
                            verbose=config.verbose)
        elif config.model == 'model13':
            assert 'max_delay' not in config.options
            M = create_model13_14(observations=config.obs.observations,
                            supervised=True,
                            pm=config.pm, 
                            timesteps=config.obs.timesteps,
                            sigma=config.options.get('sigma',None), 
                            gamma=config.options.get('gamma',0),
                            count_data=set(config.options.get('count_data',[])),
                            verbose=config.verbose)
        else:
            M = create_model(config.model)
            M(config, constraints=constraints)
            config.search_strategy = 'newmip'

        if config.savefile:
            print("Writing file:",config.savefile)
            M.write(config.savefile, io_options=dict(symbolic_solver_labels=True))
            return dict()

            M.pprint()
            M.display()

        #
        # Setup results YAML data
        #
        res = dict( solver=dict(search_strategy=config.search_strategy, model=dict(name=config.model)), 
                    data=dict(  datafile=config.datafile,
                                timesteps=config.obs.timesteps,
                                indicators=config.obs.header,
                                index=config.index),
                    results=[])
        res['data']['datetime'] = config.obs.datetime

        if config.search_strategy == 'mip':
            #
            # Perform optimization
            #
            print("Optimizing model")
            results = perform_optimization(M=M, model=config.model, solver=config.solver, options=config.solver_options, tee=config.tee, debug=config.debug, obs=config.obs, pm=config.pm)

            #
            # Append results to YAML data
            #
            res['results'].append( results )

        elif config.search_strategy == 'enum_labelling':
            M.cuts = pe.ConstraintList()
            i = 0
            maxiters = 10
            flag = True
            while flag: 
                #
                # Perform optimization
                #
                print("Optimizing model")
                results = perform_optimization(M=M, model=config.model, solver=config.solver, options=config.solver_options, tee=config.tee, debug=config.debug, obs=obs, pm=pm)
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

