#
# Simple process matching
#
from pypm.api import PYPM

def run():
    #PYPM.options['verbose'] = False

    #
    # Configure process matching api
    #
    pm = PYPM.supervised_mip()
    pm.load_config('config.yaml')
    #
    # Configure and run solver
    #
    pm.solver_options['name'] = 'glpk'
    #pm.solver_options['show_solver_output'] = True
    results = pm.run()
    #
    # Save results
    #
    results.write('results.yaml')

    return True

if __name__ == '__main__':      #pragma:nocover
    run()

