#
# Same as t3, but set the earliest start date for Activity1 using a fractional hour date
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
    pm.set_earliest_start_date('Activity1', '2021-01-02 08:15:00')

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

