#
# Same as t1, but force the inclusion of Activity6 at a specific date
#
from pypm.api import PYPM


def run():
    # PYPM.options['verbose'] = True

    #
    # Configure process matching api
    #
    pm = PYPM.supervised_mip()
    pm.load_config("config.yaml")

    #
    # Constraints
    #
    pm.maximize_total_match_score()
    pm.set_latest_start_date("Activity6", "2021-01-29 05:00:00")

    #
    # Configure and run solver
    #
    pm.solver_options["name"] = "glpk"
    # pm.solver_options['show_solver_output'] = True
    results = pm.generate_schedule()
    #
    # Save results
    #
    results.write("results.yaml")

    return True


if __name__ == "__main__":  # pragma:nocover
    run()
