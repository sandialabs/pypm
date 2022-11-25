import ray
import shutil
import json
import glob
import os
from os.path import join
import yaml
import pytest
import pyutilib.misc
from pypm.util.fileutils import this_file_dir
from pypm.api import PYPM

currdir = this_file_dir()


def run(dirname, testname, debug=False, verify=False, nworkers=1):
    driver = PYPM.tabu_labeling()
    driver.load_config(join(currdir, dirname, "{}_config.yaml".format(testname)))
    driver.config.debug = debug
    driver.config.tee = debug
    driver.config.datafile = None
    assert testname == driver.config.process[:-12]

    results = driver.generate_labeling_and_schedule(nworkers=nworkers, setup_ray=False)

    outputfile = join(currdir, dirname, "{}_results.yaml".format(testname))
    results.write(outputfile)
    baselinefile = join(currdir, dirname, "{}_baseline.yaml".format(testname))
    tmp = pyutilib.misc.compare_file(outputfile, baselinefile, tolerance=1e-7)
    assert tmp[0] == False, "Files differ:  diff {} {}".format(outputfile, baselinefile)
    os.remove(outputfile)

    # labelfile = join(currdir, dirname, "{}_results.csv".format(testname))
    # results.write_labels(labelfile)
    # baselinefile = join(currdir, dirname, "{}_baseline.csv".format(testname))
    # tmp = pyutilib.misc.compare_file(labelfile, baselinefile, tolerance=1e-7)
    # assert tmp[0] == False, "Files differ:  diff {} {}".format(labelfile, baselinefile)
    # os.remove(labelfile)


@pytest.fixture
def ray_init():
    ray.init(num_cpus=4)
    yield None
    ray.shutdown()


@pytest.mark.parametrize(
    "tname",
    [
        "test100",  # solver_strategy == first_improvement
        "test101",
        "test103",
        "test104",
        "test105",
        "test106",
        "test107",
        "test900",  # test100 with solver_strategy == best_improvement
        "test901",
        "test902",
        "test903",
        "test904",
        "test905",
        "test906",
        "test907",
    ],
)
def test_GSFED1(tname, ray_init):
    run("GSFED1", tname, nworkers=3)


@pytest.mark.parametrize(
    "tname",
    [
        "test100",  # solver_strategy == first_improvement
        "test101",
        "test103",
        "test104",
        "test105",
        "test106",
        "test107",
        "test900",  # test100 with solver_strategy == best_improvement
        "test901",
        "test902",
        "test903",
        "test904",
        "test905",
        "test906",
        "test907",
    ],
)
def test_GSFED2(tname, ray_init):
    run("GSFED2", tname, nworkers=3)
