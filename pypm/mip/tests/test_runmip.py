import os
from os.path import dirname, join
import yaml
import pytest
import pyutilib.misc
from pypm.util import runsim
from pypm.mip import runmip_from_datafile
from pypm.util.fileutils import this_file_dir

currdir = this_file_dir()

#
# Supervised
#

def test_ex1_s1_sup():
    """
    example1 with sim1
    """
    processfile = join(dirname(dirname(currdir)), 'util', 'tests', 'example1.yaml')
    configfile =  join(dirname(dirname(currdir)), 'util', 'tests', 'sim1.yaml')
    data = runsim(processfile=processfile, configfile=configfile, supervised=True)
    open(join(currdir, "ex1_s1_sup_sim.yaml"), 'w').write(yaml.dump(data, default_flow_style=None))
    results = runmip_from_datafile(data=data)
    output = yaml.dump(results, default_flow_style=None) 
    outputfile = join(currdir, "ex1_s1_sup_results.yaml")
    with open(outputfile, "w") as OUTPUT:
        OUTPUT.write(output)
    assert pyutilib.misc.compare_file( outputfile, join(currdir, "ex1_s1_sup_baseline.yaml") )[0] == False
    os.remove(outputfile)

def test_ex2_s1_sup():
    """
    example2 with sim1
    """
    processfile = join(dirname(dirname(currdir)), 'util', 'tests', 'example2.yaml')
    configfile =  join(dirname(dirname(currdir)), 'util', 'tests', 'sim1.yaml')
    data = runsim(processfile=processfile, configfile=configfile, supervised=True)
    open(join(currdir, "ex2_s1_sup_sim.yaml"), 'w').write(yaml.dump(data, default_flow_style=None))
    results = runmip_from_datafile(data=data)
    output = yaml.dump(results, default_flow_style=None) 
    outputfile = join(currdir, "ex2_s1_sup_results.yaml")
    with open(outputfile, "w") as OUTPUT:
        OUTPUT.write(output)
    assert pyutilib.misc.compare_file( outputfile, join(currdir, "ex2_s1_sup_baseline.yaml") )[0] == False
    os.remove(outputfile)

def test_ex1_s2_sup():
    """
    example1 with sim2
    """
    processfile = join(dirname(dirname(currdir)), 'util', 'tests', 'example1.yaml')
    configfile =  join(dirname(dirname(currdir)), 'util', 'tests', 'sim2.yaml')
    data = runsim(processfile=processfile, configfile=configfile, supervised=True)
    open(join(currdir, "ex1_s2_sup_sim.yaml"), 'w').write(yaml.dump(data, default_flow_style=None))
    results = runmip_from_datafile(data=data)
    output = yaml.dump(results, default_flow_style=None) 
    outputfile = join(currdir, "ex1_s2_sup_results.yaml")
    with open(outputfile, "w") as OUTPUT:
        OUTPUT.write(output)
    assert pyutilib.misc.compare_file( outputfile, join(currdir, "ex1_s2_sup_baseline.yaml") )[0] == False
    os.remove(outputfile)

def test_ex2_s2_sup():
    """
    example2 with sim2
    """
    processfile = join(dirname(dirname(currdir)), 'util', 'tests', 'example2.yaml')
    configfile =  join(dirname(dirname(currdir)), 'util', 'tests', 'sim2.yaml')
    data = runsim(processfile=processfile, configfile=configfile, supervised=True)
    open(join(currdir, "ex2_s2_sup_sim.yaml"), 'w').write(yaml.dump(data, default_flow_style=None))
    results = runmip_from_datafile(data=data)
    output = yaml.dump(results, default_flow_style=None) 
    outputfile = join(currdir, "ex2_s2_sup_results.yaml")
    with open(outputfile, "w") as OUTPUT:
        OUTPUT.write(output)
    assert pyutilib.misc.compare_file( outputfile, join(currdir, "ex2_s2_sup_baseline.yaml") )[0] == False
    os.remove(outputfile)

#
# Unsupervised
#

def test_ex1_s1_usup():
    """
    example1 with sim1
    """
    processfile = join(dirname(dirname(currdir)), 'util', 'tests', 'example1.yaml')
    configfile =  join(dirname(dirname(currdir)), 'util', 'tests', 'sim1.yaml')
    data = runsim(processfile=processfile, configfile=configfile, supervised=False)
    open(join(currdir, "ex1_s1_usup_sim.yaml"), 'w').write(yaml.dump(data, default_flow_style=None))
    results = runmip_from_datafile(data=data)
    output = yaml.dump(results, default_flow_style=None) 
    outputfile = join(currdir, "ex1_s1_usup_results.yaml")
    with open(outputfile, "w") as OUTPUT:
        OUTPUT.write(output)
    assert pyutilib.misc.compare_file( outputfile, join(currdir, "ex1_s1_usup_baseline.yaml") )[0] == False
    os.remove(outputfile)

def test_ex2_s1_usup():
    """
    example2 with sim1
    """
    processfile = join(dirname(dirname(currdir)), 'util', 'tests', 'example2.yaml')
    configfile =  join(dirname(dirname(currdir)), 'util', 'tests', 'sim1.yaml')
    data = runsim(processfile=processfile, configfile=configfile, supervised=False)
    open(join(currdir, "ex2_s1_usup_sim.yaml"), 'w').write(yaml.dump(data, default_flow_style=None))
    results = runmip_from_datafile(data=data)
    output = yaml.dump(results, default_flow_style=None) 
    outputfile = join(currdir, "ex2_s1_usup_results.yaml")
    with open(outputfile, "w") as OUTPUT:
        OUTPUT.write(output)
    assert pyutilib.misc.compare_file( outputfile, join(currdir, "ex2_s1_usup_baseline.yaml") )[0] == False
    os.remove(outputfile)

def test_ex1_s2_usup():
    """
    example1 with sim2
    """
    processfile = join(dirname(dirname(currdir)), 'util', 'tests', 'example1.yaml')
    configfile =  join(dirname(dirname(currdir)), 'util', 'tests', 'sim2.yaml')
    data = runsim(processfile=processfile, configfile=configfile, supervised=False)
    open(join(currdir, "ex1_s2_usup_sim.yaml"), 'w').write(yaml.dump(data, default_flow_style=None))
    results = runmip_from_datafile(data=data)
    output = yaml.dump(results, default_flow_style=None) 
    outputfile = join(currdir, "ex1_s2_usup_results.yaml")
    with open(outputfile, "w") as OUTPUT:
        OUTPUT.write(output)
    assert pyutilib.misc.compare_file( outputfile, join(currdir, "ex1_s2_usup_baseline.yaml") )[0] == False
    os.remove(outputfile)

def test_ex2_s2_usup():
    """
    example2 with sim2
    """
    processfile = join(dirname(dirname(currdir)), 'util', 'tests', 'example2.yaml')
    configfile =  join(dirname(dirname(currdir)), 'util', 'tests', 'sim2.yaml')
    data = runsim(processfile=processfile, configfile=configfile, supervised=False)
    open(join(currdir, "ex2_s2_usup_sim.yaml"), 'w').write(yaml.dump(data, default_flow_style=None))
    results = runmip_from_datafile(data=data)
    output = yaml.dump(results, default_flow_style=None) 
    outputfile = join(currdir, "ex2_s2_usup_results.yaml")
    with open(outputfile, "w") as OUTPUT:
        OUTPUT.write(output)
    assert pyutilib.misc.compare_file( outputfile, join(currdir, "ex2_s2_usup_baseline.yaml") )[0] == False
    os.remove(outputfile)
