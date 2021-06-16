import pytest
from pypm.util.load import load_data


def test_pm_simple():
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

