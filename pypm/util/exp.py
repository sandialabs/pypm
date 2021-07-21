# pypm.util.exp

import yaml
import os.path
from pypm.util.load import load_process
from pypm.util.sim import Simulator


def runsim(*, configfile, processfile, supervised=True):
    """
    Run simulations specified by a configuration file and process file.

    This function creates a YAML file for the simulation results.  If the 
    processfile has the name **<prefix>.yaml**, then this function creates the
    file **<prefix>_sim.yaml**.

    Args
    ----
    configfile : str
        The name of a YAML file that specifies the simulation configuration options.
    processfile : str
        The name of a YAML file that specifies the process activities.
    supervised : bool, Default: True
        If this is True, then configure the results for a supervised process matching problem.
        Otherwise, configure for unsupervised process matching with anonymized resource
        labels.
    """
    with open(configfile, 'r') as INPUT:
        yamldata=yaml.safe_load(INPUT)
    prefix = processfile[:-5]
    observe_activities = bool(yamldata.get('observe_activities',False))
    ntrials = int(yamldata.get('ntrials',1))
    timesteps = int(yamldata.get('timesteps',0))
    sigma = int(yamldata.get('sigma',0))
    seeds = yamldata.get('seeds',[])
    assert timesteps > 0, "Configuration file must specify 'timesteps' greater than zero"
    assert len(seeds) >= ntrials, "Configuration does not specify {} seeds".format(ntrials)

    model = 'model1' if supervised else 'model2'
    trials = []
    pm = load_process(processfile)
    for i in range(ntrials):
        data = []
        ground_truth = {}
        sim = Simulator(pm=pm, data=data, ground_truth=ground_truth, observe_activities=observe_activities)
        sim.run(seeds[i])
        
        observations = sim.organize_observations(data, timesteps)
        if not supervised:
            observations = {'u{}'.format(i):observations[key] for i, key in enumerate(sorted(observations.keys()))}

        trials.append( dict(    trial=i, 
                                seed=seeds[i], 
                                observations=observations,
                                ground_truth=ground_truth) )

    contents = dict( _options=dict(comments=yamldata.get('comments',[]),
                                    timesteps=timesteps,
                                    config=configfile,
                                    process=processfile,
                                    solver='glpk',
                                    model=model,
                                    tee=False),
                      data=trials)
    if sigma > 0:
        contents['_options']['sigma'] = sigma
    with open(prefix+"_sim.yaml", 'w') as OUTPUT:
        print("Writing file: {}_sim.yaml".format(prefix))
        OUTPUT.write(yaml.dump(contents, default_flow_style=None))

