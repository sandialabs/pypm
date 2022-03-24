#
# Iteratively label data with TABU search
#
import copy
import random
from munch import Munch
from .tabu_search import CachedTabuSearch

class LabelSearch(CachedTabuSearch):

    def __init__(self, config=None, nresources=None, nfeatures=None):
        CachedTabuSearch.__init__(self)
        self.config = config
        self.verbose = self.config.options.get('verbose',False)
        if 'max_stall_count' in self.config.options:
            self.max_stall_count = self.config.options.get('max_stall_count')
        self.nresources = len(config.pm.resources)+1
        self.resources = list(sorted(k for k in self.config.pm.resources)) + ['IGNORED']
        self.nfeatures = len(config.obs['observations'])
        self.features = list(sorted(config.obs['observations'].keys()))
        #
        self.tabu_tenure = round(0.25 * self.nfeatures) + 1
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
        self.mip_sup.config.solver_strategy = 'simple'
        self.mip_sup.config.model = 'model13'         # or model11?
        config.obs = obs

    def initial_solution(self):
        # Each feature is randomly labeled as a resource
        point = []
        for i in range(self.nfeatures):
            point.append( random.randint(0,self.nresources-1) )
        return tuple(point)
 
    def moves(self, point, _):
        # Generate moves in the neighborhood
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

    def compute_solution_value(self, point):
        #
        # Create labeled observations
        #
        # Take the max value across all features associated with a resource in the 
        # current point.
        #
        observations = {k: [0]*self.config.obs.timesteps for k in self.resources}
        for index, i in enumerate(self.features):
            k = self.resources[point[index]]
            if k == len(self.resources) - 1:
                # The last category of resources is ignored
                continue
            for t in range(self.config.obs.timesteps):
                #print(index,k,i,t)
                #print(list(observations.keys()))
                #print(list(self.config.obs['observations'].keys()))
                observations[k][t] = max(observations[k][t], self.config.obs['observations'][i][t])
        #
        # Setup the configuration object to use these observations
        #
        self.mip_sup.config.obs = Munch(observations=observations, header="None", timesteps=self.config.obs.timesteps, datetime=self.config.obs.datetime)
        #
        # Execute the mip
        #
        results = self.mip_sup.run()
        #
        # Cache results
        #
        point_ = {i: self.resources[point[index]] for index,i in enumerate(self.features)}
        self.results[point] = point_, results
        # 
        if False and self.verbose:
            print(results['results'][0]['separation'])
            for k in observations:
                print(k, observations[k])
        #
        return - sum(value for value in results['results'][0]['separation'].values())


def run_tabu(config, constraints=[]):
    random.seed(config.seed)
    ls = LabelSearch(config)
    ls.max_iterations = config.options.get('max_iterations',100)
    ls.tabu_tenure = config.options.get('tabu_tenure',4)
    x, f = ls.run()
    point_, results = ls.results[x]
    results['results'][0]['labeling'] = point_
    results['search_strategy'] = 'tabu'
    results['solver_statistics'] = {'iterations':ls.iteration, 'stall count':ls.stall_count, 'unique solutions':len(ls.cache), 'evaluations': ls.num_moves_evaluated}
    return results.results

