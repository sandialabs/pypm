import pytest
from pypm.util.load import load_data
from pypm.util.fileutils import this_file_dir

currdir = this_file_dir()


def test_pm_simple_string():
    data="""
resources:
- (Unknown)
- ResourceA
- ResourceB
- ResourceC

activities:

- dependencies:
  duration:
    max_hours: 10
    min_hours: 5
  resources:
  - ResourceB
  - ResourceC
  name: Activity1

- dependencies:
  - Activity1
  duration:
    max_hours: 5
    min_hours: 5
  resources:
  name: Activity2
"""
    pm = load_data(data=data)

    assert len(pm) == 2

    assert pm['Activity1']['id'] == 0
    assert pm['Activity1']['name'] == 'Activity1'
    assert pm['Activity1']['resources'] == ['ResourceB', 'ResourceC']
    assert pm['Activity1']['dependencies'] == []
    assert pm[0]['id'] == 0

    assert pm['Activity2']['id'] == 1
    assert pm['Activity2']['name'] == 'Activity2'
    assert pm['Activity2']['resources'] == []
    assert pm['Activity2']['dependencies'] == ['Activity1']
    assert pm[1]['id'] == 1


def test_pm_simple_file():
    filename="example1.yaml"
    pm = load_data(filename=filename, dirname=currdir)

    assert len(pm) == 2

    assert pm['Activity1']['id'] == 0
    assert pm['Activity1']['name'] == 'Activity1'
    assert pm['Activity1']['resources'] == ['ResourceB', 'ResourceC']
    assert pm['Activity1']['dependencies'] == []
    assert pm[0]['id'] == 0

    assert pm['Activity2']['id'] == 1
    assert pm['Activity2']['name'] == 'Activity2'
    assert pm['Activity2']['resources'] == []
    assert pm['Activity2']['dependencies'] == ['Activity1']
    assert pm[1]['id'] == 1

def test_error_bad1():
    data="""
resources:
- (Unknown)
- ResourceA
- ResourceB
- ResourceC

activities:

- dependencies:
  duration:
    max_hours: 10
    min_hours: 5
  resources:
  - ResourceB
  - ResourceC
  name: Activity1

- dependencies:
  - Activity1
  duration:
    max_hours: 5
    min_hours: 5
  resources:
  name: Activity2
"""
    pm = load_data(data=data)

    with pytest.raises(KeyError):
        pm['Activity3']
    with pytest.raises(KeyError):
        pm[2]
    with pytest.raises(KeyError):
        pm['Activity1']['bad']

def test_error_bad2():
    data="""
resources:
- (Unknown)
- ResourceA
- ResourceB
- ResourceA

activities:

- dependencies:
  duration:
    max_hours: 10
    min_hours: 5
  resources:
  - ResourceB
  - ResourceA
  name: Activity1

"""
    with pytest.raises(AssertionError):
        pm = load_data(data=data)

def test_error_bad3():
    data="""
bad:

resources:
- (Unknown)
- ResourceA
- ResourceB

activities:

- dependencies:
  duration:
    max_hours: 10
    min_hours: 5
  resources:
  - ResourceB
  - ResourceA
  name: Activity1

"""
    with pytest.raises(AssertionError):
        pm = load_data(data=data)

def test_error_bad4():
    data="""
resources:
- (Unknown)
- ResourceA
- ResourceB

activities:

- dependencies:
  duration:
    max_hours: 10
    min_hours: 5
  resources:
  - ResourceB
  - ResourceA
  name: Activity1
- name: Activity1

"""
    with pytest.raises(AssertionError):
        pm = load_data(data=data)

