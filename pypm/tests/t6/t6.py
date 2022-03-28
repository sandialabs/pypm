#
# Same as t1, but add a latest start date ... and then relax it
#
from pypm.api import PYPM

def run():
    PYPM.options['verbose'] = True

    #
    # Configure process matching api
    #
    pm = PYPM.supervised_mip()
    pm.load_config('config.yaml')

    #
    # Constraints
    #
    pm.set_latest_start_date('Activity6', '2021-01-28 16:00:00')
    pm.relax_start_date('Activity6')

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

