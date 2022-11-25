import sys
import os
import os.path
import pytest
import pyutilib.misc
import importlib
from pypm.util.fileutils import this_file_dir

currdir = this_file_dir()


def run(testname, retval=True):
    cwd = os.getcwd()
    newdir = os.path.abspath(os.path.join(currdir, testname))
    os.chdir(newdir)
    #
    sys.path.insert(0, newdir)
    module = importlib.import_module(testname)
    try:
        runval = module.run()
    except:  # pragma:nocover
        runval = None
    assert runval == retval, "Unexpected return value for test {}".format(testname)
    sys.path = sys.path[1:]
    #
    if retval:
        tmp = pyutilib.misc.compare_file("results.yaml", "baseline.yaml")
        assert tmp[0] == False, "Files differ:  diff {} {}".format(
            "results.yaml", "baseline.yaml"
        )
        os.remove("results.yaml")
    #
    # If the test writes an LP file, then compare it against a baseline LP file
    #
    if os.path.exists("baseline.lp"):  # pragma: no cover
        tmp = pyutilib.misc.compare_file("results.lp", "baseline.lp")
        assert tmp[0] == False, "Files differ:  diff {} {}".format(
            "results.lp", "baseline.lp"
        )
        os.remove("results.lp")
    #
    os.chdir(cwd)


# API tests


def test_t1():
    run("t1")


def test_t2():
    run("t2")


def test_t3():
    run("t3")


def test_t4():
    run("t4")


def test_t5():
    run("t5")


def test_t6():
    run("t6")


def test_t7():
    run("t7")


def test_t8():
    run("t8")


def test_t9():
    run("t9")


def test_t10():
    run("t10")


def test_t11():
    run("t11")


def test_t12():
    run("t12")


def test_e1():
    run("e1", retval=None)
