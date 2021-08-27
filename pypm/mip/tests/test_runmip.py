import os
from os.path import dirname, join
import yaml
import pytest
import pyutilib.misc
from pypm.util import runsim
from pypm.mip import runmip_from_datafile
from pypm.util.fileutils import this_file_dir

currdir = this_file_dir()

def run(model, example, sim, supervised):
    processfile = join(dirname(dirname(currdir)), 'util', 'tests', '{}.yaml'.format(example))
    configfile =  join(dirname(dirname(currdir)), 'util', 'tests', '{}.yaml'.format(sim))
    data = runsim(processfile=processfile, configfile=configfile, model=model, supervised=supervised=='sup')
    open(join(currdir, "{}_{}_{}_{}_sim.yaml".format(example, sim, model, supervised)), 'w').write(yaml.dump(data, default_flow_style=None))
    results = runmip_from_datafile(data=data, model=model)
    output = yaml.dump(results, default_flow_style=None) 
    outputfile = join(currdir, "{}_{}_{}_{}_results.yaml".format(example, sim, model, supervised))
    with open(outputfile, "w") as OUTPUT:
        OUTPUT.write(output)
    baselinefile = join(currdir, "{}_{}_{}_{}_baseline.yaml".format(example, sim, model, supervised))
    tmp = pyutilib.misc.compare_file( outputfile, baselinefile, tolerance=1e-7)
    assert tmp[0] == False, "Files differ:  diff {} {}".format(outputfile, baselinefile)
    os.remove(outputfile)




def test_model1_example1_sim1_sup():
    run('model1', 'example1', 'sim1', 'sup')

def test_model1_example2_sim1_sup():
    run('model1', 'example2', 'sim1', 'sup')

def test_model1_example1_sim2_sup():
    run('model1', 'example1', 'sim2', 'sup')

def test_model1_example2_sim2_sup():
    run('model1', 'example2', 'sim2', 'sup')


def test_model2_example1_sim1_usup():
    run('model2', 'example1', 'sim1', 'usup')

def test_model2_example2_sim1_usup():
    run('model2', 'example2', 'sim1', 'usup')

def test_model2_example1_sim2_usup():
    run('model2', 'example1', 'sim2', 'usup')

def test_model2_example2_sim2_usup():
    run('model2', 'example2', 'sim2', 'usup')


def test_model3_example1_sim1_sup():
    run('model3', 'example1', 'sim1', 'sup')

def test_model3_example2_sim1_sup():
    run('model3', 'example2', 'sim1', 'sup')

def test_model3_example1_sim2_sup():
    run('model3', 'example1', 'sim2', 'sup')

def test_model3_example2_sim2_sup():
    run('model3', 'example2', 'sim2', 'sup')


def test_model4_example1_sim1_usup():
    run('model4', 'example1', 'sim1', 'usup')

def test_model4_example2_sim1_usup():
    run('model4', 'example2', 'sim1', 'usup')

def test_model4_example1_sim2_usup():
    run('model4', 'example1', 'sim2', 'usup')

def test_model4_example2_sim2_usup():
    run('model4', 'example2', 'sim2', 'usup')

