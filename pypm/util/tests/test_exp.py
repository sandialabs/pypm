import os.path
import yaml
import pytest
from pypm.util.exp import runsim
from pypm.util.fileutils import this_file_dir

currdir = this_file_dir()


def test_ex1a():
    """
        a1 -> a2
    """
    process="""
resources:
  rA:
  rB:
  rC:

activities:

- name: a1
  dependencies:
  max_delay: 10
  duration:
    max_hours: 8
    min_hours: 4
  resources:
    rB:
    rC:

- name: a2
  dependencies:
  - a1
  duration:
    max_hours: 10 
    min_hours: 5
  resources:
    rA:
"""
    config = """
ntrials: 1
seeds:
- 0
timesteps: 30
"""

    results = runsim(config=config, process=process)
    output = yaml.dump(results, default_flow_style=None) 
    assert output == \
"""_options:
  comments: []
  config: null
  model: model3
  process: null
  solver: glpk
  tee: false
  timesteps: 30
data:
- ground_truth:
    a1: {start: 6, stop: 12}
    a2: {start: 13, stop: 17}
  observations:
    rA: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0,
      0, 0, 0, 0, 0]
    rB: [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
      0, 0, 0, 0, 0]
    rC: [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
      0, 0, 0, 0, 0]
  seed: 0
  trial: 0
"""

# TODO - Weaken equality test to ignore the config and process full pathname
def test_ex1b():
    """
        a1 -> a2
    """
    results = runsim(configfile=os.path.join(currdir,'sim1.yaml'), processfile=os.path.join(currdir,'example2.yaml'))
    output = yaml.dump(results, default_flow_style=None) 
    assert output == \
"""_options:
  comments: []
  config: /home/wehart/dev/adapd/pypm/pypm/util/tests/sim1.yaml
  model: model3
  process: /home/wehart/dev/adapd/pypm/pypm/util/tests/example2.yaml
  solver: glpk
  tee: false
  timesteps: 30
data:
- ground_truth:
    a1: {start: 6, stop: 12}
    a2: {start: 13, stop: 17}
  observations:
    rA: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0,
      0, 0, 0, 0, 0]
    rB: [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
      0, 0, 0, 0, 0]
    rC: [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
      0, 0, 0, 0, 0]
  seed: 0
  trial: 0
"""


# TODO - Weaken equality test to ignore the config and process full pathname
def test_ex1c():
    """
        a1 -> a2
    """
    outputfile = os.path.join(currdir,'test_ex1c.yaml')
    results = runsim(configfile=os.path.join(currdir,'sim2.yaml'), processfile=os.path.join(currdir,'example2.yaml'), supervised=False, outputfile=outputfile)
    output = yaml.dump(results, default_flow_style=None) 
    assert output == \
"""_options:
  comments: []
  config: /home/wehart/dev/adapd/pypm/pypm/util/tests/sim2.yaml
  model: model4
  process: /home/wehart/dev/adapd/pypm/pypm/util/tests/example2.yaml
  sigma: 1
  solver: glpk
  tee: false
  timesteps: 30
data:
- ground_truth:
    a1: {start: 6, stop: 12}
    a2: {start: 13, stop: 17}
  observations:
    u0: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0,
      0, 0, 0, 0, 0]
    u1: [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
      0, 0, 0, 0, 0]
    u2: [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
      0, 0, 0, 0, 0]
  seed: 0
  trial: 0
"""
    assert os.path.exists( outputfile )
    os.remove(outputfile)
