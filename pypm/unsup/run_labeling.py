#
# Iteratively label data with TABU search
#
import os
import ray
from .ts_labeling import PMLabelSearch
from .ts_labeling2 import PMLabelSearch_Restricted


#
# Run Tabu Search to generate a labeling of
#
# Note: the config.label_representation data must generally be defined.
#
def run_tabu_labeling(config, constraints=[], nworkers=1, debug=False, setup_ray=True):
    assert (
        "label_representation" in config.options
    ), "Missing required value for the pypm Tabu Search solver: label_representation.\n  Valid values are resource_feature_list and feature_label."
    label_representation = config.options["label_representation"]
    if config.labeling_restrictions:
        assert (
            label_representation == "resource_feature_list"
        ), "The label_representation used by Tabu Search must be resource_feature_list when using label restrictions."
    if setup_ray and nworkers > 1:
        ray.init(num_cpus=nworkers + 1, ignore_reinit_error=True)
    if label_representation == "resource_feature_list":
        ls = PMLabelSearch_Restricted(
            config=config,
            constraints=constraints,
            labeling_restrictions=config.labeling_restrictions,
            nworkers=nworkers,
        )
    else:
        assert (
            label_representation == "feature_label"
        ), "Bad value for label_representation: {}.  Valid values are resource_feature_list and feature_label".format(
            label_representation
        )
        ls = PMLabelSearch(config=config, constraints=constraints, nworkers=nworkers)
    ls.options.search_strategy = config.options.get("local_search", "first_improving")
    ls.options.debug = debug
    ls.options.max_iterations = config.options.get("max_iterations", 100)
    ls.options.tabu_tenure = config.options.get("tabu_tenure", 4)
    if "cache_dir" in config.options:
        if config.dirname:
            cache_dir = os.path.join(config.dirname, config.options["cache_dir"])
        else:
            cache_dir = config.options["cache_dir"]
        try:
            os.mkdir(cache_dir)
        except FileExistsError:
            pass
        ls.options.checkpoint_file_template = os.path.join(cache_dir, "point_{}.json")
    #
    # Run Tabu Search
    #
    x, f = ls.run()
    if setup_ray and nworkers > 1:
        ray.shutdown()
    #
    # Augment the results object
    #
    results = ls.results[x]
    point_ = results["point_"]
    del results["point_"]
    results["solver"]["search_strategy"] = "tabu"
    if label_representation == "resource_feature_list":
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
    if label_representation == "feature_label":
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
