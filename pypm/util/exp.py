# pypm.util.exp

import yaml
import os.path
from pypm.util.load import load_data
from pypm.util.sim import Simulator


def runsim(*, configfile, processfile):
    with open(configfile, 'r') as INPUT:
        yamldata=yaml.safe_load(INPUT)
    prefix = processfile[:-5]
    ntrials = int(yamldata.get('ntrials',1))
    timesteps = int(yamldata.get('timesteps',0))
    seeds = yamldata.get('seeds',[])
    assert timesteps > 0, "Configuration file must specify 'timesteps' greater than zero"
    assert len(seeds) >= ntrials, "Configuration does not specify {} seeds".format(ntrials)

    trials = []
    pm = load_data(processfile)
    for i in range(ntrials):
        summary = dict(comments=yamldata.get('comments',[]),
                        trial=i,
                        seed=seeds[i],
                        config=configfile,
                        process=processfile)
        data = []
        sim = Simulator(pm=pm, data=data)
        sim.run(seeds[i])
        obs = sim.organize_observations(data, timesteps)
        trials.append( dict(summary=summary, observations=obs) )

    with open(prefix+"_sim.yaml", 'w') as OUTPUT:
        print("Writing file: {}_sim.yaml".format(prefix))
        OUTPUT.write(yaml.dump(trials, default_flow_style=None))
