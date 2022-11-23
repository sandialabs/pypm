#
# Iteratively label data with TABU search
#
import copy
import random
from munch import Munch
from .tabu_search import CachedTabuSearch, TabuSearchProblem
from .parallel_tabu_search import RayTabuSearchProblem


class PMLabelSearchProblem(TabuSearchProblem):
    def __init__(
        self, *, config=None, nresources=None, nfeatures=None, constraints=None
    ):
        TabuSearchProblem.__init__(self)
        self.rng = random.Random(config.seed)
        self.config = config
        #
        self.nresources = len(config.pm.resources) + 1
        self.resources = list(sorted(k for k in self.config.pm.resources)) + ["IGNORED"]
        self.nfeatures = len(config.obs["observations"])
        self.features = list(sorted(config.obs["observations"].keys()))
        #
        # Solution representations:
        #   Standard
        #       x_i = resource_id
        #       Each resource can only be associated with a single feature
        #
        #   Combine_Features
        #       x_i = resource_id
        #       When multiple x_i point to the same resource, these features
        #           are combined with max()
        #
        self.combine_features = self.config.options.get("combine_features", False)
        self.penalize_features = self.config.options.get("penalize_features", False)
        #
        # Setup MIP solver, using a clone of the config without observation data (config.obs)
        #
        from pypm.api import PYPM

        self.mip_sup = PYPM.supervised_mip()
        obs = config.obs
        config.obs = None
        self.mip_sup.config = copy.deepcopy(config)
        self.mip_sup.config.search_strategy = "mip"
        self.mip_sup.config.model = config.options.get("tabu_model", "GSF-ED")
        self.mip_sup.config.verbose = False
        self.mip_sup.config.quiet = True
        if constraints:
            self.mip_sup.add_constraints(constraints)
        config.obs = obs

    def initial_solution(self):
        if self.combine_features:
            #
            # Each feature is randomly labeled as a resource
            #
            point = []
            for i in range(self.nfeatures):
                point.append(self.rng.randint(0, self.nresources - 1))
        else:
            #
            # Each resource is associated with a unique feature
            #
            tmp = list(range(self.nresources - 1))
            self.rng.shuffle(tmp)
            if self.nfeatures < self.nresources:
                point = [None] * self.nfeatures
                for i in range(self.nfeatures):
                    point[i] = tmp[i]
            else:
                point = [self.nresources - 1] * self.nfeatures
                for i in range(self.nresources - 1):
                    point[tmp[i]] = i
            self.rng.shuffle(point)
        #
        return tuple(point)

    def moves(self, point, _):
        #
        # Generate moves in the neighborhood
        #
        if self.combine_features:
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

        else:
            # tmp[i] is the feature that points to resource j, or None
            tmp = [None] * self.nresources
            for i in range(self.nfeatures):
                tmp[point[i]] = i
            # The last resource is 'Ignore', which multiple features can point to
            tmp[self.nresources - 1] = None

            unique = set()
            for k in range(0, int(max(1.0, self.nfeatures / self.nresources))):
                for i in range(self.nfeatures):
                    flag = True
                    while flag:  # Iterate until we generate have a new move
                        nhbr = list(point)
                        j = nhbr[i]
                        while j == nhbr[i]:
                            j = self.rng.randint(0, self.nresources - 1)
                        if tmp[j] is None:
                            point_i = nhbr[i]
                            nhbr[i] = j
                            move = tuple(nhbr), (i, j, i, point_i), None
                        else:
                            point_i = nhbr[i]
                            nhbr[i] = j
                            nhbr[tmp[j]] = point_i
                            if i < tmp[j]:
                                move = tuple(nhbr), (i, j, tmp[j], point_i), None
                            else:
                                move = tuple(nhbr), (tmp[j], point_i, i, j), None
                        if move[0] not in unique:
                            flag = False
                            unique.add(move[0])
                            yield move

    def compute_results(self, point):
        #
        # Create labeled observations
        #
        # Take the max value across all features associated with a resource in the
        # current point.
        #
        observations = {k: [0] * self.config.obs.timesteps for k in self.resources}
        for index, i in enumerate(self.features):
            k = self.resources[point[index]]
            if k == len(self.resources) - 1:
                # The last category of resources is ignored
                continue
            for t in range(self.config.obs.timesteps):
                observations[k][t] = max(
                    observations[k][t], self.config.obs["observations"][i][t]
                )
        #
        # Setup the configuration object to use these observations
        #
        self.mip_sup.config.obs = Munch(
            observations=observations,
            header="None",
            timesteps=self.config.obs.timesteps,
            datetime=self.config.obs.datetime,
        )
        #
        # Execute the mip
        #
        results = self.mip_sup.generate_schedule()
        #
        # Cache representation of the current solution
        #
        point_ = {
            i: self.resources[point[index]] for index, i in enumerate(self.features)
        }
        results["point_"] = point_
        #
        if self.penalize_features:
            #
            # Count # of ignored features
            #
            nignored = 0
            for val in point:
                if val == self.nresources - 1:
                    nignored += 1
            value = (
                -results["results"][0]["goals"]["total_separation"]
                - nignored / self.nfeatures
            )
        else:
            value = -results["results"][0]["goals"]["total_separation"]

        return value, results


class PMLabelSearch(CachedTabuSearch):
    def __init__(
        self, *, config=None, nresources=None, nfeatures=None, constraints=None, nworkers=1
    ):
        CachedTabuSearch.__init__(self)
        self.problem = PMLabelSearchProblem(
            config=config,
            nresources=nresources,
            nfeatures=nfeatures,
            constraints=constraints,
        )
        if nworkers > 1:
            self.problem = RayTabuSearchProblem(self.problem, nworkers=nworkers)
        #
        self.options.verbose = config.options.get("verbose", False)
        if "max_stall_count" in config.options:
            self.options.max_stall_count = config.options.get("max_stall_count")
        self.options.tabu_tenure = round(0.25 * self.problem.nfeatures) + 1

