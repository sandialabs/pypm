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
        max_delay_before=5,
        seed=123456789,
        quiet=quiet,
    )


# ---------------------------------------------------------------------------
# TESTS - Hidden State Parameters
# ---------------------------------------------------------------------------


def test_ex1_transition_params(ex1_simulations):
    params = estimate_transition_parameters(simulations=ex1_simulations)
    assert params.start_probs == {
        (): 0.8999100089991001,
        ("a1",): 0.09999000099990002,
        ("a2",): 9.999000099990002e-05,
    }
    assert params.transition_probs == {
        ((), ()): 0.7288135593220338,
        ((), ("a1",)): 0.15254237288135594,
        ((), ("a2",)): 0.11864406779661017,
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
        (): 9.998000399920017e-05,
        ("a1",): 0.9998000399920016,
        ("a2",): 9.998000399920017e-05,
    }
    assert params.transition_probs == {
        ((), ()): 0.3333333333333333,
        ((), ("a1",)): 0.3333333333333333,
        ((), ("a2",)): 0.3333333333333333,
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
        (): 0.7997600719784066,
        ("a1",): 0.19994001799460165,
        ("a2",): 9.997000899730082e-05,
        ("a2", "a3"): 9.997000899730082e-05,
        ("a3",): 9.997000899730082e-05,
    }
    assert params.transition_probs == {
        ((), ()): 0.6326530612244898,
        ((), ("a1",)): 0.16326530612244897,
        ((), ("a2",)): 0.08163265306122448,
        ((), ("a2", "a3")): 0.02040816326530612,
        ((), ("a3",)): 0.10204081632653061,
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
        (): 0.6998600279944011,
        ("a1",): 0.09998000399920016,
        ("a1", "a3"): 9.998000399920017e-05,
        ("a2",): 9.998000399920017e-05,
        ("a3",): 0.19996000799840033,
    }
    assert params.transition_probs == {
        ((), ()): 0.6326530612244898,
        ((), ("a1",)): 0.10204081632653061,
        ((), ("a1", "a3")): 0.02040816326530612,
        ((), ("a2",)): 0.16326530612244897,
        ((), ("a3",)): 0.08163265306122448,
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
        (): 0.6997201119552179,
        ("a1",): 0.2998800479808077,
        ("a2",): 9.996001599360257e-05,
        ("a2", "a4"): 9.996001599360257e-05,
        ("a3",): 9.996001599360257e-05,
        ("a4",): 9.996001599360257e-05,
    }
    assert params.transition_probs == pytest.approx(
        {
            ((), ()): 0.68,
            ((), ("a1",)): 0.09333333333333334,
            ((), ("a2",)): 0.04,
            ((), ("a2", "a4")): 0.013333333333333334,
            ((), ("a3",)): 0.12,
            ((), ("a4",)): 0.05333333333333334,
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
    )


def test_ex5_transition_params(ex5_simulations):
    params = estimate_transition_parameters(simulations=ex5_simulations)
    assert params.start_probs == {
        (): 0.6997201119552179,
        ("a1",): 0.2998800479808077,
        ("a2",): 9.996001599360257e-05,
        ("a2", "a4"): 9.996001599360257e-05,
        ("a3",): 9.996001599360257e-05,
        ("a4",): 9.996001599360257e-05,
    }
    assert params.transition_probs == {
        ((), ()): 0.7619047619047619,
        ((), ("a1",)): 0.06666666666666667,
        ((), ("a2",)): 0.02857142857142857,
        ((), ("a2", "a4")): 0.009523809523809525,
        ((), ("a3",)): 0.09523809523809523,
        ((), ("a4",)): 0.0380952380952381,
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
        (): 0.6997201119552179,
        ("a1",): 0.2998800479808077,
        ("a2",): 9.996001599360257e-05,
        ("a2", "a4"): 9.996001599360257e-05,
        ("a3",): 9.996001599360257e-05,
        ("a4",): 9.996001599360257e-05,
    }
    assert params.transition_probs == {
        ((), ()): 0.8137931034482758,
        ((), ("a1",)): 0.04827586206896552,
        ((), ("a2",)): 0.034482758620689655,
        ((), ("a2", "a4")): 0.006896551724137931,
        ((), ("a3",)): 0.06896551724137931,
        ((), ("a4",)): 0.027586206896551724,
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
        [0.7288135593220338, 0.15254237288135594, 0.11864406779661017],
        [0.175, 0.75, 0.075],
        [0.2, 0.0, 0.8],
    ]
    assert hmm.start_vec == [
        0.8999100089991001,
        0.09999000099990002,
        9.999000099990002e-05,
    ]
    assert hmm.observed_states == [(), ("oA",), ("oB",), ("oC",)]

    E = {
        h: {o: hmm.emission_mat[i][j] for j, o in enumerate(hmm.observed_states)}
        for i, h in enumerate(hmm.hidden_states)
    }
    tmp = {
        (): {
            (): 0.9705882352941174,
            ("oA",): 0.00980392156862746,
            ("oB",): 0.00980392156862746,
            ("oC",): 0.009803921568627458,
        },
        ("a1",): {
            (): 0.052050473186119856,
            ("oA",): 0.0005257623554153526,
            ("oB",): 0.47371188222923244,
            ("oC",): 0.4737118822292324,
        },
        ("a2",): {
            (): 0.0988023952095808,
            ("oA",): 0.8992015968063871,
            ("oB",): 0.0009980039920159686,
            ("oC",): 0.0009980039920159686,
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
        [
            0.6326530612244898,
            0.16326530612244897,
            0.08163265306122448,
            0.02040816326530612,
            0.10204081632653061,
        ],
        [0.175, 0.75, 0.025, 0.0, 0.05],
        [0.225, 0.0, 0.725, 0.05, 0.0],
        [0.0, 0.0, 0.4, 0.5, 0.1],
        [0.2, 0.0, 0.1, 0.1, 0.6],
    ]
    assert hmm.start_vec == [
        0.7997600719784066,
        0.19994001799460165,
        9.997000899730082e-05,
        9.997000899730082e-05,
        9.997000899730082e-05,
    ]
    assert hmm.observed_states == [(), ("oA",), ("oB",), ("oC",)]

    E = {
        h: {o: hmm.emission_mat[i][j] for j, o in enumerate(hmm.observed_states)}
        for i, h in enumerate(hmm.hidden_states)
    }
    tmp = {
        (): {
            (): 0.9705882352941175,
            ("oA",): 0.009803921568627461,
            ("oB",): 0.009803921568627461,
            ("oC",): 0.00980392156862746,
        },
        ("a1",): {
            (): 0.052050473186119856,
            ("oA",): 0.0005257623554153526,
            ("oB",): 0.47371188222923244,
            ("oC",): 0.4737118822292324,
        },
        ("a2",): {
            (): 0.0988023952095808,
            ("oA",): 0.8992015968063871,
            ("oB",): 0.0009980039920159686,
            ("oC",): 0.0009980039920159686,
        },
        ("a2", "a3"): {
            (): 0.009898020395920812,
            ("oA",): 0.9899020195960808,
            ("oB",): 9.998000399920022e-05,
            ("oC",): 9.998000399920022e-05,
        },
        ("a3",): {
            (): 0.0988023952095808,
            ("oA",): 0.8992015968063871,
            ("oB",): 0.0009980039920159686,
            ("oC",): 0.0009980039920159686,
        },
    }
    for i in E:
        assert E[i] == pytest.approx(tmp[i])
