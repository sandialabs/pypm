#
# Iteratively label data with TABU search
#
# import time
# import copy
import random

# from munch import Munch
import pprint
import ray
import ray.util.queue
from .ts_labeling import PMLabelSearch, ParallelPMLabelSearch
from .ts_labeling2 import PMLabelSearch_Restricted, ParallelPMLabelSearch_Restricted


def run_tabu_labeling(config, constraints=[], nworkers=1, debug=False):
    # print("YYY",len(constraints))
    if nworkers == 1:
        random.seed(config.seed)
        if config.labeling_restrictions:
            ls = PMLabelSearch_Restricted(
                config=config,
                constraints=constraints,
                labeling_restrictions=config.labeling_restrictions,
            )
        else:
            ls = PMLabelSearch(config=config, constraints=constraints)
    else:
        ray.init(num_cpus=nworkers + 1)
        if config.labeling_restrictions:
            ls = ParallelPMLabelSearch_Restricted(
                config=config,
                nworkers=nworkers,
                constraints=constraints,
                labeling_restrictions=config.labeling_restrictions,
            )
        else:
            ls = ParallelPMLabelSearch(
                config=config, nworkers=nworkers, constraints=constraints
            )
        ls.options.debug = debug
    ls.options.max_iterations = config.options.get("max_iterations", 100)
    ls.options.tabu_tenure = config.options.get("tabu_tenure", 4)
    x, f = ls.run()
    #
    # Setup results object
    #
    point_, results = ls.results[x]
    # HERE
    # pprint.pprint(results.results)
    results["solver"]["search_strategy"] = "tabu"
    if config.labeling_restrictions:
        results["results"][0]["resource_feature_list"] = {
            k: [j for j in point_[k] if point_[k][j]] for k in point_
        }
    else:
        results["results"][0]["feature_label"] = point_
    results["results"][0]["solver_statistics"] = {
        "iterations": ls.iteration,
        "stall count": ls.stall_count,
        "unique solutions": len(ls.cache),
        "evaluations": ls.num_moves_evaluated,
    }
    #
    # Add feature separation scores and scores for combined features
    #
    if not config.labeling_restrictions:
        separation = {f: 0 for f in config.obs["observations"]}
        tmp = {}
        for k, v in point_.items():
            if v in tmp:
                tmp[v].add(k)
            else:
                tmp[v] = set([k])
        for k, v in tmp.items():
            if len(v) > 1:
                name = "max({})".format(",".join(sorted(v)))
            else:
                name = list(v)[0]
            separation[name] = results["results"][0]["goals"]["separation"][k]
        results["results"][0]["goals"]["separation"] = separation
    #
    return results.results
