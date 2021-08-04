import pytest
from pypm.util.load import load_process
from pypm.util.fileutils import this_file_dir

currdir = this_file_dir()


def test_pm_simple_string():
    data="""
resources:
- rA
- rB
- rC

activities:

- dependencies:
  duration:
    max_hours: 10
    min_hours: 5
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
  name: a2
"""
    pm = load_process(data=data)

    assert len(pm) == 2

    assert pm['a1']['id'] == 0
    assert pm['a1']['name'] == 'a1'
    assert pm['a1']['resources'] == ['rB', 'rC']
    assert pm['a1']['dependencies'] == []
    assert pm[0]['id'] == 0

    assert pm['a2']['id'] == 1
    assert pm['a2']['name'] == 'a2'
    assert pm['a2']['resources'] == []
    assert pm['a2']['dependencies'] == ['a1']
    assert pm[1]['id'] == 1


def test_pm_simple_file():
    filename="example1.yaml"
    pm = load_process(filename=filename, dirname=currdir)

    assert len(pm) == 2

    assert pm['a1']['id'] == 0
    assert pm['a1']['name'] == 'a1'
    assert pm['a1']['resources'] == ['rB', 'rC']
    assert pm['a1']['dependencies'] == []
    assert pm[0]['id'] == 0

    assert pm['a2']['id'] == 1
    assert pm['a2']['name'] == 'a2'
    assert pm['a2']['resources'] == []
    assert pm['a2']['dependencies'] == ['a1']
    assert pm[1]['id'] == 1

def test_error_bad1():
    data="""
resources:
- rA
- rB
- rC

activities:

- dependencies:
  duration:
    max_hours: 10
    min_hours: 5
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
  name: a2
"""
    pm = load_process(data=data)

    with pytest.raises(KeyError):
        pm['a3']
    with pytest.raises(KeyError):
        pm[2]
    with pytest.raises(KeyError):
        pm['a1']['bad']

def test_error_bad2():
    data="""
resources:
- rA
- rB
- rA

activities:

- dependencies:
  duration:
    max_hours: 10
    min_hours: 5
  resources:
  - rB
  - rA
  name: a1

"""
    with pytest.raises(AssertionError):
        pm = load_process(data=data)

def test_error_bad3():
    data="""
bad:

resources:
- rA
- rB

activities:

- dependencies:
  duration:
    max_hours: 10
    min_hours: 5
  resources:
  - rB
  - rA
  name: a1

"""
    with pytest.raises(AssertionError):
        pm = load_process(data=data)

def test_error_bad4():
    data="""
resources:
- rA
- rB

activities:

- dependencies:
  duration:
    max_hours: 10
    min_hours: 5
  resources:
  - rB
  - rA
  name: a1
- name: a1

"""
    with pytest.raises(AssertionError):
        pm = load_process(data=data)

def test_error_bad5():
    data="""
resources:
- rA
- rB

activities:

- dependencies:
  duration:
    max_hours: 10
    min_hours: 5
  resources:
    rB
  name: a1
- name: a2

"""
    # Bad resources specification.  Must be a list
    with pytest.raises(AssertionError):
        pm = load_process(data=data)

