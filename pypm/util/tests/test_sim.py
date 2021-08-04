import pytest
from pypm.util.load import load_process
from pypm.util.sim import Simulator


def test_ex1():
    """
        a1 -> a2
    """
    data="""
resources:
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
  - rA
  name: a2
"""
    pm = load_process(data=data)

    assert len(pm) == 2

    data = []
    sim = Simulator(pm=pm, data=data, observe_activities=True)
    sim.run(10)
    assert data == [(0, 'a1'), (1, 'a1'), (2, 'a1'), (3, 'a1'), (4, 'a2'), (5, 'a2'), (6, 'a2'), (7, 'a2'), (8, 'a2')]

    data = []
    sim = Simulator(pm=pm, data=data)
    sim.run(10)
    assert data == [(0, 'rB'), (0, 'rC'), (1, 'rB'), (1, 'rC'), (2, 'rB'), (2, 'rC'), (3, 'rB'), (3, 'rC'), (4, 'rA'), (5, 'rA'), (6, 'rA'), (7, 'rA'), (8, 'rA')]

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
  - rA
  name: a2

- dependencies:
  - a1
  duration:
    max_hours: 3
    min_hours: 3
  resources:
  - rA
  name: a3
"""
    pm = load_process(data=data)

    assert len(pm) == 3

    data = []
    sim = Simulator(pm=pm, data=data, observe_activities=True)
    sim.run(10)
    assert data == [(0, 'a1'), (1, 'a1'), (2, 'a1'), (3, 'a1'), (4, 'a2'), (4, 'a3'), (5, 'a2'), (5, 'a3'), (6, 'a2'), (6, 'a3'), (7, 'a2'), (8, 'a2')]

    data = []
    sim = Simulator(pm=pm, data=data)
    sim.run(10)
    assert data == [(0, 'rB'), (0, 'rC'), (1, 'rB'), (1, 'rC'), (2, 'rB'), (2, 'rC'), (3, 'rB'), (3, 'rC'), (4, 'rA'), (4, 'rA'), (5, 'rA'), (5, 'rA'), (6, 'rA'), (6, 'rA'), (7, 'rA'), (8, 'rA')]

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
  - rA
  name: a2

- dependencies:
  duration:
    max_hours: 3
    min_hours: 3
  resources:
  - rA
  name: a3
"""
    pm = load_process(data=data)

    assert len(pm) == 3

    data = []
    sim = Simulator(pm=pm, data=data, observe_activities=True)
    sim.run(10)
    assert data == [(0, 'a1'), (0, 'a3'), (1, 'a1'), (1, 'a3'), (2, 'a1'), (2, 'a3'), (3, 'a1'), (4, 'a2'), (5, 'a2'), (6, 'a2'), (7, 'a2'), (8, 'a2')]

    data = []
    sim = Simulator(pm=pm, data=data)
    sim.run(10)
    assert data == [(0, 'rB'), (0, 'rC'), (0, 'rA'), (1, 'rB'), (1, 'rC'), (1, 'rA'), (2, 'rB'), (2, 'rC'), (2, 'rA'), (3, 'rB'), (3, 'rC'), (4, 'rA'), (5, 'rA'), (6, 'rA'), (7, 'rA'), (8, 'rA')]

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
  - rA
  name: a2

- dependencies:
  - a2
  - a4
  duration:
    max_hours: 3
    min_hours: 3
  resources:
  - rA
  name: a3

- dependencies:
  - a1
  duration:
    max_hours: 3
    min_hours: 3
  resources:
  - rA
  name: a4
"""
    pm = load_process(data=data)

    assert len(pm) == 4

    data = []
    sim = Simulator(pm=pm, data=data, observe_activities=True)
    sim.run(10)
    assert data == [(0, 'a1'), (1, 'a1'), (2, 'a1'), (3, 'a1'), (4, 'a2'), (4, 'a4'), (5, 'a2'), (5, 'a4'), (6, 'a2'), (6, 'a4'), (7, 'a2'), (8, 'a2'), (9, 'a3'), (10, 'a3'), (11, 'a3')]

    obs = sim.organize_observations(data, 15)
    assert obs == { 'a1':[1,1,1,1,0,0,0,0,0,0,0,0,0,0,0],
                    'a2':[0,0,0,0,1,1,1,1,1,0,0,0,0,0,0],
                    'a3':[0,0,0,0,0,0,0,0,0,1,1,1,0,0,0],
                    'a4':[0,0,0,0,1,1,1,0,0,0,0,0,0,0,0] }

    obs = sim.organize_observations(data)
    assert obs == { 'a1':[1,1,1,1,0,0,0,0,0,0,0,0],
                    'a2':[0,0,0,0,1,1,1,1,1,0,0,0],
                    'a3':[0,0,0,0,0,0,0,0,0,1,1,1],
                    'a4':[0,0,0,0,1,1,1,0,0,0,0,0] }

    data = []
    sim = Simulator(pm=pm, data=data)
    sim.run(10)
    assert data == [(0, 'rB'), (0, 'rC'), (1, 'rB'), (1, 'rC'), (2, 'rB'), (2, 'rC'), (3, 'rB'), (3, 'rC'), (4, 'rA'), (4, 'rA'), (5, 'rA'), (5, 'rA'), (6, 'rA'), (6, 'rA'), (7, 'rA'), (8, 'rA'), (9, 'rA'), (10, 'rA'), (11, 'rA')]

    obs = sim.organize_observations(data, 15)
    assert obs == {'rA': [0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0],
                   'rB': [1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                   'rC': [1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]}

    obs = sim.organize_observations(data)
    assert obs == {'rA': [0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1],
                   'rB': [1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
                   'rC': [1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0]}

def test_ex5():
    """
        a1 -> a2 -> a3
        a1 -> a4 -> a3

    Activity a4 has a delay starting
    """
    data="""
resources:
- (Unknown)
- rA
- rB
- rC

activities:

- name: a1
  dependencies:
  duration:
    max_hours: 4
    min_hours: 4
  resources:
  - rB
  - rC

- name: a2
  dependencies:
  - a1
  duration:
    max_hours: 5
    min_hours: 5
  resources:
  - rA

- name: a3
  dependencies:
  - a2
  - a4
  duration:
    max_hours: 3
    min_hours: 3
  resources:
  - rA

- name: a4
  max_delay: 5
  dependencies:
  - a1
  duration:
    max_hours: 3
    min_hours: 3
  resources:
  - rA
"""
    pm = load_process(data=data)

    assert len(pm) == 4

    data = []
    sim = Simulator(pm=pm, data=data, observe_activities=True)
    sim.run(10)
    #assert data == [(0, 'a1'), (1, 'a1'), (2, 'a1'), (3, 'a1'), (4, 'a2'), (4, 'a4'), (5, 'a2'), (5, 'a4'), (6, 'a2'), (6, 'a4'), (7, 'a2'), (8, 'a2'), (9, 'a3'), (10, 'a3'), (11, 'a3')]

    obs = sim.organize_observations(data, 20)
    assert obs == { 'a1':[1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                    'a2':[0,0,0,0,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0],
                    'a3':[0,0,0,0,0,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0],
                    'a4':[0,0,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0,0,0,0] }

    data = []
    sim = Simulator(pm=pm, data=data)
    sim.run(10)
    #assert data == [(0, 'a1'), (1, 'a1'), (2, 'a1'), (3, 'a1'), (4, 'a2'), (4, 'a4'), (5, 'a2'), (5, 'a4'), (6, 'a2'), (6, 'a4'), (7, 'a2'), (8, 'a2'), (9, 'a3'), (10, 'a3'), (11, 'a3')]

    obs = sim.organize_observations(data, 20)
    assert obs == {'rA': [0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0],
                   'rB': [1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                   'rC': [1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]}

def test_ex6():
    """
        a1 -> a2 -> a3
        a1 -> a4 -> a3

    Activity a4 has a delay starting
    """
    data="""
resources:
- (Unknown)
- rA
- rB
- rC

activities:

- name: a1
  max_delay: 4
  dependencies:
  duration:
    max_hours: 4
    min_hours: 4
  resources:
  - rB
  - rC

- name: a2
  dependencies:
  - a1
  duration:
    max_hours: 5
    min_hours: 5
  resources:
  - rA

- name: a3
  dependencies:
  - a2
  - a4
  duration:
    max_hours: 3
    min_hours: 3
  resources:
  - rA

- name: a4
  max_delay: 5
  dependencies:
  - a1
  duration:
    max_hours: 3
    min_hours: 3
  resources:
  - rA
"""
    pm = load_process(data=data)

    assert len(pm) == 4

    data = []
    sim = Simulator(pm=pm, data=data, observe_activities=True)
    sim.run(10)
    #assert data == [(0, 'a1'), (1, 'a1'), (2, 'a1'), (3, 'a1'), (4, 'a2'), (4, 'a4'), (5, 'a2'), (5, 'a4'), (6, 'a2'), (6, 'a4'), (7, 'a2'), (8, 'a2'), (9, 'a3'), (10, 'a3'), (11, 'a3')]

    obs = sim.organize_observations(data, 20)
    assert obs == { 'a1':[0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0],
                    'a2':[0,0,0,0,0,0,0,0,1,1,1,1,1,0,0,0,0,0,0,0],
                    'a3':[0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,0,0,0],
                    'a4':[0,0,0,0,0,0,0,0,0,0,0,1,1,1,0,0,0,0,0,0] }

    data = []
    sim = Simulator(pm=pm, data=data)
    sim.run(10)
    #assert data == [(0, 'a1'), (1, 'a1'), (2, 'a1'), (3, 'a1'), (4, 'a2'), (4, 'a4'), (5, 'a2'), (5, 'a4'), (6, 'a2'), (6, 'a4'), (7, 'a2'), (8, 'a2'), (9, 'a3'), (10, 'a3'), (11, 'a3')]

    obs = sim.organize_observations(data, 20)
    assert obs == {'rA': [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0],
                   'rB': [0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                   'rC': [0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]}


