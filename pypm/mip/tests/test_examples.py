import os
from os.path import join
import yaml
import pytest
import pyutilib.misc
from pypm.mip import runmip_from_datafile
from pypm.util.fileutils import this_file_dir

currdir = this_file_dir()

def run(testname, debug=False, verify=False):
    configfile = processfile = '{}.yaml'.format(testname)
    with open(join(currdir, processfile), 'r') as INPUT:
        data = yaml.safe_load(INPUT)
    assert testname.startswith(data['_options']['process'][:-5])

    results = runmip_from_datafile(data=data, model=data['_options']['model'], dirname=currdir, debug=debug, tee=debug)
    output = yaml.dump(results, default_flow_style=None) 
    outputfile = join(currdir, "{}_results.yaml".format(testname))
    with open(outputfile, "w") as OUTPUT:
        OUTPUT.write(output)

    if verify:
        alignment = results['results'][0]['alignment']
        for j,val in data['data'][0]['ground_truth'].items():
            assert ((val['start'] == alignment[j]['start']) and (val['stop'] == alignment[j]['stop'])), "Differ from ground truth: {} {} {}".format(j, str(val), str(alignment[j]))
 
    baselinefile = join(currdir, "{}_baseline.yaml".format(testname))
    tmp = pyutilib.misc.compare_file(outputfile, baselinefile, tolerance=1e-7)
    assert tmp[0] == False, "Files differ:  diff {} {}".format(outputfile, baselinefile)
    os.remove(outputfile)




def test1():
    run('test1')

def test2():
    run('test2')

def test3():
    run('test3')

def test4():
    run('test4')

def test5():
    run('test5')

def test6():
    run('test6')

def test7():
    run('test7')


def test1_5():
    run('test1_5', debug=False)

def test2_5():
    run('test2_5')

def test3_5():
    run('test3_5')

def test4_5():
    run('test4_5')

def test5_5():
    run('test5_5')

def test6_5():
    run('test6_5')

def test7_5():
    run('test7_5')

