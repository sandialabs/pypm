#
# Iteratively label data with TABU search
#
import time
import copy
import random
from munch import Munch
import ray
import ray.util.queue
from .tabu_search import CachedTabuSearch, TabuSearchProblem, AsyncTabuSearch


class PMLabelSearchProblem(TabuSearchProblem):

    def __init__(self, config=None, nresources=None, nfeatures=None):
        TabuSearchProblem.__init__(self)
        self.config = config
        #
        self.nresources = len(config.pm.resources)+1
        self.resources = list(sorted(k for k in self.config.pm.resources)) + ['IGNORED']
        self.nfeatures = len(config.obs['observations'])
        self.features = list(sorted(config.obs['observations'].keys()))
        #
        # Solution representations:
        #   Standard
        #       x_i = resource_id
        #       Each resource can only be associated with a single feature
        # 
        #   Combine_Features
        #       x_i = resource_id
        #       When multiple x_i point to the same resource, these features
        #           are combined with max()
        #
        self.combine_features = self.config.options.get('combine_features',False)
        self.penalize_features = self.config.options.get('penalize_features',False)
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
        #print("HERE", self.mip_sup.config.model)
        self.mip_sup.config.verbose = False
        self.mip_sup.config.quiet = True
        config.obs = obs

    def initial_solution(self):
        if self.combine_features:
            #
            # Each feature is randomly labeled as a resource
            #
            point = []
            for i in range(self.nfeatures):
                point.append( random.randint(0,self.nresources-1) )
        else:
            #
            # Each resource is associated with a unique feature
            #
            tmp = list(range(self.nresources-1))
            random.shuffle(tmp)
            if self.nfeatures < self.nresources:
                point = [None]*self.nfeatures
                for i in range(self.nfeatures):
                    point[i] = tmp[i]
            else:
                point = [self.nresources - 1] * self.nfeatures
                for i in range(self.nresources-1):
                    point[tmp[i]] = i
        #
        return tuple(point)
 
    def moves(self, point, _):
        #
        # Generate moves in the neighborhood
        #
        if self.combine_features:
            rorder = list(range(self.nresources))
            random.shuffle(rorder)
            features = list(range(self.nfeatures))
            random.shuffle(features)
           
            for i in features:
                j = rorder.index(point[i])
                nhbr = list(point)

                nhbr[i] = rorder[j-1]
                yield tuple(nhbr), (i,rorder[j-1]), None

                nhbr[i] = rorder[(j+1) % self.nresources]
                yield tuple(nhbr), (i,rorder[(j+1) % self.nresources]), None

        else:
            # tmp[i] is the feature that points to resource j, or None
            tmp = [None] * self.nresources
            for i in range(self.nfeatures):
                tmp[point[i]] = i
            # The last resource is 'Ignore', which multiple features can point to
            tmp[self.nresources-1] = None

            unique = set()
            for k in range(0, int(max(1.0, self.nfeatures/self.nresources))):
                for i in range(self.nfeatures):
                    flag = True
                    while flag:         # Iterate until we generate have a new move
                        nhbr = list(point)
                        j = nhbr[i]
                        while j == nhbr[i]:
                            j = random.randint(0, self.nresources-1)
                        if tmp[j] is None:
                            point_i = nhbr[i]
                            nhbr[i] = j
                            move = tuple(nhbr), (i,j,i,point_i), None
                        else:
                            point_i = nhbr[i]
                            nhbr[i] = j
                            nhbr[tmp[j]] = point_i
                            if i < tmp[j]:
                                move = tuple(nhbr), (i,j,tmp[j],point_i), None
                            else:
                                move = tuple(nhbr), (tmp[j],point_i,i,j), None
                        if move[0] not in unique:
                            flag = False
                            unique.add(move[0])
                            yield move

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
            k = self.resources[point[index]]
            if k == len(self.resources) - 1:
                # The last category of resources is ignored
                continue
            for t in range(self.config.obs.timesteps):
                observations[k][t] = max(observations[k][t], self.config.obs['observations'][i][t])
        #
        # Setup the configuration object to use these observations
        #
        self.mip_sup.config.obs = Munch(observations=observations, header="None", timesteps=self.config.obs.timesteps, datetime=self.config.obs.datetime)
        #
        # Execute the mip
        #
        results = self.mip_sup.generate_schedule()
        #
        # Cache results
        #
        point_ = {i: self.resources[point[index]] for index,i in enumerate(self.features)}
        self.results[point] = point_, results
        # 
        if False and self.options.verbose:
            print(results['results'][0]['goals']['separation'])
            for k in observations:
                print(k, observations[k])
        #
        if self.penalize_features:
            #
            # Count # of ignored features
            #
            nignored = 0
            for val in point:
                if val == self.nresources - 1:
                    nignored += 1
            return - results['results'][0]['goals']['total_separation'] - nignored/self.nfeatures
        else:
            return - results['results'][0]['goals']['total_separation']


@ray.remote(num_cpus=1)
class Worker(object):

    def __init__(self, config):
        random.seed(config.seed)
        self.problem = PMLabelSearchProblem(config)
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
        print("HERE", self.mip_sup.config.model)
        self.mip_sup.config.verbose = False
        self.mip_sup.config.quiet = True
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


class ParallelPMLabelSearchProblem(TabuSearchProblem):

    def __init__(self, config=None, nresources=None, nfeatures=None, nworkers=None):
        TabuSearchProblem.__init__(self)
        self.problem = PMLabelSearchProblem(config)
        #
        self.nfeatures = self.problem.nfeatures
        self.nresources = self.problem.nresources
        #
        nworkers = ray.available_resources() if nworkers is None else nworkers
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


class PMLabelSearch(CachedTabuSearch):

    def __init__(self, config=None, nresources=None, nfeatures=None):
        CachedTabuSearch.__init__(self)
        self.problem = PMLabelSearchProblem(config=config, nresources=nresources, nfeatures=nfeatures)
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


class ParallelPMLabelSearch(AsyncTabuSearch):

    def __init__(self, config=None, nresources=None, nfeatures=None, nworkers=1):
        AsyncTabuSearch.__init__(self)
        self.problem = ParallelPMLabelSearchProblem(config=config, nresources=nresources, nfeatures=nfeatures, nworkers=nworkers)
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


def run_tabu(config, constraints=[], nworkers=1, debug=False):
    if nworkers == 1:
        random.seed(config.seed)
        ls = PMLabelSearch(config)
    else:
        ray.init(num_cpus=nworkers+1)
        ls = ParallelPMLabelSearch(config=config, nworkers=nworkers)
        ls.options.debug = debug
    ls.options.max_iterations = config.options.get('max_iterations',100)
    ls.options.tabu_tenure = config.options.get('tabu_tenure',4)
    x, f = ls.run()
    #
    # Setup results object
    #
    point_, results = ls.results[x]
    results['solver']['search_strategy'] = 'tabu'
    results['results'][0]['feature_label'] = point_
    results['results'][0]['solver_statistics'] = {'iterations':ls.iteration, 'stall count':ls.stall_count, 'unique solutions':len(ls.cache), 'evaluations': ls.num_moves_evaluated}
    #
    # Add feature separation scores and scores for combined features
    #
    separation = { f:0 for f in config.obs['observations'] }
    tmp = {}
    for k,v in point_.items():
        if v in tmp:
            tmp[v].add(k)
        else:
            tmp[v] = set([k])
    for k,v in tmp.items():
        if len(v) > 1:
            name = "max({})".format(",".join(sorted(v)))
        else:
            name = list(v)[0]
        separation[name] = results['results'][0]['goals']['separation'][k]
    results['results'][0]['goals']['separation'] = separation
    #
    return results.results

