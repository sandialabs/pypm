import pytest

from pypm.hmm.matrix import Sparse_Emissions_Matrix

# from pypm.util.load import load_process
# from pypm.util.run_simian import run_simian


@pytest.fixture
def mat1():
    return Sparse_Emissions_Matrix(
        true_positive=0.8,
        false_emission=0.1,
        hidden_states=[(), (1,), (2,), (1, 2)],
        observed_states=[("A",), ("B",), ("A", "B")],
    )


@pytest.fixture
def mat2():
    return Sparse_Emissions_Matrix(
        true_positive=0.8,
        false_emission=0.1,
        hidden_states=[(), ("a",), ("b",), ("a", "b")],
        observed_states=[("A",), ("B",), ("A", "B")],
    )


def test_mat1_bad_creation():
    with pytest.raises(AssertionError):
        Sparse_Emissions_Matrix(
            true_positive=0.9,
            false_emission=0.1,
            hidden_states=[(), (1,), (2,), (1, 2)],
        )


def test_mat2_bad_index(mat2):
    with pytest.raises(ValueError):
        assert mat2[("c"), ("A")] == 0.08999999999999998
    with pytest.raises(ValueError):
        assert mat2[("b"), ("C")] == 0.08999999999999998


def test_mat1_values(mat1):
    # (1-fe)*(1-fe)
    assert mat1[(), ()] == 0.81
    # (1-fe)*fe
    assert mat1[(), ("A",)] == pytest.approx(0.09)
    # (1-fe)*fe
    assert mat1[(), ("B",)] == pytest.approx(0.09)
    # fe*fe
    assert mat1[(), ("A", "B")] == pytest.approx(0.01)

    # (1-fe)*(1-tp) * (1-fe)*(1-tp)
    assert mat1[(1,), ()] == pytest.approx(0.0324)
    # (1-(1-fe)*(1-tp)) * (1-fe)*(1-tp)
    assert mat1[(1,), ("A")] == pytest.approx(0.1476)
    # (1-(1-fe)*(1-tp)) * (1-fe)*(1-tp)
    assert mat1[(1,), ("B")] == pytest.approx(0.1476)
    # (1-(1-fe)*(1-tp)) * (1-(1-fe)*(1-tp))
    assert mat1[(1,), ("A", "B")] == pytest.approx(0.6724)

    # (1-fe)*(1-tp)*(1-tp) * (1-fe)*(1-tp)*(1-tp)
    assert mat1[(1, 2), ()] == pytest.approx(0.001296)
    # (1-(1-fe)*(1-tp)*(1-tp)) * (1-fe)*(1-tp)*(1-tp)
    assert mat1[(1, 2), ("A")] == pytest.approx(0.034704)
    # (1-(1-fe)*(1-tp)*(1-tp)) * (1-fe)*(1-tp)*(1-tp)
    assert mat1[(1, 2), ("B")] == pytest.approx(0.034704)
    # (1-(1-fe)*(1-tp)*(1-tp)) * (1-(1-fe)*(1-tp)*(1-tp))
    assert mat1[(1, 2), ("A", "B")] == pytest.approx(0.929296)


def test_mat2_values(mat2):
    # (1-fe)*(1-fe)
    assert mat2[(), ()] == 0.81
    # (1-fe)*fe
    assert mat2[(), ("A",)] == pytest.approx(0.09)
    # (1-fe)*fe
    assert mat2[(), ("B",)] == pytest.approx(0.09)
    # fe*fe
    assert mat2[(), ("A", "B")] == pytest.approx(0.01)

    # (1-fe)*(1-tp) * (1-fe)*(1-tp)
    assert mat2[("a",), ()] == pytest.approx(0.0324)
    # (1-(1-fe)*(1-tp)) * (1-fe)*(1-tp)
    assert mat2[("a",), ("A")] == pytest.approx(0.1476)
    # (1-(1-fe)*(1-tp)) * (1-fe)*(1-tp)
    assert mat2[("a",), ("B")] == pytest.approx(0.1476)
    # (1-(1-fe)*(1-tp)) * (1-(1-fe)*(1-tp))
    assert mat2[("a",), ("A", "B")] == pytest.approx(0.6724)

    # (1-fe)*(1-tp)*(1-tp) * (1-fe)*(1-tp)*(1-tp)
    assert mat2[("a", "b"), ()] == pytest.approx(0.001296)
    # (1-(1-fe)*(1-tp)*(1-tp)) * (1-fe)*(1-tp)*(1-tp)
    assert mat2[("a", "b"), ("A")] == pytest.approx(0.034704)
    # (1-(1-fe)*(1-tp)*(1-tp)) * (1-fe)*(1-tp)*(1-tp)
    assert mat2[("a", "b"), ("B")] == pytest.approx(0.034704)
    # (1-(1-fe)*(1-tp)*(1-tp)) * (1-(1-fe)*(1-tp)*(1-tp))
    assert mat2[("a", "b"), ("A", "B")] == pytest.approx(0.929296)


def Xtest_mat1_iter(mat1):
    assert list(x for x in mat1) == [
        ((), ("A",)),
        ((), ("B",)),
        ((), ("A", "B")),
        ((1,), ("A",)),
        ((1,), ("B",)),
        ((1,), ("A", "B")),
        ((2,), ("A",)),
        ((2,), ("B",)),
        ((2,), ("A", "B")),
        ((1, 2), ("A",)),
        ((1, 2), ("B",)),
        ((1, 2), ("A", "B")),
    ]
