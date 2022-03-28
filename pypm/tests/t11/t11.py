#
# Simple process matching
#
from munch import Munch
from pypm.api import PYPM

def run():
    #PYPM.options['verbose'] = True

    #
    # Configure process matching api
    #
    pm = PYPM.supervised_mip()
    pm.load_config('config.yaml')

    #
    # Collect activity lengths
    #
    length = {}
    for j in pm.config.pm:
        length[j] = Munch(min=pm.config.pm[j]['duration']['min_hours'], max=pm.config.pm[j]['duration']['max_hours'])
    for j in length:
        print("{} {} {}".format(j, length[j].min, length[j].max))

    #
    # Constraints
    #
    # Set the activity min/max lengths to be equal to the min value
    #
    pm.maximize_total_match_score()
    for j in length:
        pm.set_activity_duration(j, length[j].min, length[j].min)

    #
    # Configure and run solver
    #
    pm.solver_options['name'] = 'glpk'
    #pm.solver_options['show_solver_output'] = True
    results = pm.generate_schedule()
    #
    # Save results
    #
    results.write('results.yaml')

    return True

if __name__ == '__main__':      #pragma:nocover
    run()

