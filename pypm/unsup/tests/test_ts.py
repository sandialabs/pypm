import math
import random
from pypm.unsup.tabu_search import CachedTabuSearch


class Search(CachedTabuSearch):
    def __init__(self, pm=None, data=None, nresources=None, nfeatures=None):
        CachedTabuSearch.__init__(self)
        if pm is not None:
            self.pm = pm
            self.nresources = len(pm.resources)
            self.nfeatures = len(data)
        else:
            self.nresources = nresources
            self.nfeatures = nfeatures
        #
        self.tabu_tenure = round(0.25 * self.nfeatures) + 1

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

    def compute_solution_value(self, point):
        return sum((i + 1) * (1 + math.sin(i / 10.0)) for i in point)


def test_ts():
    random.seed(39483098)
    ls = Search(nresources=6, nfeatures=7)
    ls.max_iterations = 100
    ls.tabu_tenure = 4
    x, f = ls.run()

    assert f == 7.0
    assert x == (0, 0, 0, 0, 0, 0, 0)
