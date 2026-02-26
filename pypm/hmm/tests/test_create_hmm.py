import pyutilib.misc
import pytest
import os
import munch

from pypm.util.fileutils import this_file_dir
from pypm.util.load import load_process
from pypm.util.run_simian import run_simian, create_data_wrapper
from pypm.hmm.create_hmm import estimate_transition_parameters, create_hmm
from pypm.hmm.estimate_emissions import initial_emission_parameters


from . import examples

currdir = this_file_dir()

quiet = True
num_simulations = 10


def config(**kwds):
    return munch.DefaultMunch(None, **kwds)


# ---------------------------------------------------------------------------
# ex1
# ---------------------------------------------------------------------------


@pytest.fixture
def ex1_pm():
    """Load process model for ex1"""
    return load_process(data=examples.ex1)


@pytest.fixture
def ex1_simulations(ex1_pm):
    """Generate simulations for ex1"""
    return run_simian(
        pm=ex1_pm,
        num_simulations=num_simulations,
        num_time_steps=20,
        max_delay_before=5,
        seed=123456789,
        quiet=quiet,
    )


@pytest.fixture
def ex1_nodelay_simulations(ex1_pm):
    """Generate simulations for ex1 with no delay"""
    return run_simian(
        pm=ex1_pm,
        num_simulations=num_simulations,
        num_time_steps=20,
        seed=123456789,
        quiet=quiet,
    )


# ---------------------------------------------------------------------------
# ex2
# ---------------------------------------------------------------------------


@pytest.fixture
def ex2_pm():
    """Load process model for ex2"""
    return load_process(data=examples.ex2)


@pytest.fixture
def ex2_simulations(ex2_pm):
    """Generate simulations for ex2"""
    return run_simian(
        pm=ex2_pm,
        num_simulations=num_simulations,
        num_time_steps=20,
        max_delay_before=5,
        seed=123456789,
        quiet=quiet,
    )


# ---------------------------------------------------------------------------
# ex3
# ---------------------------------------------------------------------------


@pytest.fixture
def ex3_pm():
    """Load process model for ex3"""
    return load_process(data=examples.ex3)


@pytest.fixture
def ex3_simulations(ex3_pm):
    """Generate simulations for ex3"""
    return run_simian(
        pm=ex3_pm,
        num_simulations=num_simulations,
        num_time_steps=20,
        max_delay_before=5,
        seed=123456789,
        quiet=quiet,
    )


# ---------------------------------------------------------------------------
# ex4
# ---------------------------------------------------------------------------


@pytest.fixture
def ex4_pm():
    """Load process model for ex4"""
    return load_process(data=examples.ex4)


@pytest.fixture
def ex4_simulations(ex4_pm):
    """Generate simulations for ex4"""
    return run_simian(
        pm=ex4_pm,
        num_simulations=num_simulations,
        num_time_steps=20,
        max_delay_before=5,
        seed=123456789,
        quiet=quiet,
    )


# ---------------------------------------------------------------------------
# ex5
# ---------------------------------------------------------------------------


@pytest.fixture
def ex5_pm():
    """Load process model for ex5"""
    return load_process(data=examples.ex5)


@pytest.fixture
def ex5_simulations(ex5_pm):
    """Generate simulations for ex5"""
    return run_simian(
        pm=ex5_pm,
        num_simulations=num_simulations,
        num_time_steps=30,
        max_delay_before=5,
        seed=123456789,
        quiet=quiet,
    )


# ---------------------------------------------------------------------------
# ex6
# ---------------------------------------------------------------------------


@pytest.fixture
def ex6_pm():
    """Load process model for ex6"""
    return load_process(data=examples.ex6)


@pytest.fixture
def ex6_simulations(ex6_pm):
    """Generate simulations for ex6"""
    return run_simian(
        pm=ex6_pm,
        num_simulations=num_simulations,
        num_time_steps=30,
        max_delay_before=5,
        seed=123456789,
        quiet=quiet,
    )


# ---------------------------------------------------------------------------
# TESTS - Hidden State Parameters
# ---------------------------------------------------------------------------


def test_ex1_transition_params(ex1_simulations):
    params = estimate_transition_parameters(simulations=ex1_simulations)
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


def test_ex1_nodelay_transition_params(ex1_nodelay_simulations):
    params = estimate_transition_parameters(simulations=ex1_nodelay_simulations)
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


def test_ex2_transition_params(ex2_simulations):
    params = estimate_transition_parameters(simulations=ex2_simulations)
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


def test_ex3_transition_params(ex3_simulations):
    params = estimate_transition_parameters(simulations=ex3_simulations)
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


def test_ex4_transition_params(ex4_simulations):
    params = estimate_transition_parameters(simulations=ex4_simulations)
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


def test_ex5_transition_params(ex5_simulations):
    params = estimate_transition_parameters(simulations=ex5_simulations)
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


def test_ex6_transition_params(ex6_simulations):
    params = estimate_transition_parameters(simulations=ex6_simulations)
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


# ---------------------------------------------------------------------------
# TESTS - Emission Parameters
# ---------------------------------------------------------------------------


def test_ex1_initial_emission_params(ex1_pm):
    params = initial_emission_parameters(
        data_wrapper=create_data_wrapper(pm=ex1_pm, features={"oA", "oB", "oC"})
    )
    assert params.true_positive == {
        ("a1", "oA"): 0.9,
        ("a1", "oB"): 0.9,
        ("a1", "oC"): 0.9,
        ("a2", "oA"): 0.9,
        ("a2", "oB"): 0.9,
        ("a2", "oC"): 0.9,
    }
    assert params.false_emission == {"oA": 0.01, "oB": 0.01, "oC": 0.01}

    # Restrict process features to those related to resources
    known_process_features = dict(a1={"oB", "oC"}, a2={"oA"})
    params = initial_emission_parameters(
        data_wrapper=create_data_wrapper(
            config=config(pm=ex1_pm, known_process_features=known_process_features),
            pm=ex1_pm,
            features={"oA", "oB", "oC"},
        )
    )
    assert params.true_positive == {
        ("a1", "oB"): 0.9,
        ("a1", "oC"): 0.9,
        ("a2", "oA"): 0.9,
    }
    assert params.false_emission == {"oA": 0.01, "oB": 0.01, "oC": 0.01}

    # Restrict process features to those related to resources
    known_process_features = dict(a1={"oB", "oC"}, a2={"oA"})
    possible_process_features = dict(a1={"oA"}, a2={"oB", "oC"})
    params = initial_emission_parameters(
        data_wrapper=create_data_wrapper(
            config=config(
                pm=ex1_pm,
                known_process_features=known_process_features,
                possible_process_features=possible_process_features,
            ),
            pm=ex1_pm,
            features={"oA", "oB", "oC"},
        )
    )
    assert params.true_positive == {
        ("a1", "oA"): 0.5,
        ("a1", "oB"): 0.9,
        ("a1", "oC"): 0.9,
        ("a2", "oA"): 0.9,
        ("a2", "oB"): 0.5,
        ("a2", "oC"): 0.5,
    }
    assert params.false_emission == {"oA": 0.01, "oB": 0.01, "oC": 0.01}


def test_ex1_initial_emission_params_alt_values(ex1_pm):
    params = initial_emission_parameters(
        data_wrapper=create_data_wrapper(pm=ex1_pm, features={"oA", "oB", "oC"}),
        known_positive=0.5,
        false_emission=0.1,
    )
    assert params.true_positive == {
        ("a1", "oA"): 0.5,
        ("a1", "oB"): 0.5,
        ("a1", "oC"): 0.5,
        ("a2", "oA"): 0.5,
        ("a2", "oB"): 0.5,
        ("a2", "oC"): 0.5,
    }
    assert params.false_emission == {"oA": 0.1, "oB": 0.1, "oC": 0.1}


def test_ex2_initial_emission_params(ex2_pm):
    params = initial_emission_parameters(
        data_wrapper=create_data_wrapper(pm=ex2_pm, features={"oA", "oB", "oC"})
    )
    assert params.true_positive == {
        ("a1", "oA"): 0.9,
        ("a1", "oB"): 0.9,
        ("a1", "oC"): 0.9,
        ("a2", "oA"): 0.9,
        ("a2", "oB"): 0.9,
        ("a2", "oC"): 0.9,
        ("a3", "oA"): 0.9,
        ("a3", "oB"): 0.9,
        ("a3", "oC"): 0.9,
    }
    assert params.false_emission == {"oA": 0.01, "oB": 0.01, "oC": 0.01}

    # Restrict process features to those related to resources
    known_process_features = dict(a1={"oB", "oC"}, a2={"oA"}, a3={"oA"})
    params = initial_emission_parameters(
        data_wrapper=create_data_wrapper(
            config=config(pm=ex2_pm, known_process_features=known_process_features),
            pm=ex2_pm,
            features={"oA", "oB", "oC"},
        )
    )
    assert params.true_positive == {
        ("a1", "oB"): 0.9,
        ("a1", "oC"): 0.9,
        ("a2", "oA"): 0.9,
        ("a3", "oA"): 0.9,
    }
    assert params.false_emission == {"oA": 0.01, "oB": 0.01, "oC": 0.01}


def test_ex3_initial_emission_params(ex3_pm):
    params = initial_emission_parameters(
        data_wrapper=create_data_wrapper(pm=ex3_pm, features={"oA", "oB", "oC"})
    )
    assert params.true_positive == {
        ("a1", "oA"): 0.9,
        ("a1", "oB"): 0.9,
        ("a1", "oC"): 0.9,
        ("a2", "oA"): 0.9,
        ("a2", "oB"): 0.9,
        ("a2", "oC"): 0.9,
        ("a3", "oA"): 0.9,
        ("a3", "oB"): 0.9,
        ("a3", "oC"): 0.9,
    }
    assert params.false_emission == {"oA": 0.01, "oB": 0.01, "oC": 0.01}

    # Restrict process features to those related to resources
    known_process_features = dict(a1={"oB", "oC"}, a2={"oA"}, a3={"oA"})
    params = initial_emission_parameters(
        data_wrapper=create_data_wrapper(
            config=config(pm=ex3_pm, known_process_features=known_process_features),
            pm=ex3_pm,
            features={"oA", "oB", "oC"},
        )
    )
    assert params.true_positive == {
        ("a1", "oB"): 0.9,
        ("a1", "oC"): 0.9,
        ("a2", "oA"): 0.9,
        ("a3", "oA"): 0.9,
    }
    assert params.false_emission == {"oA": 0.01, "oB": 0.01, "oC": 0.01}


def test_ex4_initial_emission_params(ex4_pm):
    params = initial_emission_parameters(
        data_wrapper=create_data_wrapper(pm=ex4_pm, features={"oA", "oB", "oC"})
    )
    assert params.true_positive == {
        ("a1", "oA"): 0.9,
        ("a1", "oB"): 0.9,
        ("a1", "oC"): 0.9,
        ("a2", "oA"): 0.9,
        ("a2", "oB"): 0.9,
        ("a2", "oC"): 0.9,
        ("a3", "oA"): 0.9,
        ("a3", "oB"): 0.9,
        ("a3", "oC"): 0.9,
        ("a4", "oA"): 0.9,
        ("a4", "oB"): 0.9,
        ("a4", "oC"): 0.9,
    }
    assert params.false_emission == {"oA": 0.01, "oB": 0.01, "oC": 0.01}


def test_ex5_initial_emission_params(ex5_pm):
    params = initial_emission_parameters(
        data_wrapper=create_data_wrapper(pm=ex5_pm, features={"oA", "oB", "oC"})
    )
    assert params.true_positive == {
        ("a1", "oA"): 0.9,
        ("a1", "oB"): 0.9,
        ("a1", "oC"): 0.9,
        ("a2", "oA"): 0.9,
        ("a2", "oB"): 0.9,
        ("a2", "oC"): 0.9,
        ("a3", "oA"): 0.9,
        ("a3", "oB"): 0.9,
        ("a3", "oC"): 0.9,
        ("a4", "oA"): 0.9,
        ("a4", "oB"): 0.9,
        ("a4", "oC"): 0.9,
    }
    assert params.false_emission == {"oA": 0.01, "oB": 0.01, "oC": 0.01}


def test_ex6_initial_emission_params(ex6_pm):
    params = initial_emission_parameters(
        data_wrapper=create_data_wrapper(pm=ex6_pm, features={"oA", "oB", "oC"})
    )
    assert params.true_positive == {
        ("a1", "oA"): 0.9,
        ("a1", "oB"): 0.9,
        ("a1", "oC"): 0.9,
        ("a2", "oA"): 0.9,
        ("a2", "oB"): 0.9,
        ("a2", "oC"): 0.9,
        ("a3", "oA"): 0.9,
        ("a3", "oB"): 0.9,
        ("a3", "oC"): 0.9,
        ("a4", "oA"): 0.9,
        ("a4", "oB"): 0.9,
        ("a4", "oC"): 0.9,
    }
    assert params.false_emission == {"oA": 0.01, "oB": 0.01, "oC": 0.01}


# ---------------------------------------------------------------------------
# TESTS - HMM Parameters
# ---------------------------------------------------------------------------


def test_ex1_create_hmm(ex1_pm, ex1_simulations):
    transition_params = estimate_transition_parameters(simulations=ex1_simulations)
    known_process_features = dict(a1={"oB", "oC"}, a2={"oA"})
    emission_params = initial_emission_parameters(
        data_wrapper=create_data_wrapper(
            config=config(pm=ex1_pm, known_process_features=known_process_features),
            pm=ex1_pm,
            features={"oA", "oB", "oC"},
        )
    )
    hmm = create_hmm(
        observed_states={(), ("oA",), ("oC",), ("oB",)},
        transition_params=transition_params,
        emission_params=emission_params,
    )
    assert hmm.hidden_states == [(), ("a1",), ("a2",)]
    assert hmm.transition_mat == [
        [0.84, 0.09, 0.07],
        [0.175, 0.75, 0.075],
        [0.2, 0.0, 0.8],
    ]
    assert hmm.start_vec == [0.9, 0.1, 0.0]
    assert hmm.observed_states == [(), ("_unknown_",), ("oA",), ("oB",), ("oC",)]

    E = {
        h: {o: hmm.emission_mat[i][j] for j, o in enumerate(hmm.observed_states)}
        for i, h in enumerate(hmm.hidden_states)
    }
    tmp = {
        (): {
            (): 0.9702989999999999,
            ("_unknown_",): 0.00029800000000002047,
            ("oA",): 0.00980100000000001,
            ("oB",): 0.00980100000000001,
            ("oC",): 0.009801000000000008,
        },
        ("a1",): {
            (): 0.009702989999999995,
            ("_unknown_",): 0.81358498,
            ("oA",): 9.801000000000005e-05,
            ("oB",): 0.08830700999999999,
            ("oC",): 0.08830700999999998,
        },
        ("a2",): {
            (): 0.09702989999999997,
            ("_unknown_",): 0.01793979999999984,
            ("oA",): 0.8830701000000001,
            ("oB",): 0.0009801000000000007,
            ("oC",): 0.0009801000000000007,
        },
    }
    for i in E:
        assert E[i] == pytest.approx(tmp[i])


def test_ex2_create_hmm(ex2_pm, ex2_simulations):
    transition_params = estimate_transition_parameters(simulations=ex2_simulations)
    known_process_features = dict(a1={"oB", "oC"}, a2={"oA"}, a3={"oA"})
    emission_params = initial_emission_parameters(
        data_wrapper=create_data_wrapper(
            config=config(pm=ex2_pm, known_process_features=known_process_features),
            pm=ex2_pm,
            features={"oA", "oB", "oC"},
        )
    )
    hmm = create_hmm(
        observed_states={(), ("oA",), ("oB",), ("oC",)},
        transition_params=transition_params,
        emission_params=emission_params,
    )
    assert hmm.hidden_states == [(), ("a1",), ("a2",), ("a2", "a3"), ("a3",)]
    assert hmm.transition_mat == [
        [0.775, 0.1, 0.05, 0.0125, 0.0625],
        [0.175, 0.75, 0.025, 0.0, 0.05],
        [0.225, 0.0, 0.725, 0.05, 0.0],
        [0.0, 0.0, 0.4, 0.5, 0.1],
        [0.2, 0.0, 0.1, 0.1, 0.6],
    ]
    assert hmm.start_vec == [0.8, 0.2, 0.0, 0.0, 0.0]
    assert hmm.observed_states == [(), ("_unknown_",), ("oA",), ("oB",), ("oC",)]

    E = {
        h: {o: hmm.emission_mat[i][j] for j, o in enumerate(hmm.observed_states)}
        for i, h in enumerate(hmm.hidden_states)
    }
    tmp = {
        (): {
            (): 0.9702989999999999,
            ("_unknown_",): 0.00029799999999990945,
            ("oA",): 0.00980100000000001,
            ("oB",): 0.00980100000000001,
            ("oC",): 0.009801000000000008,
        },
        ("a1",): {
            (): 0.009702989999999995,
            ("_unknown_",): 0.81358498,
            ("oA",): 9.801000000000005e-05,
            ("oB",): 0.08830700999999999,
            ("oC",): 0.08830700999999998,
        },
        ("a2",): {
            (): 0.09702989999999997,
            ("_unknown_",): 0.01793979999999984,
            ("oA",): 0.8830701000000001,
            ("oB",): 0.0009801000000000007,
            ("oC",): 0.0009801000000000007,
        },
        ("a2", "a3"): {
            (): 0.009702989999999995,
            ("_unknown_",): 0.019703980000000176,
            ("oA",): 0.9703970099999999,
            ("oB",): 9.801000000000005e-05,
            ("oC",): 9.801000000000005e-05,
        },
        ("a3",): {
            (): 0.09702989999999997,
            ("_unknown_",): 0.01793979999999984,
            ("oA",): 0.8830701000000001,
            ("oB",): 0.0009801000000000007,
            ("oC",): 0.0009801000000000007,
        },
    }
    for i in E:
        assert E[i] == pytest.approx(tmp[i])
