import os
from os.path import join
import yaml
import pytest
import pyutilib.misc
from pypm.api import PYPM
from pypm.util.fileutils import this_file_dir

currdir = this_file_dir()


def run(testname, dirname, debug=False, verify=False):
    unsupervised = dirname in ["UPM"]
    dirname = join(currdir, dirname)
    if unsupervised:
        driver = PYPM.unsupervised_mip()
    else:
        driver = PYPM.supervised_mip()

    driver.load_config(join(dirname, "{}.yaml".format(testname)))
    driver.config.dirname = dirname
    driver.config.debug = debug
    driver.config.tee = debug
    driver.config.datafile = None  # Ignore this for the test
    assert testname.startswith(driver.config.process[:-5])

    results = driver.generate_schedule()
    outputfile = join(dirname, "{}_results.yaml".format(testname))
    results.write(outputfile, verbose=True)

    if verify:
        alignment = results["results"][0]["alignment"]
        for j, val in data["data"][0]["ground_truth"].items():
            assert (val["start"] == alignment[j]["start"]) and (
                val["stop"] == alignment[j]["stop"]
            ), "Differ from ground truth: {} {} {}".format(
                j, str(val), str(alignment[j])
            )

    baselinefile = join(dirname, "{}_baseline.yaml".format(testname))
    tmp = pyutilib.misc.compare_file(outputfile, baselinefile, tolerance=1e-7)
    assert tmp[0] == False, "Files differ:  diff {} {}".format(outputfile, baselinefile)
    os.remove(outputfile)


def test1_11():
    run("test1", "model11")


def test2_11():
    run("test2", "model11")


def test3_11():
    run("test3", "model11")


def test4_11():
    run("test4", "model11")


def test5_11():
    run("test5", "model11")


def test6_11():
    run("test6", "model11")


def test7_11():
    run("test7", "model11")


def test100_11():
    run("test100", "model11")


def test101_11():
    run("test101", "model11")


def test102_11():
    run("test102", "model11")


def test103_11():
    run("test103", "model11")


def test104_11():
    run("test104", "model11")


def test105_11():
    run("test105", "model11")


def test106_11():
    run("test106", "model11")


def test107_11():
    run("test107", "model11")


def test108_11():
    run("test108", "model11")


def test301_11():
    run("test301", "model11")


def test302_11():
    run("test302", "model11")


def test1_GSF_compact():
    run("test1", "GSF-compact")


def test2_GSF_compact():
    run("test2", "GSF-compact")


def test3_GSF_compact():
    run("test3", "GSF-compact")


def test4_GSF_compact():
    run("test4", "GSF-compact")


def test5_GSF_compact():
    run("test5", "GSF-compact")


def test6_GSF_compact():
    run("test6", "GSF-compact")


def test7_GSF_compact():
    run("test7", "GSF-compact")


def test100_GSF_compact():
    run("test100", "GSF-compact")


def test101_GSF_compact():
    run("test101", "GSF-compact")


def test102_GSF_compact():
    run("test102", "GSF-compact")


def test103_GSF_compact():
    run("test103", "GSF-compact")


def test104_GSF_compact():
    run("test104", "GSF-compact")


def test105_GSF_compact():
    run("test105", "GSF-compact")


def test106_GSF_compact():
    run("test106", "GSF-compact")


def test107_GSF_compact():
    run("test107", "GSF-compact")


def test108_GSF_compact():
    run("test108", "GSF-compact")


def test300_GSF_compact():
    run("test300", "GSF-compact")


def test301_GSF_compact():
    run("test301", "GSF-compact")


def test302_GSF_compact():
    run("test302", "GSF-compact")


def test1_13():
    run("test1", "model13")


def test2_13():
    run("test2", "model13")


def test3_13():
    run("test3", "model13")


def test4_13():
    run("test4", "model13")


def test5_13():
    run("test5", "model13")


def test6_13():
    run("test6", "model13")


def test7_13():
    run("test7", "model13")


def test100_13():
    run("test100", "model13")


def test101_13():
    run("test101", "model13")


def test102_13():
    run("test102", "model13")


def test103_13():
    run("test103", "model13")


def test104_13():
    run("test104", "model13")


def test105_13():
    run("test105", "model13")


def test106_13():
    run("test106", "model13")


def test107_13():
    run("test107", "model13")


def test201_13():
    run("test201", "model13")


def test1_UPM():
    run("test1", "UPM")


def test2_UPM():
    run("test2", "UPM")


def test3_UPM():
    run("test3", "UPM")


def test4_UPM():
    run("test4", "UPM")


def test5_UPM():
    run("test5", "UPM")


def test6_UPM():
    run("test6", "UPM")


def test7_UPM():
    run("test7", "UPM")


def test100_UPM():
    run("test100", "UPM")


def test101_UPM():
    run("test101", "UPM")


def test102_UPM():
    run("test102", "UPM")


def test103_UPM():
    run("test103", "UPM")


def test104_UPM():
    run("test104", "UPM")


def test105_UPM():
    run("test105", "UPM")


def test106_UPM():
    run("test106", "UPM")


def test107_UPM():
    run("test107", "UPM")


def test1_XSF():
    run("test1", "XSF")


def test2_XSF():
    run("test2", "XSF")


def test3_XSF():
    run("test3", "XSF")


def test4_XSF():
    run("test4", "XSF")


def test5_XSF():
    run("test5", "XSF")


def test6_XSF():
    run("test6", "XSF")


def test7_XSF():
    run("test7", "XSF")


def test100_XSF():
    run("test100", "XSF")


def test101_XSF():
    run("test101", "XSF")


def test102_XSF():
    run("test102", "XSF")


def test103_XSF():
    run("test103", "XSF")


def test104_XSF():
    run("test104", "XSF")


def test105_XSF():
    run("test105", "XSF")


def test106_XSF():
    run("test106", "XSF")


def test107_XSF():
    run("test107", "XSF")


def test108_XSF():
    run("test108", "XSF")


def test1_XSF_compact():
    run("test1", "XSF-compact")


def test2_XSF_compact():
    run("test2", "XSF-compact")


def test3_XSF_compact():
    run("test3", "XSF-compact")


def test4_XSF_compact():
    run("test4", "XSF-compact")


def test5_XSF_compact():
    run("test5", "XSF-compact")


def test6_XSF_compact():
    run("test6", "XSF-compact")


def test7_XSF_compact():
    run("test7", "XSF-compact")


def test100_XSF_compact():
    run("test100", "XSF-compact")


def test101_XSF_compact():
    run("test101", "XSF-compact", debug=True)


def test102_XSF_compact():
    run("test102", "XSF-compact")


def test103_XSF_compact():
    run("test103", "XSF-compact")


def test104_XSF_compact():
    run("test104", "XSF-compact")


def test105_XSF_compact():
    run("test105", "XSF-compact")


def test106_XSF_compact():
    run("test106", "XSF-compact")


def test107_XSF_compact():
    run("test107", "XSF-compact")


def test108_XSF_compact():
    run("test108", "XSF-compact")


def test300_XSF_compact():
    run("test300", "XSF-compact")
