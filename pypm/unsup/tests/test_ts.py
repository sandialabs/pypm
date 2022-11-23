import json
import glob
import shutil
import math
import random
import os
from pypm.unsup.tabu_search import TabuSearch, CachedTabuSearch, TabuSearchProblem
import ray
from pypm.unsup.parallel_tabu_search import RayTabuSearchProblem
from pypm.util.fileutils import this_file_dir

currdir = this_file_dir()


class LabelSearchProblem(TabuSearchProblem):
    def __init__(self, pm=None, data=None, nresources=None, nfeatures=None, seed=None):
        TabuSearchProblem.__init__(self)
        self.rng = random.Random(seed)
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
            point.append(self.rng.randint(0, self.nresources - 1))
        return tuple(point)

    def moves(self, point, _):
        # Generate moves in the neighborhood
        rorder = list(range(self.nresources))
        self.rng.shuffle(rorder)
        features = list(range(self.nfeatures))
        self.rng.shuffle(features)

        for i in features:
            j = rorder.index(point[i])
            nhbr = list(point)

            nhbr[i] = rorder[j - 1]
            yield tuple(nhbr), (i, rorder[j - 1]), None

            nhbr[i] = rorder[(j + 1) % self.nresources]
            yield tuple(nhbr), (i, rorder[(j + 1) % self.nresources]), None

    def compute_results(self, point):
        # This objective is minimized
        return sum((i + 1) * (1 + math.sin(i / 10.0)) for i in point), None


class LabelSearch(TabuSearch):
    def __init__(
        self, pm=None, data=None, nresources=None, nfeatures=None, nworkers=1, seed=None
    ):
        TabuSearch.__init__(self)
        self.problem = LabelSearchProblem(
            pm=pm, data=data, nresources=nresources, nfeatures=nfeatures, seed=seed
        )
        if nworkers > 1:
            self.problem = RayTabuSearchProblem(problem=self.problem, nworkers=nworkers)


class CachedLabelSearch(CachedTabuSearch):
    def __init__(
        self, pm=None, data=None, nresources=None, nfeatures=None, nworkers=1, seed=None
    ):
        CachedTabuSearch.__init__(self)
        self.problem = LabelSearchProblem(
            pm=pm, data=data, nresources=nresources, nfeatures=nfeatures, seed=seed
        )
        if nworkers > 1:
            self.problem = RayTabuSearchProblem(problem=self.problem, nworkers=nworkers)


def test_ts_first_improving():
    ls = LabelSearch(nresources=6, nfeatures=7, seed=39483098)
    ls.max_iterations = 100
    ls.options.tabu_tenure = 4
    # ls.options.verbose=True
    # ls.options.quiet=False
    x, f = ls.run()

    assert f == 7.0
    assert x == (0, 0, 0, 0, 0, 0, 0)


def test_ts_best_improving():
    ls = LabelSearch(nresources=6, nfeatures=7, seed=39483098)
    ls.max_iterations = 100
    ls.options.tabu_tenure = 4
    ls.options.search_strategy = "best_improving"
    # ls.options.verbose=True
    # ls.options.quiet=False
    x, f = ls.run()

    assert f == 7.0
    assert x == (0, 0, 0, 0, 0, 0, 0)


def test_cachedts_first_improving():
    ls = CachedLabelSearch(nresources=6, nfeatures=7, seed=39483098)
    ls.max_iterations = 100
    ls.options.tabu_tenure = 4
    # ls.options.verbose=True
    # ls.options.quiet=False
    x, f = ls.run()

    assert f == 7.0
    assert x == (0, 0, 0, 0, 0, 0, 0)
    assert len(ls.cache) == 264


def test_cachedts_best_improving():
    ls = CachedLabelSearch(nresources=6, nfeatures=7, seed=39483098)
    ls.max_iterations = 100
    ls.options.tabu_tenure = 4
    ls.options.search_strategy = "best_improving"
    # ls.options.verbose=True
    # ls.options.quiet=False
    x, f = ls.run()

    assert f == 7.0
    assert x == (0, 0, 0, 0, 0, 0, 0)
    assert len(ls.cache) == 392


def test_ts_checkpoint():
    ls = LabelSearch(nresources=6, nfeatures=7, seed=39483098)
    ls.max_iterations = 100
    ls.options.tabu_tenure = 4

    checkpoint_dir = os.path.join(currdir, "checkpoints")
    if os.path.exists(checkpoint_dir):
        shutil.rmtree(checkpoint_dir)
    os.mkdir(checkpoint_dir)
    ls.options.checkpoint_file_template = os.path.join(checkpoint_dir, "point_{}.json")
    # ls.options.verbose=True
    # ls.options.quiet=False
    x, f = ls.run()

    values = {}
    points = {}
    for fname in glob.glob(os.path.join(checkpoint_dir, "*.json")):
        with open(fname, "r") as INPUT:
            data = json.load(INPUT)
            values[data["iteration"]] = data["value"]
            points[data["iteration"]] = data["point"]

    values_baseline = {
        0: 28.04632486871978,
        16: 9.399333666587314,
        1: 25.06391087536808,
        21: 8.199666833293657,
        22: 7.0,
        2: 23.864244042074425,
        3: 22.467902882982898,
        4: 21.07156172389137,
        5: 19.675220564799844,
        6: 14.394675325559811,
        7: 11.798667333174627,
        8: 10.59900049988097,
    }
    points_baseline = {
        0: [3, 0, 1, 2, 5, 2, 2],
        16: [0, 0, 0, 1, 0, 1, 0],
        1: [1, 0, 1, 2, 5, 2, 2],
        21: [0, 0, 0, 1, 0, 0, 0],
        22: [0, 0, 0, 0, 0, 0, 0],
        2: [0, 0, 1, 2, 5, 2, 2],
        3: [0, 0, 1, 2, 5, 1, 2],
        4: [0, 0, 1, 1, 5, 1, 2],
        5: [0, 0, 1, 1, 5, 1, 1],
        6: [0, 0, 1, 1, 2, 1, 1],
        7: [0, 0, 1, 1, 0, 1, 1],
        8: [0, 0, 0, 1, 0, 1, 1],
    }
    assert values == values_baseline
    assert points == points_baseline

    if os.path.exists(checkpoint_dir):
        shutil.rmtree(checkpoint_dir)


if __name__ == "__main__":  # pragma: no cover
    ray.init(num_cpus=4)
    ls = CachedLabelSearch(nresources=6, nfeatures=7, seed=39483098, nworkers=3)
    # ls = CachedLabelSearch(nresources=6, nfeatures=7, seed=39483098)
    ls.options.max_iterations = 100
    ls.options.tabu_tenure = 4
    ls.options.search_strategy = "best_improving"
    # ls.options.verbose=True
    # ls.options.quiet=False
    ls.run()
