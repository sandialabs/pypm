import pyutilib.misc
import pytest
import os
import munch

from pypm.util.fileutils import this_file_dir
from pypm.util.load import load_process

# from pypm.util.run_simian import run_simian, create_data_wrapper
# from pypm.hmm.create_hmm import estimate_hidden_state_parameters, create_hmm
# from pypm.hmm.estimate_emissions import initial_emission_parameters
from pypm.hmm.hmm_application import PypmHMMApplication

from pypm.hmm.tests import examples

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


# ---------------------------------------------------------------------------
# ex2
# ---------------------------------------------------------------------------


@pytest.fixture
def ex2_pm():
    """Load process model for ex2"""
    return load_process(data=examples.ex2)


# ---------------------------------------------------------------------------
# ex3
# ---------------------------------------------------------------------------


@pytest.fixture
def ex3_pm():
    """Load process model for ex3"""
    return load_process(data=examples.ex3)


# ---------------------------------------------------------------------------
# ex4
# ---------------------------------------------------------------------------


@pytest.fixture
def ex4_pm():
    """Load process model for ex4"""
    return load_process(data=examples.ex4)


# ---------------------------------------------------------------------------
# ex5
# ---------------------------------------------------------------------------


@pytest.fixture
def ex5_pm():
    """Load process model for ex5"""
    return load_process(data=examples.ex5)


# ---------------------------------------------------------------------------
# ex6
# ---------------------------------------------------------------------------


def ex6_pm():
    """Load process model for ex6"""
    return load_process(data=examples.ex6)


# ---------------------------------------------------------------------------
# TESTS - HMM Application
# ---------------------------------------------------------------------------


@pytest.fixture
def ex1_application(ex1_pm):
    app = PypmHMMApplication()

    features = {"oA", "oB", "oC"}
    known_process_features = dict(a1={"oB", "oC"}, a2={"oA"})
    observed_states = {(), ("oA",), ("oC",), ("oB",)}

    app.initialize(
        config(
            pm=ex1_pm, known_process_features=known_process_features, features=features
        )
    )

    app.learn_transition_parameters(
        num_simulations=num_simulations,
        num_time_steps=20,
        max_delay_before=5,
        seed=123456789,
        quiet=quiet,
    )

    app.create_hmm(observed_states=observed_states)

    return app


def test_ex1_application(ex1_application):
    hmm = ex1_application.hmm

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
            ("_unknown_",): 0.01793979999999995,
            ("oA",): 0.8830701000000001,
            ("oB",): 0.0009801000000000007,
            ("oC",): 0.0009801000000000007,
        },
    }
    for i in E:
        assert E[i] == pytest.approx(tmp[i])


@pytest.fixture
def ex2_application(ex2_pm):
    app = PypmHMMApplication()

    features = {"oA", "oB", "oC"}
    known_process_features = dict(a1={"oB", "oC"}, a2={"oA"}, a3={"oA"})
    observed_states = {(), ("oA",), ("oC",), ("oB",)}

    app.initialize(
        config(
            pm=ex2_pm, known_process_features=known_process_features, features=features
        )
    )

    app.learn_transition_parameters(
        num_simulations=num_simulations,
        num_time_steps=20,
        max_delay_before=5,
        seed=123456789,
        quiet=quiet,
    )

    app.create_hmm(observed_states=observed_states)

    return app


def test_ex2_application(ex2_application):
    hmm = ex2_application.hmm

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
            ("oA",): 0.009801000000000008,
            ("oB",): 0.00980100000000001,
            ("oC",): 0.00980100000000001,
        },
        ("a1",): {
            (): 0.009702989999999995,
            ("_unknown_",): 0.81358498,
            ("oA",): 9.801000000000005e-05,
            ("oB",): 0.08830700999999999,
            ("oC",): 0.08830700999999999,
        },
        ("a2",): {
            (): 0.09702989999999997,
            ("_unknown_",): 0.01793980000000006,
            ("oA",): 0.8830701,
            ("oB",): 0.0009801000000000007,
            ("oC",): 0.0009801000000000007,
        },
        ("a2", "a3"): {
            (): 0.009702989999999995,
            ("_unknown_",): 0.019703979999999954,
            ("oA",): 0.97039701,
            ("oB",): 9.801000000000005e-05,
            ("oC",): 9.801000000000005e-05,
        },
        ("a3",): {
            (): 0.09702989999999997,
            ("_unknown_",): 0.01793980000000006,
            ("oA",): 0.8830701,
            ("oB",): 0.0009801000000000007,
            ("oC",): 0.0009801000000000007,
        },
    }
    for i in E:
        assert E[i] == pytest.approx(tmp[i])


def test_ex1_application_write(ex1_application):
    baseline = os.path.join(currdir, "ex1_app_baseline.json")
    fname = os.path.join(currdir, "ex1_app_test.json")
    ex1_application.write(fname)
    tmp = pyutilib.misc.compare_file(fname, baseline, tolerance=1e-7)
    assert tmp[0] == False, f"Files differ:  diff {fname} {baseline}"
    os.remove(fname)


def test_ex1_application_read(ex1_application):
    app = PypmHMMApplication()
    baseline = os.path.join(currdir, "ex1_app_baseline.json")
    app.read(baseline)

    assert app.transition_params.start_probs == {(): 0.9, ("a1",): 0.1, ("a2",): 0.0}
    assert app.transition_params.transition_probs == {
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

    assert app.emission_params.false_emission == {"oA": 0.01, "oB": 0.01, "oC": 0.01}
    assert app.emission_params.true_positive == {
        ("a1", "oB"): 0.9,
        ("a1", "oC"): 0.9,
        ("a2", "oA"): 0.9,
    }

    hmm = app.hmm

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
            ("oA",): 0.009801000000000008,
            ("oB",): 0.00980100000000001,
            ("oC",): 0.00980100000000001,
        },
        ("a1",): {
            (): 0.009702989999999995,
            ("_unknown_",): 0.81358498,
            ("oA",): 9.801000000000005e-05,
            ("oB",): 0.08830700999999999,
            ("oC",): 0.08830700999999999,
        },
        ("a2",): {
            (): 0.09702989999999997,
            ("_unknown_",): 0.01793979999999995,
            ("oA",): 0.8830701,
            ("oB",): 0.0009801000000000007,
            ("oC",): 0.0009801000000000007,
        },
    }
    for i in E:
        assert E[i] == pytest.approx(tmp[i])
