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
import ray
import ray.util.queue
from .tabu_search import CachedTabuSearch, TabuSearchProblem, AsyncTabuSearch


class hdict(dict):
    def __hash__(self):
        return hash(json.dumps(self, sort_keys=True))


class PMLabelSearchProblem_Restricted(TabuSearchProblem):

    def __init__(self, *, config=None, nresources=None, nfeatures=None, constraints=None, labeling_restrictions=None):
        TabuSearchProblem.__init__(self)
        self.config = config
        self.labeling_restrictions = labeling_restrictions
        #
        self.nresources = len(config.pm.resources)
        self.resources = list(sorted(k for k in self.config.pm.resources))
        self.nfeatures = len(config.obs['observations'])
        self.features = list(sorted(config.obs['observations'].keys()))
        #
        # Solution representations:
        #   Standard
        #       x_ij = 1 if feature i is associted with resource j
        #       When multiple features are associated a resource, these features
        #           are combined with max()
        #
        self.results = {}
        #
        # Setup MIP solver, using a clone of the config without observation data (config.obs)
        #
        from pypm.api import PYPM
        self.mip_sup = PYPM.supervised_mip()
        obs = config.obs
        config.obs = None
        self.mip_sup.config = copy.deepcopy(config)
        self.mip_sup.config.search_strategy = 'mip'
        self.mip_sup.config.model = config.options.get('tabu_model', 'GSF-ED')
        self.mip_sup.config.verbose = False
        self.mip_sup.config.quiet = True
        if constraints:
            self.mip_sup.add_constraints(constraints)
        config.obs = obs

    def initial_solution(self):
        point = hdict()
        for i in self.resources:
            point[i] = hdict()
            for j in self.labeling_restrictions[i]['optional']:
                point[i][j] = random.randint(0,1)
            for j in self.labeling_restrictions[i]['required']:
                point[i][j] = 1
        return point
 
    def moves(self, point, _):
        #
        # Generate moves in the neighborhood
        #
        rorder = list(range(self.nresources))
        random.shuffle(rorder)
        for i_ in rorder:
            i = self.resources[i_]
            curr = self.labeling_restrictions[i]['optional']
            j = random.choice(list(point[i].keys()))
            nhbr = copy.deepcopy(point)
            #print("BEFORE", nhbr[i][j])
            nhbr[i][j] = 1 - nhbr[i][j]
            #print("AFTER", nhbr[i][j])
            #print("X",i,j,point[i][j])
            #print("Y",nhbr)
            yield nhbr, (i,j,point[i][j]), None

    def compute_solution_value(self, point):
        #
        # Create labeled observations
        #
        # Take the max value across all features associated with a resource in the 
        # current point.
        #
        observations = {k: [0]*self.config.obs.timesteps for k in self.resources}
        for index, i in enumerate(self.features):
            #print("HERE",index,point[index],self.resources)
            for k in point:
                if point[k][i]:
                    for t in range(self.config.obs.timesteps):
                        observations[k][t] = max(observations[k][t], self.config.obs['observations'][i][t])
        #
        # Setup the configuration object to use these observations
        #
        self.mip_sup.config.obs = Munch(observations=observations, header="None", timesteps=self.config.obs.timesteps, datetime=self.config.obs.datetime)
        #
        # Execute the mip
        #
        #print("XXX",len(self.mip_sup.constraints))
        results = self.mip_sup.generate_schedule()
        #pprint.pprint(results.results)
        #
        # Cache results
        #
        self.results[point] = point, results
        # 
        if False and self.options.verbose:
            print(results['results'][0]['goals']['separation'])
            for k in observations:
                print(k, observations[k])
        #
        return - results['results'][0]['goals']['total_separation']


@ray.remote(num_cpus=1)
class Worker(object):

    def __init__(self, config):
        random.seed(config.seed)
        self.problem = PMLabelSearchProblem_Restricted(config=config, constraints=config.constraints)
        #
        # Setup MIP solver, using a clone of the config without observation data (config.obs)
        #
        from pypm.api import PYPM
        self.mip_sup = PYPM.supervised_mip()
        obs = self.problem.config.obs
        self.problem.config.obs = None
        self.mip_sup.config = copy.deepcopy(self.problem.config)
        self.mip_sup.config.search_strategy = 'mip'
        self.mip_sup.config.model = config.options.get('tabu_model', 'GSF-ED')
        print("HERE", self.mip_sup.config.model, len(config.constraints))
        self.mip_sup.config.verbose = False
        self.mip_sup.config.quiet = True
        if config.constraints:
            self.mip_sup.add_constraints(config.constraints)
        self.problem.config.obs = obs

    def run(self, point_queue, results_queue):
        # NOTE - Need to rework this to allow overlapping communication
        #           and computation
        while True:
            point = point_queue.get(block=True)
            results_queue.put(self.compute_solution_value(point))

    def compute_solution_value(self, point):
        value = self.problem.compute_solution_value(point)
        point_, results = self.problem.results[point]
        return value, point, results, point_


class ParallelPMLabelSearchProblem_Restricted(TabuSearchProblem):

    def __init__(self, config=None, nresources=None, nfeatures=None, nworkers=None, constraints=None, labeling_restrictions=None):
        TabuSearchProblem.__init__(self)
        self.problem = PMLabelSearchProblem_Restricted(config=config)
        #
        self.nfeatures = self.problem.nfeatures
        self.nresources = self.problem.nresources
        #
        nworkers = ray.available_resources() if nworkers is None else nworkers
        config.constraints = constraints
        config_obj = ray.put(config)
        self.workers = [Worker.remote(config_obj) for i in range(nworkers)]
        self.requests_queue = ray.util.queue.Queue()
        self.results_queue = ray.util.queue.Queue()
        for w in self.workers:
            w.run.remote(self.requests_queue, self.results_queue)
        #
        self.results = {}
        random.seed(config.seed)

    def initial_solution(self):
        return self.problem.initial_solution()

    def moves(self, point, _):
        return self.problem.moves(point, None)

    def request_solution_value(self, point):
        #print("request_solution_value")
        return self.requests_queue.put_nowait(point)

    def get_solution_value(self):
        #print("get_solution_value")
        if self.results_queue.empty():
            return None
        value, point, results, point_ = self.results_queue.get()
        self.results[point] = point_, results
        return value, point

    def compute_solution_value(self, point):
        #print("compute_solution_value")
        self.request_solution_value(point)
        results = self.get_solution_value()
        while results == None:
            time.sleep(0.1)
            results = self.get_solution_value()
        return results[0]


class PMLabelSearch_Restricted(CachedTabuSearch):

    def __init__(self, *, config=None, nresources=None, nfeatures=None, constraints=None, labeling_restrictions=None):
        CachedTabuSearch.__init__(self)
        self.problem = PMLabelSearchProblem_Restricted(config=config, nresources=nresources, nfeatures=nfeatures, constraints=constraints, labeling_restrictions=labeling_restrictions)
        #
        self.options.verbose = config.options.get('verbose',False)
        if 'max_stall_count' in config.options:
            self.options.max_stall_count = config.options.get('max_stall_count')
        self.options.tabu_tenure = round(0.25 * self.problem.nfeatures) + 1
        #

    @property
    def results(self):
        #
        # Return the cached results, which are stored on self.problem
        #
        return self.problem.results


class ParallelPMLabelSearch_Restricted(AsyncTabuSearch):

    def __init__(self, *, config=None, nresources=None, nfeatures=None, nworkers=1, constraints=None, labeling_restrictions=None):
        AsyncTabuSearch.__init__(self)
        self.problem = ParallelPMLabelSearchProblem_Restricted(config=config, nresources=nresources, nfeatures=nfeatures, nworkers=nworkers, constraints=constraints, labeling_restrictions=labeling_restrictions)
        #
        self.options.verbose = config.options.get('verbose',False)
        if 'max_stall_count' in config.options:
            self.options.max_stall_count = config.options.get('max_stall_count')
        self.options.tabu_tenure = round(0.25 * self.problem.nfeatures) + 1

    @property
    def results(self):
        #
        # Return the cached results, which are stored on self.problem
        #
        return self.problem.results

