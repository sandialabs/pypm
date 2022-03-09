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
    run('test1_5')

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


def test1_7():
    run('test1_7')

def test2_7():
    run('test2_7')

def test3_7():
    run('test3_7')

def test4_7():
    run('test4_7')

def test5_7():
    run('test5_7')

def test6_7():
    run('test6_7')


def test1_8():
    run('test1_8')

def test2_8():
    run('test2_8')

def test3_8():
    run('test3_8')

def test4_8():
    run('test4_8')

def test5_8():
    run('test5_8')

def test6_8():
    run('test6_8')

def test7_8():
    run('test7_8')


def test1_11():
    run('test1_11')

def test2_11():
    run('test2_11')

def test3_11():
    run('test3_11')

def test4_11():
    run('test4_11')

def test5_11():
    run('test5_11')

def test6_11():
    run('test6_11')

def test7_11():
    run('test7_11')

def test100_11():
    run('test100_11')

def test101_11():
    run('test101_11')

def test102_11():
    run('test102_11')

def test103_11():
    run('test103_11')

def test104_11():
    run('test104_11')

def test105_11():
    run('test105_11')

def test106_11():
    run('test106_11')

def test107_11():
    run('test107_11')


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


def test1_13():
    run('test1_13')

def test2_13():
    run('test2_13')

def test3_13():
    run('test3_13')

def test4_13():
    run('test4_13')

def test5_13():
    run('test5_13')

def test6_13():
    run('test6_13')

def test7_13():
    run('test7_13')

def test100_13():
    run('test100_13')

def test101_13():
    run('test101_13')

def test102_13():
    run('test102_13')

def test103_13():
    run('test103_13')

def test104_13():
    run('test104_13')

def test105_13():
    run('test105_13')

def test106_13():
    run('test106_13')

def test107_13():
    run('test107_13')


def test201_13():
    run('test201_13')

