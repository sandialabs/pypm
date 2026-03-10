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


def run(
    *,
    name,
    observed,
    features,
    known_process_features=None,
    constrained,
    debug=False,
    schedule_all_activities=True,
):
    pm = load_process(data=getattr(examples, name))
    app = PypmHMMApplication()

    app.initialize(
        config(pm=pm, known_process_features=known_process_features, features=features)
    )

    app.learn_transition_parameters(
        num_simulations=num_simulations,
        seed=123456789,
        quiet=quiet,
    )

    app.learn_emission_parameters(
        observed=observed,
        constrained=constrained,
        schedule_all_activities=schedule_all_activities,
        debug=debug,
        false_emission_probability=1e-3,
        seed=123456789,
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


def ex7_app(observed, constrained, debug=False, schedule_all_activities=True):
    name = "ex7"
    features = {"oA"}
    return run(
        name=name,
        observed=observed,
        features=features,
        constrained=constrained,
        schedule_all_activities=schedule_all_activities,
        debug=debug,
    )


def test1():
    obs = [ (), (), (), ("oC",), ("oB",), ("oB",), ("oB",), (), (), ("oA",), ("oA",), ]  # fmt: skip
    ans = ex1_app(obs, False, debug=False)
    assert ans.false_emission == {"oB": 0.001, "oC": 0.001, "oA": 0.001}
    assert ans.true_positive == pytest.approx(
        {
            ("a1", "oB"): 0.7497497494361838,
            ("a1", "oC"): 0.24924924956491418,
            ("a2", "oA"): 1.0,
        },
        abs=1e-3,
    )


def test2():
    obs = [ (), (), (), ("oB",), ("oB",), ("oB",), ("oB",), (), (), ("oA",), ("oA",), ]  # fmt: skip
    ans = ex1_app(obs, False, debug=False)
    assert ans.false_emission == {"oB": 0.001, "oC": 0.001, "oA": 0.001}
    assert ans.true_positive == pytest.approx(
        {("a1", "oC"): 0.0, ("a1", "oB"): 1.0, ("a2", "oA"): 1.0},
        abs=1e-3,
    )


def test3():
    obs = [ ("oB",), ("oB",), ("oB",), ("oB",), ("oA",), ("oA",), ("oA",), ("oA",), ("oA",), ]  # fmt: skip
    ans = ex1_app(obs, False, debug=False)
    assert ans.false_emission == {"oB": 0.001, "oC": 0.001, "oA": 0.001}
    assert ans.true_positive == pytest.approx(
        {("a1", "oC"): 0.0, ("a1", "oB"): 1.0, ("a2", "oA"): 1.0}, abs=1e-3
    )


def test4():
    obs = [ ("oC",), ("oC",), ("oC",), ("oC",), ("oA",), ("oA",), ("oA",), ("oA",), ("oA",), ]  # fmt: skip
    ans = ex1_app(obs, False, debug=False)
    assert ans.false_emission == {"oB": 0.001, "oC": 0.001, "oA": 0.001}
    assert ans.true_positive == pytest.approx(
        {("a1", "oC"): 1.0, ("a1", "oB"): 0.0, ("a2", "oA"): 1.0}, abs=1e-3
    )


def test5():
    obs = [ ("oB",), ("oC",), ("oC",), ("oC",), ("oA",), ("oA",), ("oA",), ("oA",), ("oA",), ]  # fmt: skip
    ans = ex1_app(obs, False, debug=False)
    assert ans.false_emission == {"oB": 0.001, "oC": 0.001, "oA": 0.001}
    assert ans.true_positive == pytest.approx(
        {
            ("a1", "oC"): 0.7497497494361861,
            ("a1", "oB"): 0.24924924956491606,
            ("a2", "oA"): 1.0,
        },
        abs=1e-3,
    )


def test6():
    obs = [ ("oC", "oB"), ("oC", "oB"), ("oC", "oB"), ("oC", "oB"), ("oA",), ("oA",), ("oA",), ("oA",), ("oA",), ]  # fmt: skip
    ans = ex1_app(obs, False, debug=False)
    assert ans.false_emission == {"oB": 0.001, "oC": 0.001, "oA": 0.001}
    assert ans.true_positive == pytest.approx(
        {("a1", "oC"): 1.0, ("a1", "oB"): 1.0, ("a2", "oA"): 1.0}, abs=1e-3
    )


def test7():
    obs = [ ("oC", "oB"), ("oC",), ("oC",), ("oC",), ("oA",), ("oA",), ("oA",), ("oA",), ("oA",), ]  # fmt: skip
    ans = ex1_app(obs, False, debug=False)
    assert ans.false_emission == {"oB": 0.001, "oC": 0.001, "oA": 0.001}
    assert ans.true_positive == pytest.approx(
        {("a1", "oC"): 1.0, ("a1", "oB"): 0.24924924956491612, ("a2", "oA"): 1.0},
        abs=1e-3,
    )


def test8():
    obs = [ (), (), (), ("oC",), ("oB",), ("oB",), ("oB",), (), (), ("oA",), ("oA",), (), (), ]  # fmt: skip
    ans = ex1_app(obs, False, debug=False)
    assert ans.false_emission == {"oB": 0.001, "oC": 0.001, "oA": 0.001}
    assert ans.true_positive == pytest.approx(
        {
            ("a1", "oB"): 0.7497497494361838,
            ("a1", "oC"): 0.24924924956491418,
            ("a2", "oA"): 1.0,
        },
        abs=1e-3,
    )


def test9():
    obs = [ (), (), (), ("oC",), ("oB",), ("oB",), ("oB",), (), (), ("oA",), ("oA",), (), (), ]  # fmt: skip
    ans = ex1_app(obs, True, debug=False)
    assert ans.false_emission == {"oB": 0.001, "oC": 0.001, "oA": 0.001}
    assert ans.true_positive == pytest.approx(
        {
            ("a1", "oC"): 0.24924924956490946,
            ("a1", "oB"): 0.7497497494361829,
            ("a2", "oA"): 0.49949949950012884,
        },
        abs=1e-3,
    )


def test10():
    obs = [("oA",)] * 50
    ans = ex7_app(obs, True, debug=False)
    assert ans.false_emission == {"oA": 0.001}
    assert ans.true_positive == {
        ("a1", "oA"): 1.0,
        ("a2", "oA"): 1.0,
        ("a3", "oA"): 1.0,
        ("a4", "oA"): 1.0,
        ("a5", "oA"): 1.0,
        ("a6", "oA"): 1.0,
    }


def test11():
    obs = [("oA",)] * 20
    ans = ex7_app(obs, True, debug=False, schedule_all_activities=False)
    assert ans.false_emission == {"oA": 0.001}
    assert ans.true_positive == pytest.approx({
        ("a1", "oA"): 1.0,
        ("a2", "oA"): 1.0,
        ("a3", "oA"): 1.0,
        ("a4", "oA"): 1.0,
        ("a5", "oA"): 1.0,
        ("a6", "oA"): 1.0,
    })
