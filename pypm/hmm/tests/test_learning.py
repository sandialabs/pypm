import pytest
import os
import munch

from pypm.util.fileutils import this_file_dir
from pypm.util.load import load_process

from pypm.hmm.hmm_application import PypmHMMApplication

from pypm.hmm.tests import examples

quiet = True
num_simulations = 10


def config(**kwds):
    return munch.DefaultMunch(None, **kwds)


def run(*, name, observed, features, known_process_features, constrained, debug=False):
    pm = load_process(data=getattr(examples, name))
    app = PypmHMMApplication()

    app.initialize(
        config(pm=pm, known_process_features=known_process_features, features=features)
    )

    app.learn_transition_parameters(
        num_simulations=num_simulations,
        num_time_steps=20,
        max_delay_before=5,
        seed=123456789,
        quiet=quiet,
    )

    app.learn_emission_parameters(
        observed=observed, constrained=constrained, debug=debug
    )

    observed_states = {o for o in observed}
    app.create_hmm(observed_states=observed_states)

    mat = app.hmm.emission_mat
    return munch.Munch(
        true_positive=app.emission_params.true_positive,
        false_emission=app.emission_params.false_emission,
        E={
            h: {o: mat[i][j] for j, o in enumerate(app.hmm.observed_states)}
            for i, h in enumerate(app.hmm.hidden_states)
        },
    )


def ex1_app(observed, constrained, debug=False):
    name = "ex1"
    features = {"oA", "oB", "oC"}
    known_process_features = dict(a1={"oB", "oC"}, a2={"oA"})
    return run(
        name=name,
        observed=observed,
        features=features,
        known_process_features=known_process_features,
        constrained=constrained,
        debug=debug,
    )


def test1():
    obs = [ (), (), (), ("oC",), ("oB",), ("oB",), ("oB",), (), (), ("oA",), ("oA",), ]  # fmt: skip
    ans = ex1_app(obs, False, debug=False)
    assert ans.true_positive == pytest.approx(
        {
            ("a1", "oC"): 0.25,
            ("a1", "oB"): 0.75,
            ("a2", "oA"): 1.0,
        }
    )
    assert ans.false_emission == {"oC": 0.0, "oA": 0.0, "oB": 0.0}


def test2():
    obs = [ (), (), (), ("oB",), ("oB",), ("oB",), ("oB",), (), (), ("oA",), ("oA",), ]  # fmt: skip
    ans = ex1_app(obs, False, debug=False)
    assert ans.true_positive == pytest.approx(
        {
            ("a1", "oC"): 0.0,
            ("a1", "oB"): 1.0,
            ("a2", "oA"): 1.0,
        }
    )
    assert ans.false_emission == {"oC": 0.0, "oA": 0.0, "oB": 0.0}


def test3():
    obs = [ ("oB",), ("oB",), ("oB",), ("oB",), ("oA",), ("oA",), ("oA",), ("oA",), ("oA",), ]  # fmt: skip
    ans = ex1_app(obs, False, debug=False)
    assert ans.true_positive == pytest.approx(
        {
            ("a1", "oC"): 0.0,
            ("a1", "oB"): 1.0,
            ("a2", "oA"): 1.0,
        }
    )
    assert ans.false_emission == {"oC": 0.0, "oA": 0.0, "oB": 0.0}


def test4():
    obs = [ ("oC",), ("oC",), ("oC",), ("oC",), ("oA",), ("oA",), ("oA",), ("oA",), ("oA",), ]  # fmt: skip
    ans = ex1_app(obs, False, debug=False)
    assert ans.true_positive == pytest.approx(
        {
            ("a1", "oC"): 1.0,
            ("a1", "oB"): 0.0,
            ("a2", "oA"): 1.0,
        }
    )
    assert ans.false_emission == {"oC": 0.0, "oA": 0.0, "oB": 0.0}


def test5():
    obs = [ ("oB",), ("oC",), ("oC",), ("oC",), ("oA",), ("oA",), ("oA",), ("oA",), ("oA",), ]  # fmt: skip
    ans = ex1_app(obs, False, debug=False)
    assert ans.true_positive == pytest.approx(
        {
            ("a1", "oC"): 0.75,
            ("a1", "oB"): 0.25,
            ("a2", "oA"): 1.0,
        }
    )
    assert ans.false_emission == {"oC": 0.0, "oA": 0.0, "oB": 0.0}


def test6():
    obs = [ ("oC", "oB"), ("oC", "oB"), ("oC", "oB"), ("oC", "oB"), ("oA",), ("oA",), ("oA",), ("oA",), ("oA",), ]  # fmt: skip
    ans = ex1_app(obs, False, debug=False)
    assert ans.true_positive == pytest.approx(
        {
            ("a1", "oC"): 1.0,
            ("a1", "oB"): 1.0,
            ("a2", "oA"): 1.0,
        }
    )
    assert ans.false_emission == {"oC": 0.0, "oA": 0.0, "oB": 0.0}


def test7():
    obs = [ ("oC", "oB"), ("oC",), ("oC",), ("oC",), ("oA",), ("oA",), ("oA",), ("oA",), ("oA",), ]  # fmt: skip
    ans = ex1_app(obs, False, debug=False)
    assert ans.true_positive == pytest.approx(
        {
            ("a1", "oC"): 1.0,
            ("a1", "oB"): 0.25,
            ("a2", "oA"): 1.0,
        }
    )
    assert ans.false_emission == {"oC": 0.0, "oA": 0.0, "oB": 0.0}


def test8():
    obs = [ (), (), (), ("oC",), ("oB",), ("oB",), ("oB",), (), (), ("oA",), ("oA",), (), (), ]  # fmt: skip
    ans = ex1_app(obs, False, debug=False)
    assert ans.true_positive == pytest.approx(
        {
            ("a1", "oC"): 0.25,
            ("a1", "oB"): 0.75,
            ("a2", "oA"): 1.0,
        }
    )
    assert ans.false_emission == {"oC": 0.0, "oA": 0.0, "oB": 0.0}


def test9():
    obs = [ (), (), (), ("oC",), ("oB",), ("oB",), ("oB",), (), (), ("oA",), ("oA",), (), (), ]  # fmt: skip
    ans = ex1_app(obs, True, debug=False)
    assert ans.true_positive == pytest.approx(
        {
            ("a1", "oB"): 0.75,
            ("a1", "oC"): 0.25,
            ("a2", "oA"): 0.50,
        }
    )
    assert ans.false_emission == {"oC": 0.0, "oA": 0.0, "oB": 0.0}


def test10():
    obs = [ (), (), (), ("oC",), ("oB",), ("oB",), ("oB",), (), (), ("oA",), ("oA",), ]  # fmt: skip
    ans = ex1_app(obs, True, debug=False)
    assert ans.true_positive == pytest.approx(
        {
            ("a1", "oB"): 0.750000002116943,
            ("a1", "oC"): 0.2500000076041971,
            ("a2", "oA"): 1.0,
        }
    )
    assert ans.false_emission == {"oC": 0.0, "oA": 0.0, "oB": 0.0}
