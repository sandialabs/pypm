import os
from os.path import join
import yaml
import pytest
import pyutilib.misc
from pypm.util.fileutils import this_file_dir
from pypm.api import PYPM

currdir = this_file_dir()

def run(testname, debug=False, verify=False):
    driver = PYPM.supervised_mip()

    driver.load_config(join(currdir, 'model3', '{}_config.yaml'.format(testname)))
    driver.config.dirname = join(currdir,'model3')
    driver.config.debug = debug
    driver.config.tee = debug
    driver.config.datafile = None                           # Ignore this for the test

    results = driver.run()
    outputfile = join(currdir, "model3/{}_results.yaml".format(testname))
    results.write(outputfile, verbose=True)

    if verify:
        alignment = results['results'][0]['alignment']
        for j,val in data['data'][0]['ground_truth'].items():
            assert ((val['start'] == alignment[j]['start']) and (val['stop'] == alignment[j]['stop'])), "Differ from ground truth: {} {} {}".format(j, str(val), str(alignment[j]))
 
    baselinefile = join(currdir, "model3", "{}_baseline.yaml".format(testname))
    tmp = pyutilib.misc.compare_file(outputfile, baselinefile, tolerance=1e-7)
    assert tmp[0] == False, "Files differ:  diff {} {}".format(outputfile, baselinefile)
    os.remove(outputfile)


def test1():
    run('run1')

def test2():
    run('run2')

