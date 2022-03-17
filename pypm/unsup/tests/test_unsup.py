import os
from os.path import join
import yaml
import pytest
import pyutilib.misc
from pypm.mip.runmip import load_config
from pypm.unsup.ts_labeling import run_tabu
from pypm.util.fileutils import this_file_dir

currdir = this_file_dir()

def run(testname, debug=False, verify=False):
    configfile = processfile = '{}.yaml'.format(testname)
    with open(join(currdir, processfile), 'r') as INPUT:
        data = yaml.safe_load(INPUT)
    assert testname.startswith(data['_options']['process'][:-5])

    config = load_config(data=data, dirname=currdir, debug=debug, tee=debug, model='tabu')

    results = run_tabu(config)
    #results = runmip_from_datafile(data=data, model=data['_options']['model'], dirname=currdir, debug=debug, tee=debug)
    output = yaml.dump(results, default_flow_style=None) 
    outputfile = join(currdir, "{}_results.yaml".format(testname))
    with open(outputfile, "w") as OUTPUT:
        OUTPUT.write(output)

    #if verify:
    #    alignment = results['results'][0]['alignment']
    #    for j,val in data['data'][0]['ground_truth'].items():
    #        assert ((val['start'] == alignment[j]['start']) and (val['stop'] == alignment[j]['stop'])), "Differ from ground truth: {} {} {}".format(j, str(val), str(alignment[j]))
 
    baselinefile = join(currdir, "{}_baseline.yaml".format(testname))
    tmp = pyutilib.misc.compare_file(outputfile, baselinefile, tolerance=1e-7)
    assert tmp[0] == False, "Files differ:  diff {} {}".format(outputfile, baselinefile)
    os.remove(outputfile)



def test1_12():
    run('test1_12')

def test2_12():
    run('test2_12')

def test3_12():
    run('test3_12')

def test4_12():
    run('test4_12')

def test5_12():
    run('test5_12')

def test6_12():
    run('test6_12')

def test7_12():
    run('test7_12')

def test100_12():
    run('test100_12')

def test101_12():
    run('test101_12')

def test102_12():
    run('test102_12')

def test103_12():
    run('test103_12')

def test104_12():
    run('test104_12')

def test105_12():
    run('test105_12')

def test106_12():
    run('test106_12')

def test107_12():
    run('test107_12')

def test300_12():
    run('test300_12')

def test301_12():
    run('test301_12')

