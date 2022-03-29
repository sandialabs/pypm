#
# Simple process matching
#
from pypm.api import PYPM

#PYPM.options['verbose'] = True

#
# Configure process matching api
#
pm = PYPM.supervised_mip()
pm.load_config('config.yaml')

#
# Constraints
#
pm.maximize_total_match_score()

#
# Configure and run solver
#
pm.solver_options['name'] = 'glpk'
pm.solver_options['show_solver_output'] = True
results = pm.generate_schedule()
#
# Save results
#
results.write('results.yaml')

