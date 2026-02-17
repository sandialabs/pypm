import pytest

from pypm.util.load import load_process
from pypm.util.run_simian import run_simian

from pypm.hmm.create_hmm import estimate_hidden_state_parameters

# from pypm.util.fileutils import this_file_dir
# currdir = this_file_dir()

quiet = True
num_simulations = 10


ex1 = """
resources:
  rA:
  rB:
  rC:

activities:

- dependencies:
  duration:
    max_hours: 4
    min_hours: 4
  resources:
    rB:
    rC:
  name: a1

- dependencies:
  - a1
  duration:
    max_hours: 5
    min_hours: 5
  resources:
    rA:
  name: a2
"""


@pytest.fixture
def ex1_simulations():
    """Generate simulations for ex1"""
    pm = load_process(data=ex1)

    return run_simian(
        pm=pm,
        num_simulations=num_simulations,
        num_time_steps=20,
        max_delay_before=5,
        seed=123456789,
        quiet=quiet,
    )


@pytest.fixture
def ex1_nodelay_simulations():
    """Generate simulations for ex1"""
    pm = load_process(data=ex1)

    return run_simian(
        pm=pm,
        num_simulations=num_simulations,
        num_time_steps=20,
        seed=123456789,
        quiet=quiet,
    )


ex2 = """
resources:
  rA:
  rB:
  rC:

activities:

- dependencies:
  duration:
    max_hours: 4
    min_hours: 4
  resources:
    rB:
    rC:
  name: a1

- dependencies:
  - a1
  duration:
    max_hours: 5
    min_hours: 5
  resources:
    rA:
  name: a2

- dependencies:
  - a1
  duration:
    max_hours: 3
    min_hours: 3
  resources:
    rA:
  name: a3
"""


@pytest.fixture
def ex2_simulations():
    """Generate simulations for ex2"""
    pm = load_process(data=ex2)

    return run_simian(
        pm=pm,
        num_simulations=num_simulations,
        num_time_steps=20,
        max_delay_before=5,
        seed=123456789,
        quiet=quiet,
    )


ex3 = """
resources:
  rA:
  rB:
  rC:

activities:

- dependencies:
  duration:
    max_hours: 4
    min_hours: 4
  resources:
    rB:
    rC:
  name: a1

- dependencies:
  - a1
  - a3
  duration:
    max_hours: 5
    min_hours: 5
  resources:
    rA:
  name: a2

- dependencies:
  duration:
    max_hours: 3
    min_hours: 3
  resources:
    rA:
  name: a3
"""


@pytest.fixture
def ex3_simulations():
    """Generate simulations for ex3"""
    pm = load_process(data=ex3)
    return run_simian(
        pm=pm,
        num_simulations=num_simulations,
        num_time_steps=20,
        max_delay_before=5,
        seed=123456789,
        quiet=quiet,
    )


ex4 = """
resources:
  rA:
  rB:
  rC:

activities:

- dependencies:
  duration:
    max_hours: 4
    min_hours: 4
  resources:
    rB:
    rC:
  name: a1

- dependencies:
  - a1
  duration:
    max_hours: 5
    min_hours: 5
  resources:
    rA:
  name: a2

- dependencies:
  - a2
  - a4
  duration:
    max_hours: 3
    min_hours: 3
  resources:
    rA:
  name: a3

- dependencies:
  - a1
  duration:
    max_hours: 3
    min_hours: 3
  resources:
    rA:
  name: a4
"""


@pytest.fixture
def ex4_simulations():
    """Generate simulations for ex4"""
    pm = load_process(data=ex4)

    return run_simian(
        pm=pm,
        num_simulations=num_simulations,
        num_time_steps=20,
        max_delay_before=5,
        seed=123456789,
        quiet=quiet,
    )


ex5 = """
resources:
  rA:
  rB:
  rC:

activities:

- name: a1
  dependencies:
  duration:
    max_hours: 4
    min_hours: 4
  resources:
    rB:
    rC:

- name: a2
  dependencies:
  - a1
  duration:
    max_hours: 5
    min_hours: 5
  resources:
    rA:

- name: a3
  dependencies:
  - a2
  - a4
  duration:
    max_hours: 3
    min_hours: 3
  resources:
    rA:

- name: a4
  delay_after_hours: 5
  dependencies:
  - a1
  duration:
    max_hours: 3
    min_hours: 3
  resources:
    rA:
"""


@pytest.fixture
def ex5_simulations():
    """Generate simulations for ex5"""
    pm = load_process(data=ex5)

    return run_simian(
        pm=pm,
        num_simulations=num_simulations,
        num_time_steps=30,
        max_delay_before=5,
        seed=123456789,
        quiet=quiet,
    )


ex6 = """
resources:
  rA:
  rB:
  rC:

activities:

- name: a1
  delay_after_hours: 4
  dependencies:
  duration:
    max_hours: 4
    min_hours: 4
  resources:
    rB:
    rC:

- name: a2
  dependencies:
  - a1
  duration:
    max_hours: 5
    min_hours: 5
  resources:
    rA:

- name: a3
  dependencies:
  - a2
  - a4
  duration:
    max_hours: 3
    min_hours: 3
  resources:
    rA:

- name: a4
  delay_after_hours: 5
  dependencies:
  - a1
  duration:
    max_hours: 3
    min_hours: 3
  resources:
    rA:
"""


@pytest.fixture
def ex6_simulations():
    """Generate simulations for ex6"""
    pm = load_process(data=ex6)

    return run_simian(
        pm=pm,
        num_simulations=num_simulations,
        num_time_steps=30,
        max_delay_before=5,
        seed=123456789,
        quiet=quiet,
    )


def test_ex1_hidden_state_params(ex1_simulations):
    params = estimate_hidden_state_parameters(simulations=ex1_simulations)
    assert params.start_probs == {(): 0.9, ("a1",): 0.1, ("a2",): 0.0}
    assert params.transition_probs == {
        ((), ()): 0.84,
        ((), ("a1",)): 0.09,
        ((), ("a2",)): 0.07,
        (("a1",), ()): 0.175,
        (("a1",), ("a1",)): 0.75,
        (("a1",), ("a2",)): 0.075,
        (("a2",), ()): 0.2,
        (("a2",), ("a1",)): 0.0,
        (("a2",), ("a2",)): 0.8,
    }


def test_ex1_nodelay_hidden_state_params(ex1_nodelay_simulations):
    params = estimate_hidden_state_parameters(simulations=ex1_nodelay_simulations)
    assert params.start_probs == {
        (): 0.0009990009990009992,
        ("a1",): 0.9990009990009991,
        ("a2",): 0.0,
    }
    assert params.transition_probs == {
        ((), ()): 1.0,
        ((), ("a1",)): 0.0,
        ((), ("a2",)): 0.0,
        (("a1",), ()): 0.0,
        (("a1",), ("a1",)): 0.75,
        (("a1",), ("a2",)): 0.25,
        (("a2",), ()): 0.2,
        (("a2",), ("a1",)): 0.0,
        (("a2",), ("a2",)): 0.8,
    }


def test_ex2_hidden_state_params(ex2_simulations):
    params = estimate_hidden_state_parameters(simulations=ex2_simulations)
    assert params.start_probs == {
        (): 0.8,
        ("a1",): 0.2,
        ("a2",): 0.0,
        ("a2", "a3"): 0.0,
        ("a3",): 0.0,
    }
    assert params.transition_probs == {
        ((), ()): 0.775,
        ((), ("a1",)): 0.1,
        ((), ("a2",)): 0.05,
        ((), ("a2", "a3")): 0.0125,
        ((), ("a3",)): 0.0625,
        (("a1",), ()): 0.175,
        (("a1",), ("a1",)): 0.75,
        (("a1",), ("a2",)): 0.025,
        (("a1",), ("a2", "a3")): 0.0,
        (("a1",), ("a3",)): 0.05,
        (("a2",), ()): 0.225,
        (("a2",), ("a1",)): 0.0,
        (("a2",), ("a2",)): 0.725,
        (("a2",), ("a2", "a3")): 0.05,
        (("a2",), ("a3",)): 0.0,
        (("a2", "a3"), ()): 0.0,
        (("a2", "a3"), ("a1",)): 0.0,
        (("a2", "a3"), ("a2",)): 0.4,
        (("a2", "a3"), ("a2", "a3")): 0.5,
        (("a2", "a3"), ("a3",)): 0.1,
        (("a3",), ()): 0.2,
        (("a3",), ("a1",)): 0.0,
        (("a3",), ("a2",)): 0.1,
        (("a3",), ("a2", "a3")): 0.1,
        (("a3",), ("a3",)): 0.6,
    }


def test_ex3_hidden_state_params(ex3_simulations):
    params = estimate_hidden_state_parameters(simulations=ex3_simulations)
    assert params.start_probs == {
        (): 0.7,
        ("a1",): 0.1,
        ("a1", "a3"): 0.0,
        ("a2",): 0.0,
        ("a3",): 0.2,
    }
    assert params.transition_probs == {
        ((), ()): 0.7777777777777778,
        ((), ("a1",)): 0.06172839506172839,
        ((), ("a1", "a3")): 0.012345679012345678,
        ((), ("a2",)): 0.09876543209876543,
        ((), ("a3",)): 0.04938271604938271,
        (("a1",), ()): 0.1724137931034483,
        (("a1",), ("a1",)): 0.6551724137931034,
        (("a1",), ("a1", "a3")): 0.06896551724137931,
        (("a1",), ("a2",)): 0.06896551724137931,
        (("a1",), ("a3",)): 0.034482758620689655,
        (("a1", "a3"), ()): 0.18181818181818182,
        (("a1", "a3"), ("a1",)): 0.18181818181818182,
        (("a1", "a3"), ("a1", "a3")): 0.6363636363636364,
        (("a1", "a3"), ("a2",)): 0.0,
        (("a1", "a3"), ("a3",)): 0.0,
        (("a2",), ()): 0.2,
        (("a2",), ("a1",)): 0.0,
        (("a2",), ("a1", "a3")): 0.0,
        (("a2",), ("a2",)): 0.8,
        (("a2",), ("a3",)): 0.0,
        (("a3",), ()): 0.21052631578947367,
        (("a3",), ("a1",)): 0.10526315789473684,
        (("a3",), ("a1", "a3")): 0.05263157894736842,
        (("a3",), ("a2",)): 0.0,
        (("a3",), ("a3",)): 0.631578947368421,
    }


def test_ex4_hidden_state_params(ex4_simulations):
    params = estimate_hidden_state_parameters(simulations=ex4_simulations)
    assert params.start_probs == {
        (): 0.7,
        ("a1",): 0.3,
        ("a2",): 0.0,
        ("a2", "a4"): 0.0,
        ("a3",): 0.0,
        ("a4",): 0.0,
    }
    assert params.transition_probs == {
        ((), ()): 0.7368421052631579,
        ((), ("a1",)): 0.09210526315789473,
        ((), ("a2",)): 0.039473684210526314,
        ((), ("a2", "a4")): 0.013157894736842105,
        ((), ("a3",)): 0.06578947368421052,
        ((), ("a4",)): 0.05263157894736842,
        (("a1",), ()): 0.2,
        (("a1",), ("a1",)): 0.75,
        (("a1",), ("a2",)): 0.05,
        (("a1",), ("a2", "a4")): 0.0,
        (("a1",), ("a3",)): 0.0,
        (("a1",), ("a4",)): 0.0,
        (("a2",), ()): 0.2,
        (("a2",), ("a1",)): 0.0,
        (("a2",), ("a2",)): 0.6,
        (("a2",), ("a2", "a4")): 0.16666666666666666,
        (("a2",), ("a3",)): 0.03333333333333333,
        (("a2",), ("a4",)): 0.0,
        (("a2", "a4"), ()): 0.1,
        (("a2", "a4"), ("a1",)): 0.0,
        (("a2", "a4"), ("a2",)): 0.3,
        (("a2", "a4"), ("a2", "a4")): 0.55,
        (("a2", "a4"), ("a3",)): 0.0,
        (("a2", "a4"), ("a4",)): 0.05,
        (("a3",), ()): 0.21428571428571427,
        (("a3",), ("a1",)): 0.0,
        (("a3",), ("a2",)): 0.0,
        (("a3",), ("a2", "a4")): 0.0,
        (("a3",), ("a3",)): 0.7857142857142857,
        (("a3",), ("a4",)): 0.0,
        (("a4",), ()): 0.1,
        (("a4",), ("a1",)): 0.0,
        (("a4",), ("a2",)): 0.1,
        (("a4",), ("a2", "a4")): 0.3,
        (("a4",), ("a3",)): 0.0,
        (("a4",), ("a4",)): 0.5,
    }


def test_ex5_hidden_state_params(ex5_simulations):
    params = estimate_hidden_state_parameters(simulations=ex5_simulations)
    assert params.start_probs == {
        (): 0.7,
        ("a1",): 0.3,
        ("a2",): 0.0,
        ("a2", "a4"): 0.0,
        ("a3",): 0.0,
        ("a4",): 0.0,
    }
    assert params.transition_probs == {
        ((), ()): 0.84375,
        ((), ("a1",)): 0.04375,
        ((), ("a2",)): 0.01875,
        ((), ("a2", "a4")): 0.00625,
        ((), ("a3",)): 0.0625,
        ((), ("a4",)): 0.025,
        (("a1",), ()): 0.2,
        (("a1",), ("a1",)): 0.75,
        (("a1",), ("a2",)): 0.05,
        (("a1",), ("a2", "a4")): 0.0,
        (("a1",), ("a3",)): 0.0,
        (("a1",), ("a4",)): 0.0,
        (("a2",), ()): 0.23333333333333334,
        (("a2",), ("a1",)): 0.0,
        (("a2",), ("a2",)): 0.6,
        (("a2",), ("a2", "a4")): 0.16666666666666666,
        (("a2",), ("a3",)): 0.0,
        (("a2",), ("a4",)): 0.0,
        (("a2", "a4"), ()): 0.1,
        (("a2", "a4"), ("a1",)): 0.0,
        (("a2", "a4"), ("a2",)): 0.3,
        (("a2", "a4"), ("a2", "a4")): 0.55,
        (("a2", "a4"), ("a3",)): 0.0,
        (("a2", "a4"), ("a4",)): 0.05,
        (("a3",), ()): 0.3333333333333333,
        (("a3",), ("a1",)): 0.0,
        (("a3",), ("a2",)): 0.0,
        (("a3",), ("a2", "a4")): 0.0,
        (("a3",), ("a3",)): 0.6666666666666666,
        (("a3",), ("a4",)): 0.0,
        (("a4",), ()): 0.1,
        (("a4",), ("a1",)): 0.0,
        (("a4",), ("a2",)): 0.1,
        (("a4",), ("a2", "a4")): 0.3,
        (("a4",), ("a3",)): 0.0,
        (("a4",), ("a4",)): 0.5,
    }


def test_ex6_hidden_state_params(ex6_simulations):
    params = estimate_hidden_state_parameters(simulations=ex6_simulations)
    assert params.start_probs == {
        (): 0.7,
        ("a1",): 0.3,
        ("a2",): 0.0,
        ("a2", "a4"): 0.0,
        ("a3",): 0.0,
        ("a4",): 0.0,
    }
    assert params.transition_probs == {
        ((), ()): 0.8333333333333334,
        ((), ("a1",)): 0.043209876543209874,
        ((), ("a2",)): 0.030864197530864196,
        ((), ("a2", "a4")): 0.006172839506172839,
        ((), ("a3",)): 0.06172839506172839,
        ((), ("a4",)): 0.024691358024691357,
        (("a1",), ()): 0.25,
        (("a1",), ("a1",)): 0.75,
        (("a1",), ("a2",)): 0.0,
        (("a1",), ("a2", "a4")): 0.0,
        (("a1",), ("a3",)): 0.0,
        (("a1",), ("a4",)): 0.0,
        (("a2",), ()): 0.23333333333333334,
        (("a2",), ("a1",)): 0.0,
        (("a2",), ("a2",)): 0.6,
        (("a2",), ("a2", "a4")): 0.16666666666666666,
        (("a2",), ("a3",)): 0.0,
        (("a2",), ("a4",)): 0.0,
        (("a2", "a4"), ()): 0.1,
        (("a2", "a4"), ("a1",)): 0.0,
        (("a2", "a4"), ("a2",)): 0.3,
        (("a2", "a4"), ("a2", "a4")): 0.55,
        (("a2", "a4"), ("a3",)): 0.0,
        (("a2", "a4"), ("a4",)): 0.05,
        (("a3",), ()): 0.2857142857142857,
        (("a3",), ("a1",)): 0.0,
        (("a3",), ("a2",)): 0.0,
        (("a3",), ("a2", "a4")): 0.0,
        (("a3",), ("a3",)): 0.7142857142857143,
        (("a3",), ("a4",)): 0.0,
        (("a4",), ()): 0.1,
        (("a4",), ("a1",)): 0.0,
        (("a4",), ("a2",)): 0.1,
        (("a4",), ("a2", "a4")): 0.3,
        (("a4",), ("a3",)): 0.0,
        (("a4",), ("a4",)): 0.5,
    }
