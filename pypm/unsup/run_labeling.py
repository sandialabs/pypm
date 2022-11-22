#
# Iteratively label data with TABU search
#
import random
import ray
import ray.util.queue
from .ts_labeling import PMLabelSearch, ParallelPMLabelSearch
from .ts_labeling2 import PMLabelSearch_Restricted, ParallelPMLabelSearch_Restricted


#
# Run Tabu Search to generate a labeling of
#
# Note: the config.label_representation data must generally be defined.
#
def run_tabu_labeling(config, constraints=[], nworkers=1, debug=False):
    if config.labeling_restrictions:
        assert config.label_representation == "resource_feature_list"
    if nworkers == 1:
        #
        # Serial Tabu Search
        #
        random.seed(config.seed)
        if config.label_representation == "resource_feature_list":
            ls = PMLabelSearch_Restricted(
                config=config,
                constraints=constraints,
                labeling_restrictions=config.labeling_restrictions,
            )
        else:
            assert config.label_representation == "feature_label"
            ls = PMLabelSearch(config=config, constraints=constraints)
    else:  # pragma: no cover
        #
        # Parallel Tabu Search
        #
        # NOTE: pytest does not work properly with ray, so we ignore this branch while testing
        #
        ray.init(num_cpus=nworkers + 1)
        if config.label_representation == "resource_feature_list":
            ls = ParallelPMLabelSearch_Restricted(
                config=config,
                nworkers=nworkers,
                constraints=constraints,
                labeling_restrictions=config.labeling_restrictions,
            )
        else:
            assert config.label_representation == "feature_label"
            ls = ParallelPMLabelSearch(
                config=config, nworkers=nworkers, constraints=constraints
            )
    ls.options.debug = debug
    ls.options.max_iterations = config.options.get("max_iterations", 100)
    ls.options.tabu_tenure = config.options.get("tabu_tenure", 4)
    #
    # Run Tabu Search
    #
    x, f = ls.run()
    #
    # Augment the results object
    #
    results = ls.results[x]
    point_ = results["point_"]
    del results["point_"]
    results["solver"]["search_strategy"] = "tabu"
    if config.label_representation == "resource_feature_list":
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
    if config.label_representation == "feature_label":
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
