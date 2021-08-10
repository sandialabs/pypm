import os
from os.path import join
import yaml
import pytest
import pyutilib.misc
from pypm.mip import runmip_from_datafile
from pypm.util.fileutils import this_file_dir

currdir = this_file_dir()

def run(testname):
    configfile = processfile = '{}.yaml'.format(testname)
    with open(join(currdir, processfile), 'r') as INPUT:
        data = yaml.safe_load(INPUT)

    results = runmip_from_datafile(data=data, model=data['_options']['model'], dirname=currdir)
    output = yaml.dump(results, default_flow_style=None) 
    outputfile = join(currdir, "{}_results.yaml".format(testname))
    with open(outputfile, "w") as OUTPUT:
        OUTPUT.write(output)

    tmp = pyutilib.misc.compare_file( outputfile, join(currdir, "{}_baseline.yaml".format(testname)), tolerance=1e-7)
    assert tmp[0] == False
    os.remove(outputfile)




def test1():
    run('test1')

def test2():
    run('test2')

def test3():
    run('test3')

