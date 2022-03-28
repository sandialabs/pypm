import sys
import os
import os.path
import pytest
import pyutilib.misc
import importlib
from pypm.util.fileutils import this_file_dir

currdir = this_file_dir()


def run(testname):
    cwd = os.getcwd()
    newdir = os.path.abspath(os.path.join(currdir,testname))
    os.chdir(newdir)
    #
    sys.path.insert(0, newdir)
    module = importlib.import_module(testname)
    try:
        runval = module.run()
    except:                         #pragma:nocover
        runval = None
    assert runval == True, "Unexpected return value for test {}".format(testname)
    sys.path = sys.path[1:]
    #
    tmp = pyutilib.misc.compare_file('results.yaml', 'baseline.yaml')
    assert tmp[0] == False, "Files differ:  diff {} {}".format('results.yaml', 'baseline.yaml')
    os.remove('results.yaml')
    #
    if os.path.exists('baseline.lp'):
        tmp = pyutilib.misc.compare_file('results.lp', 'baseline.lp')
        assert tmp[0] == False, "Files differ:  diff {} {}".format('results.lp', 'baseline.lp')
        os.remove('results.lp')
    #
    os.chdir(cwd)


# API tests

def test_t1():
    run('t1')

