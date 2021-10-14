import os
from os.path import join
import yaml
import pytest
import pyutilib.misc
from pypm.chunk import chunk_csv
from pypm.util.fileutils import this_file_dir

currdir = this_file_dir()

def run(testname, filename, step):
    outputfile = join(currdir,testname+"_results.csv")
    chunk_csv(join(currdir, filename), outputfile, "DateTime", step)

    baselinefile = join(currdir,testname+"_baseline.csv")
    tmp = pyutilib.misc.compare_file(outputfile, baselinefile, tolerance=1e-7)
    assert tmp[0] == False, "Files differ:  diff {} {}".format(outputfile, baselinefile)
    os.remove(outputfile)


def test1_2h():
    run('test1_2h', 'test1.csv', '2h')

def test1_2h_7_17():
    run('test1_2h_7_17', 'test1.csv', '2h_workday(7-17)')

def test1_10h_7_17():
    run('test1_10h_7_17', 'test1.csv', '10h_workday(7-17)')

