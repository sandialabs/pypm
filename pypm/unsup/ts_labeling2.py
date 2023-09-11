#
# Iteratively label data with TABU search
#
import time
import copy
import random
import json
import pprint
import sys
from munch import Munch
from .tabu_search import CachedTabuSearch, TabuSearchProblem
from .parallel_tabu_search import RayTabuSearchProblem


class hdict(dict):
    def __hash__(self):
        return hash((frozenset(self), frozenset(self.values())))

    def __le__(self, other):
        for k in sorted(self.keys()):
            v = self[k]
            v_ = other[k]
            if v > v_:
                return False
        return True

    def __eq__(self, other):
        for k in self.keys():
            v = self[k]
            v_ = other[k]
            if v != v_:
                return False
        return True

    def __lt__(self, other):
        for k in sorted(self.keys()):
            v = self[k]
            v_ = other[k]
            if v > v_:
                return False
            elif v < v_:
                return True
        return False


class PMLabelSearchProblem_Restricted(TabuSearchProblem):
    def __init__(
        self,
        *,
        config=None,
        nresources=None,
        nfeatures=None,
        constraints=None,
        labeling_restrictions=None
    ):
        TabuSearchProblem.__init__(self)
        self.rng = random.Random(config.seed)
        self.config = config
        #
        self.nresources = len(config.pm.resources)
        self.resources = list(sorted(k for k in self.config.pm.resources))
        self.nfeatures = len(config.obs["observations"])
        self.features = list(sorted(config.obs["observations"].keys()))
        if labeling_restrictions is not None:
            self.labeling_restrictions = labeling_restrictions
        else:
            self.labeling_restrictions = {
                i: {"optional": self.features, "required": []} for i in self.resources
            }
        #
        # Solution representations:
        #   Standard
        #       x_ij = 1 if feature i is associated with resource j
        #       When multiple features are associated a resource, these features
        #           are combined with max()
        #
        #
        # Setup MIP solver, using a clone of the config without observation data (config.obs)
        #
        from pypm.api import PYPM

        self.mip_sup = PYPM.supervised_mip()
        obs = config.obs
        config.obs = None
        self.mip_sup.config = copy.deepcopy(config)
        self.mip_sup.config.search_strategy = "mip"
        self.mip_sup.config.model = config.options.get(
            "tabu_model", "UnrestrictedMatches_VariableLengthActivities"
        )
        self.mip_sup.config.verbose = False
        self.mip_sup.config.quiet = True
        if constraints:
            self.mip_sup.add_constraints(constraints)
        config.obs = obs

    def initial_solution(self):
        point = hdict()
        ctr = 0
        mv = 0
        for i in self.resources:
            if i not in self.labeling_restrictions:
                print(
                    "WARNING: Ignoring resource '{}'.\tResource is not including in labeling restrictions".format(
                        i
                    )
                )
                continue
            if (
                len(self.labeling_restrictions[i]["optional"])
                + len(self.labeling_restrictions[i]["required"])
                == 0
            ):
                print(
                    "WARNING: Ignoring resource '{}'.\tResource has no optional or required features specified".format(
                        i
                    )
                )
                continue
            point[i] = hdict()
            for j in self.labeling_restrictions[i]["optional"]:
                point[i][j] = self.rng.randint(0, 1)
                ctr += 1
            mv += len(self.labeling_restrictions[i]["optional"]) > 0
            for j in self.labeling_restrictions[i]["required"]:
                point[i][j] = 1
        print(
            "SUMMARY: TABU search is optimizing an {}-dimensional binary space.  Each iteration will generate {} local moves.".format(
                ctr, mv
            )
        )
        return point

    def moves(self, point, _):
        #
        # Generate moves in the neighborhood
        #
        rorder = list(range(self.nresources))
        self.rng.shuffle(rorder)
        for i_ in rorder:
            i = self.resources[i_]
            if i not in self.labeling_restrictions:
                continue
            if len(self.labeling_restrictions[i]["optional"]) == 0:
                continue
            j = self.rng.choice(list(self.labeling_restrictions[i]["optional"]))
            nhbr = copy.deepcopy(point)
            nhbr[i][j] = 1 - nhbr[i][j]
            yield nhbr, (i, j, point[i][j]), None

    def compute_results(self, point):
        #
        # Create labeled observations
        #
        # Take the max value across all features associated with a resource in the
        # current point.
        #
        observations = {k: [0] * self.config.obs.timesteps for k in self.resources}
        for index, i in enumerate(self.features):
            for k in point:
                if point[k].get(i, 0):
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
        # self.mip_sup.config.verbose=True
        # self.mip_sup.config.quiet=False
        # self.mip_sup.config.tee=True
        # self.mip_sup.config.debug=True
        results = self.mip_sup.generate_schedule()
        results["point_"] = point
        #
        # This is a hack to handle the case where the MIP solver failed.
        # TODO: add more diagnostics here
        #
        if results["results"][0] is None:
            results["results"][0] = {"goals": {"total_separation": -999}}
        #
        # Return the total_separation statistic and results object
        #
        value = -results["results"][0]["goals"]["total_separation"]
        return value, results


class PMLabelSearch_Restricted(CachedTabuSearch):
    def __init__(
        self,
        *,
        config=None,
        nresources=None,
        nfeatures=None,
        constraints=None,
        labeling_restrictions=None,
        nworkers=1
    ):
        CachedTabuSearch.__init__(self)
        problem = PMLabelSearchProblem_Restricted(
            config=config,
            nresources=nresources,
            nfeatures=nfeatures,
            constraints=constraints,
            labeling_restrictions=labeling_restrictions,
        )
        if nworkers > 1:
            self.problem = RayTabuSearchProblem(problem=problem, nworkers=nworkers)
        else:
            self.problem = problem
        #
        self.options.verbose = config.options.get("verbose", False)
        if "max_stall_count" in config.options:
            self.options.max_stall_count = config.options.get("max_stall_count")
        if "stall_tolerance" in config.options:
            self.options.stall_tolerance = config.options.get("stall_tolerance")
        self.options.tabu_tenure = round(0.25 * problem.nfeatures) + 1
