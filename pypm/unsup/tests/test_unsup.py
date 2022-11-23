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

    results = driver.generate_labeling_and_schedule(nworkers=nworkers)

    outputfile = join(currdir, dirname, "{}_results.yaml".format(testname))
    results.write(outputfile)
    baselinefile = join(currdir, dirname, "{}_baseline.yaml".format(testname))
    tmp = pyutilib.misc.compare_file(outputfile, baselinefile, tolerance=1e-7)
    assert tmp[0] == False, "Files differ:  diff {} {}".format(outputfile, baselinefile)
    os.remove(outputfile)

    labelfile = join(currdir, dirname, "{}_results.csv".format(testname))
    results.write_labels(labelfile)
    baselinefile = join(currdir, dirname, "{}_baseline.csv".format(testname))
    tmp = pyutilib.misc.compare_file(labelfile, baselinefile, tolerance=1e-7)
    assert tmp[0] == False, "Files differ:  diff {} {}".format(labelfile, baselinefile)
    os.remove(labelfile)


@pytest.mark.parametrize(
    "tname",
    [
        "test100",
        "test101",
        "test103",
        "test104",
        "test105",
        "test106",
        "test107",
        "test200",  # test100 without combined features
        "test201",
        "test202",
        "test203",
        "test204",
        "test205",
        "test206",
        "test207",
        "test300",  # test100 with "always-on" features
        "test301",
        "test401",
        "test402",
        "test403",
        "test404",
        "test405",
        "test406",
        "test407",
        "test501",  # Extending test401
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
def test_GSFED1(tname):
    run("GSFED1", tname)


@pytest.mark.parametrize(
    "tname",
    [
        "test100",
        "test101",
        "test103",
        "test104",
        "test105",
        "test106",
        "test107",
        "test200",  # test100 without combined features
        "test201",
        "test202",
        "test203",
        "test204",
        "test205",
        "test206",
        "test207",
        "test300",  # test100 with "always-on" features
        "test301",
        "test401",
        "test402",
        "test403",
        "test404",
        "test405",
        "test406",
        "test407",
        "test501",  # Extending test401
        "test600",  # With labeling restrictions
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
def test_GSFED2(tname):
    run("GSFED2", tname)

@pytest.mark.parametrize(
    "tname",
    [
        "test100",
        "test101",
        "test103",
        "test104",
        "test105",
        "test106",
        "test107",
        "test200",  # test100 without combined features
        "test201",
        "test202",
        "test203",
        "test204",
        "test205",
        "test206",
        "test207",
        "test300",  # test100 with "always-on" features
        "test301",
        "test401",
        "test402",
        "test403",
        "test404",
        "test405",
        "test406",
        "test407",
        "test501",  # Extending test401
        "test600",  # With labeling restrictions
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
def test_XSF2(tname):
    run("XSF2", tname)

def test_misc_cached():
    run("MISC", "test_cached")
    checkpoint_dir = os.path.join(currdir, "MISC", "checkpoints")

    values = {}
    points = {}
    for fname in glob.glob( os.path.join(checkpoint_dir, "*.json")):
        with open(fname, "r") as INPUT:
            data = json.load(INPUT)
            values[data["iteration"]] = data["value"]
            points[data["iteration"]] = data["point"]

    values_baseline = {
        0: -2.0,
        3: -1.3333333333333333
        }
    points_baseline = {
        0: {"rA": {"ra": 1, "rb": 0, "rc": 0}, "rB": {"ra": 1, "rb": 0, "rc": 1}, "rC": {"ra": 1, "rb": 1, "rc": 1}},
        3: {"rA": {"ra": 1, "rb": 1, "rc": 0}, "rB": {"ra": 1, "rb": 0, "rc": 0}, "rC": {"ra": 0, "rb": 1, "rc": 1}},
    }
    assert values == values_baseline
    assert points == points_baseline

    if os.path.exists(checkpoint_dir):
        shutil.rmtree(checkpoint_dir)

