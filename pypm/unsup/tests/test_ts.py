import math
import random
from pypm.unsup.tabu_search import TabuSearch, CachedTabuSearch, TabuSearchProblem


class LabelSearchProblem(TabuSearchProblem):
    def __init__(self, pm=None, data=None, nresources=None, nfeatures=None):
        TabuSearchProblem.__init__(self)
        if pm is not None:
            self.pm = pm
            self.nresources = len(pm.resources)
            self.nfeatures = len(data)
        else:
            self.nresources = nresources
            self.nfeatures = nfeatures

    def initial_solution(self):
        # Each feature is randomly labeled as a resource
        point = []
        for i in range(self.nfeatures):
            point.append(random.randint(0, self.nresources - 1))
        return tuple(point)

    def moves(self, point, _):
        # Generate moves in the neighborhood
        rorder = list(range(self.nresources))
        random.shuffle(rorder)
        features = list(range(self.nfeatures))
        random.shuffle(features)

        for i in features:
            j = rorder.index(point[i])
            nhbr = list(point)

            nhbr[i] = rorder[j - 1]
            yield tuple(nhbr), (i, rorder[j - 1]), None

            nhbr[i] = rorder[(j + 1) % self.nresources]
            yield tuple(nhbr), (i, rorder[(j + 1) % self.nresources]), None

    def compute_results(self, point):
        # This is a dummy value used to test this searcher
        return sum((i + 1) * (1 + math.sin(i / 10.0)) for i in point), None


class LabelSearch(TabuSearch):
    def __init__(self, pm=None, data=None, nresources=None, nfeatures=None):
        TabuSearch.__init__(self)
        self.problem = LabelSearchProblem(
            pm=pm, data=data, nresources=nresources, nfeatures=nfeatures
        )


class CachedLabelSearch(CachedTabuSearch):
    def __init__(self, pm=None, data=None, nresources=None, nfeatures=None):
        CachedTabuSearch.__init__(self)
        self.problem = LabelSearchProblem(
            pm=pm, data=data, nresources=nresources, nfeatures=nfeatures
        )


def test_ts_first_improving():
    random.seed(39483098)
    ls = LabelSearch(nresources=6, nfeatures=7)
    ls.max_iterations = 100
    ls.options.tabu_tenure = 4
    # ls.options.verbose=True
    # ls.options.quiet=False
    x, f = ls.run()

    assert f == 7.0
    assert x == (0, 0, 0, 0, 0, 0, 0)


def test_ts_best_improving():
    random.seed(39483098)
    ls = LabelSearch(nresources=6, nfeatures=7)
    ls.max_iterations = 100
    ls.options.tabu_tenure = 4
    ls.options.search_strategy = "best_improving"
    # ls.options.verbose=True
    # ls.options.quiet=False
    x, f = ls.run()

    assert f == 7.0
    assert x == (0, 0, 0, 0, 0, 0, 0)


def test_cachedts_first_improving():
    random.seed(39483098)
    ls = CachedLabelSearch(nresources=6, nfeatures=7)
    ls.max_iterations = 100
    ls.options.tabu_tenure = 4
    # ls.options.verbose=True
    # ls.options.quiet=False
    x, f = ls.run()

    assert f == 7.0
    assert x == (0, 0, 0, 0, 0, 0, 0)
    assert len(ls.cache) == 264


def test_cachedts_best_improving():
    random.seed(39483098)
    ls = CachedLabelSearch(nresources=6, nfeatures=7)
    ls.max_iterations = 100
    ls.options.tabu_tenure = 4
    ls.options.search_strategy = "best_improving"
    # ls.options.verbose=True
    # ls.options.quiet=False
    x, f = ls.run()

    assert f == 7.0
    assert x == (0, 0, 0, 0, 0, 0, 0)
    assert len(ls.cache) == 392


if __name__ == "__main__":  # pragma: no cover
    random.seed(39483098)
    ls = LabelSearch(nresources=6, nfeatures=7)
    ls.options.max_iterations = 100
    ls.options.tabu_tenure = 4
    # ls.options.verbose=True
    # ls.options.quiet=False
    ls.run()

    random.seed(39483098)
    ls = LabelSearch(nresources=6, nfeatures=7)
    ls.options.max_iterations = 100
    ls.options.tabu_tenure = 4
    ls.options.search_strategy = "best_improving"
    # ls.options.verbose=True
    # ls.options.quiet=False
    ls.run()

    random.seed(39483098)
    ls = CachedLabelSearch(nresources=6, nfeatures=7)
    ls.max_iterations = 100
    ls.options.tabu_tenure = 4
    # ls.options.verbose=True
    # ls.options.quiet=False
    x, f = ls.run()

    random.seed(39483098)
    ls = CachedLabelSearch(nresources=6, nfeatures=7)
    ls.max_iterations = 100
    ls.options.tabu_tenure = 4
    ls.options.search_strategy = "best_improving"
    # ls.options.verbose=True
    # ls.options.quiet=False
    x, f = ls.run()
