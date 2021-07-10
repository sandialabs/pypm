import pytest

from pypm.util.load import load_data
#from pypm.util.fileutils import this_file_dir
#currdir = this_file_dir()
from pypm.util.sim import Simulator


def test_ex1():
    """
        a1 -> a2
    """
    data="""
resources:
- (Unknown)
- rA
- rB
- rC

activities:

- dependencies:
  duration:
    max_hours: 4
    min_hours: 4
  resources:
  - rB
  - rC
  name: a1

- dependencies:
  - a1
  duration:
    max_hours: 5
    min_hours: 5
  resources:
    rA
  name: a2
"""
    pm = load_data(data=data)

    assert len(pm) == 2

    data = []
    sim = Simulator(pm=pm, data=data)
    sim.run(10)
    assert data == [(0, 'a1'), (1, 'a1'), (2, 'a1'), (3, 'a1'), (4, 'a2'), (5, 'a2'), (6, 'a2'), (7, 'a2'), (8, 'a2')]

def test_ex2():
    """
        a1 -> a2
        a1 -> a3
    """
    data="""
resources:
- (Unknown)
- rA
- rB
- rC

activities:

- dependencies:
  duration:
    max_hours: 4
    min_hours: 4
  resources:
  - rB
  - rC
  name: a1

- dependencies:
  - a1
  duration:
    max_hours: 5
    min_hours: 5
  resources:
    rA
  name: a2

- dependencies:
  - a1
  duration:
    max_hours: 3
    min_hours: 3
  resources:
    rA
  name: a3
"""
    pm = load_data(data=data)

    assert len(pm) == 3

    data = []
    sim = Simulator(pm=pm, data=data)
    sim.run(10)
    assert data == [(0, 'a1'), (1, 'a1'), (2, 'a1'), (3, 'a1'), (4, 'a2'), (4, 'a3'), (5, 'a2'), (5, 'a3'), (6, 'a2'), (6, 'a3'), (7, 'a2'), (8, 'a2')]

def test_ex3():
    """
        a1 -> a2
        a3 -> a2
    """
    data="""
resources:
- (Unknown)
- rA
- rB
- rC

activities:

- dependencies:
  duration:
    max_hours: 4
    min_hours: 4
  resources:
  - rB
  - rC
  name: a1

- dependencies:
  - a1
  - a3
  duration:
    max_hours: 5
    min_hours: 5
  resources:
    rA
  name: a2

- dependencies:
  duration:
    max_hours: 3
    min_hours: 3
  resources:
    rA
  name: a3
"""
    pm = load_data(data=data)

    assert len(pm) == 3

    data = []
    sim = Simulator(pm=pm, data=data)
    sim.run(10)
    assert data == [(0, 'a1'), (0, 'a3'), (1, 'a1'), (1, 'a3'), (2, 'a1'), (2, 'a3'), (3, 'a1'), (4, 'a2'), (5, 'a2'), (6, 'a2'), (7, 'a2'), (8, 'a2')]

def test_ex4():
    """
        a1 -> a2 -> a3
        a1 -> a4 -> a3
    """
    data="""
resources:
- (Unknown)
- rA
- rB
- rC

activities:

- dependencies:
  duration:
    max_hours: 4
    min_hours: 4
  resources:
  - rB
  - rC
  name: a1

- dependencies:
  - a1
  duration:
    max_hours: 5
    min_hours: 5
  resources:
    rA
  name: a2

- dependencies:
  - a2
  - a4
  duration:
    max_hours: 3
    min_hours: 3
  resources:
    rA
  name: a3

- dependencies:
  - a1
  duration:
    max_hours: 3
    min_hours: 3
  resources:
    rA
  name: a4
"""
    pm = load_data(data=data)

    assert len(pm) == 4

    data = []
    sim = Simulator(pm=pm, data=data)
    sim.run(10)
    assert data == [(0, 'a1'), (1, 'a1'), (2, 'a1'), (3, 'a1'), (4, 'a2'), (4, 'a4'), (5, 'a2'), (5, 'a4'), (6, 'a2'), (6, 'a4'), (7, 'a2'), (8, 'a2'), (9, 'a3'), (10, 'a3'), (11, 'a3')]


