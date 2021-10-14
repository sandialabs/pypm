import os
from os.path import join
import yaml
import pytest
import pyutilib.misc
from pypm.chunk import chunk_process
from pypm.util.fileutils import this_file_dir

currdir = this_file_dir()

def run(testname, filename, step):
    outputfile = join(currdir, testname+"_results.yaml")
    chunk_process(join(currdir, filename), outputfile, step)

    baselinefile = join(currdir, testname+"_baseline.yaml")
    tmp = pyutilib.misc.compare_file(outputfile, baselinefile, tolerance=1e-7)
    assert tmp[0] == False, "Files differ:  diff {} {}".format(outputfile, baselinefile)
    os.remove(outputfile)


def test1_2h():
    run('process1_2h', 'process1.yaml', '2h')

def test1_2h_7_17():
    run('process1_2h_7_17', 'process1.yaml', '2h_workday(7-17)')

def test1_5h_7_17():
    run('process1_5h_7_17', 'process1.yaml', '5h_workday(7-17)')

def test1_10h_7_17():
    run('process1_10h_7_17', 'process1.yaml', '10h_workday(7-17)')

