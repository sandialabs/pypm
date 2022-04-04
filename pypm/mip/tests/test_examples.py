import os
from os.path import join
import yaml
import pytest
import pyutilib.misc
from pypm.api import PYPM
from pypm.util.fileutils import this_file_dir

currdir = this_file_dir()

def run(testname, dirname, debug=False, verify=False):
    unsupervised = dirname in ['UPM']
    dirname = join(currdir, dirname)
    if unsupervised:
        driver = PYPM.unsupervised_mip()
    else:
        driver = PYPM.supervised_mip()

    driver.load_config(join(dirname, '{}.yaml'.format(testname)))
    driver.config.dirname = dirname
    driver.config.debug = debug
    driver.config.tee = debug
    driver.config.datafile = None                           # Ignore this for the test
    assert testname.startswith(driver.config.process[:-5])

    results = driver.generate_schedule()
    outputfile = join(dirname, "{}_results.yaml".format(testname))
    results.write(outputfile, verbose=True)

    if verify:
        alignment = results['results'][0]['alignment']
        for j,val in data['data'][0]['ground_truth'].items():
            assert ((val['start'] == alignment[j]['start']) and (val['stop'] == alignment[j]['stop'])), "Differ from ground truth: {} {} {}".format(j, str(val), str(alignment[j]))
 
    baselinefile = join(dirname, "{}_baseline.yaml".format(testname))
    tmp = pyutilib.misc.compare_file(outputfile, baselinefile, tolerance=1e-7)
    assert tmp[0] == False, "Files differ:  diff {} {}".format(outputfile, baselinefile)
    os.remove(outputfile)


def test1():
    run('test1', 'model3')

def test2():
    run('test2', 'model3')

def test3():
    run('test3', 'model3')

def test4():
    run('test4', 'model3')

def test5():
    run('test5', 'model3')

def test6():
    run('test6', 'model3')

def test7():
    run('test7', 'model3')


def test1_5():
    run('test1', 'model5')

def test2_5():
    run('test2', 'model5')

def test3_5():
    run('test3', 'model5')

def test4_5():
    run('test4', 'model5')

def test5_5():
    run('test5', 'model5')

def test6_5():
    run('test6', 'model5')

def test7_5():
    run('test7', 'model5')


def test1_7():
    run('test1', 'model7')

def test2_7():
    run('test2', 'model7')

def test3_7():
    run('test3', 'model7')

def test4_7():
    run('test4', 'model7')

def test5_7():
    run('test5', 'model7')

def test6_7():
    run('test6', 'model7')


def test1_8():
    run('test1', 'model8')

def test2_8():
    run('test2', 'model8')

def test3_8():
    run('test3', 'model8')

def test4_8():
    run('test4', 'model8')

def test5_8():
    run('test5', 'model8')

def test6_8():
    run('test6', 'model8')

def test7_8():
    run('test7', 'model8')


def test1_11():
    run('test1', 'model11')

def test2_11():
    run('test2', 'model11')

def test3_11():
    run('test3', 'model11')

def test4_11():
    run('test4', 'model11')

def test5_11():
    run('test5', 'model11')

def test6_11():
    run('test6', 'model11')

def test7_11():
    run('test7', 'model11')

def test100_11():
    run('test100', 'model11')

def test101_11():
    run('test101', 'model11')

def test102_11():
    run('test102', 'model11')

def test103_11():
    run('test103', 'model11')

def test104_11():
    run('test104', 'model11')

def test105_11():
    run('test105', 'model11')

def test106_11():
    run('test106', 'model11')

def test107_11():
    run('test107', 'model11')

def test108_11():
    run('test108', 'model11')


def test1_12():
    run('test1', 'model12')

def test2_12():
    run('test2', 'model12')

def test3_12():
    run('test3', 'model12')

def test4_12():
    run('test4', 'model12')

def test5_12():
    run('test5', 'model12')

def test6_12():
    run('test6', 'model12')

def test7_12():
    run('test7', 'model12')

def test100_12():
    run('test100', 'model12')

def test101_12():
    run('test101', 'model12')

def test102_12():
    run('test102', 'model12')

def test103_12():
    run('test103', 'model12')

def test104_12():
    run('test104', 'model12')

def test105_12():
    run('test105', 'model12')

def test106_12():
    run('test106', 'model12')

def test107_12():
    run('test107', 'model12')


def test1_13():
    run('test1', 'model13')

def test2_13():
    run('test2', 'model13')

def test3_13():
    run('test3', 'model13')

def test4_13():
    run('test4', 'model13')

def test5_13():
    run('test5', 'model13')

def test6_13():
    run('test6', 'model13')

def test7_13():
    run('test7', 'model13')

def test100_13():
    run('test100', 'model13')

def test101_13():
    run('test101', 'model13')

def test102_13():
    run('test102', 'model13')

def test103_13():
    run('test103', 'model13')

def test104_13():
    run('test104', 'model13')

def test105_13():
    run('test105', 'model13')

def test106_13():
    run('test106', 'model13')

def test107_13():
    run('test107', 'model13')


def test201_13():
    run('test201', 'model13')


def test1_UPM():
    run('test1', 'UPM')

def test2_UPM():
    run('test2', 'UPM')

def test3_UPM():
    run('test3', 'UPM')

def test4_UPM():
    run('test4', 'UPM')

def test5_UPM():
    run('test5', 'UPM')

def test6_UPM():
    run('test6', 'UPM')

def test7_UPM():
    run('test7', 'UPM')

def test100_UPM():
    run('test100', 'UPM')

def test101_UPM():
    run('test101', 'UPM')

def test102_UPM():
    run('test102', 'UPM')

def test103_UPM():
    run('test103', 'UPM')

def test104_UPM():
    run('test104', 'UPM')

def test105_UPM():
    run('test105', 'UPM')

def test106_UPM():
    run('test106', 'UPM')

def test107_UPM():
    run('test107', 'UPM')


