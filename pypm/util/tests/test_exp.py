import yaml
import pytest
from pypm.util.exp import runsim


def test_ex1():
    """
        a1 -> a2
    """
    process="""
resources:
- (Unknown)
- rA
- rB
- rC

activities:

- name: a1
  dependencies:
  max_delay: 10
  duration:
    max_hours: 8
    min_hours: 4
  resources:
  - rB
  - rC

- name: a2
  dependencies:
  - a1
  duration:
    max_hours: 10 
    min_hours: 5
  resources:
  - rA
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
  model: model1
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
