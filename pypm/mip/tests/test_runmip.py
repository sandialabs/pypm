import os
from os.path import dirname, join
import yaml
import pytest
import pyutilib.misc
from pypm.util import runsim
from pypm.api import PYPM
from pypm.util.fileutils import this_file_dir

currdir = this_file_dir()


def run(model, example, sim, supervised):
    datadir = join(currdir, model)

    processfile = join(
        dirname(dirname(currdir)), "util", "tests", "{}.yaml".format(example)
    )
    configfile = join(dirname(dirname(currdir)), "util", "tests", "{}.yaml".format(sim))
    data = runsim(
        processfile=processfile,
        configfile=configfile,
        model=model,
        supervised=supervised == "sup",
    )
    sim_config = join(datadir, "{}_{}_{}_sim.yaml".format(example, sim, supervised))
    open(sim_config, "w").write(yaml.dump(data, default_flow_style=None))

    driver = PYPM.supervised_mip()

    driver.load_config(sim_config)
    driver.config.dirname = datadir
    driver.config.datafile = None  # Ignore this for the test

    results = driver.generate_schedule()
    outputfile = join(datadir, "{}_{}_{}_results.yaml".format(example, sim, supervised))
    results.write(outputfile, verbose=True)

    baselinefile = join(
        datadir, "{}_{}_{}_baseline.yaml".format(example, sim, supervised)
    )
    tmp = pyutilib.misc.compare_file(outputfile, baselinefile, tolerance=1e-7)
    assert tmp[0] == False, "Files differ:  diff {} {}".format(outputfile, baselinefile)
    os.remove(outputfile)


if False:

    def test_model1_example1_sim1_sup():
        run("model1", "example1", "sim1", "sup")

    def test_model1_example2_sim1_sup():
        run("model1", "example2", "sim1", "sup")

    def test_model1_example1_sim2_sup():
        run("model1", "example1", "sim2", "sup")

    def test_model1_example2_sim2_sup():
        run("model1", "example2", "sim2", "sup")

    def test_model2_example1_sim1_usup():
        run("model2", "example1", "sim1", "usup")

    def test_model2_example2_sim1_usup():
        run("model2", "example2", "sim1", "usup")

    def test_model2_example1_sim2_usup():
        run("model2", "example1", "sim2", "usup")

    def test_model2_example2_sim2_usup():
        run("model2", "example2", "sim2", "usup")

    def test_model3_example1_sim1_sup():
        run("model3", "example1", "sim1", "sup")

    def test_model3_example2_sim1_sup():
        run("model3", "example2", "sim1", "sup")

    def test_model3_example1_sim2_sup():
        run("model3", "example1", "sim2", "sup")

    def test_model3_example2_sim2_sup():
        run("model3", "example2", "sim2", "sup")

    def test_model4_example1_sim1_usup():
        run("model4", "example1", "sim1", "usup")

    def test_model4_example2_sim1_usup():
        run("model4", "example2", "sim1", "usup")

    def test_model4_example1_sim2_usup():
        run("model4", "example1", "sim2", "usup")

    def test_model4_example2_sim2_usup():
        run("model4", "example2", "sim2", "usup")
