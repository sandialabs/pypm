import os
from os.path import join
import yaml
import pytest
import pyutilib.misc
from pypm.mip import runmip_from_datafile
from pypm.util.fileutils import this_file_dir

currdir = this_file_dir()

def run(testname, debug=False, verify=False):
    configfile = '{}_config.yaml'.format(testname)
    with open(join(currdir, configfile), 'r') as INPUT:
        data = yaml.safe_load(INPUT)
    assert testname+"_process.yaml" == data['_options']['process']

    results = runmip_from_datafile(data=data, model=data['_options']['model'], dirname=currdir, debug=debug, tee=debug)
    output = yaml.dump(results, default_flow_style=None) 
    outputfile = join(currdir, "{}_results.yaml".format(testname))
    with open(outputfile, "w") as OUTPUT:
        OUTPUT.write(output)

    if verify:
        alignment = results['results'][0]['alignment']
        for j,val in data['data'][0]['ground_truth'].items():
            assert ((val['start'] == alignment[j]['start']) and (val['stop'] == alignment[j]['stop'])), "Differ from ground truth: {} {} {}".format(j, str(val), str(alignment[j]))
 
    tmp = pyutilib.misc.compare_file(outputfile, join(currdir, "{}_baseline.yaml".format(testname)), tolerance=1e-7)
    assert tmp[0] == False
    os.remove(outputfile)


def test1():
    run('run1')

