import os
from os.path import join
import yaml
import pytest
import pyutilib.misc
from pypm.util.fileutils import this_file_dir
from pypm.api import PYPM

currdir = this_file_dir()

def run(testname, debug=False, verify=False, nworkers=1):
    driver = PYPM.tabu_labeling()
    driver.load_config(join(currdir, '{}.yaml'.format(testname)))
    driver.config.debug=debug
    driver.config.tee=debug
    driver.config.datafile = None
    assert testname.startswith(driver.config.process[:-5])

    results = driver.generate_labeling_and_schedule(nworkers=nworkers)
    outputfile = join(currdir, "{}_results.yaml".format(testname))
    results.write(outputfile)

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


def test200_12():
    run('test200_12')

def test201_12():
    run('test201_12')

def test202_12():
    run('test202_12')


def test300_12():
    run('test300_12')

def test301_12():
    run('test301_12')


#
# WEH - This code fails for some reason, complaining that the 'pypm' package is not installed.
#
#def test407_12():
#    run('test407_12', nworkers=3)

