#
# Generic Tabu Search Solver
#
import abc
from munch import Munch
import time
import random
import math
import ray


class TabuSearch(object):

    def __init__(self, problem=None):
        self.options = Munch()
        self.options.max_iterations = 100
        self.options.max_stall_count = self.options.max_iterations/4
        self.options.tabu_tenure = 2
        self.options.verbose = False
        self.options.debug = False
        #
        self.iteration = 0
        self.stall_count = 0
        self.tabu_time = {}
        #
        self.problem = problem

    def initial_solution(self):
        #
        # Generate initial solution
        # Returns: the solution
        #
        return self.problem.initial_solution()
 
    def moves(self, point, value):
        #
        # Returns (neighbor, move used to generate the neighbor, value of the neighbor (or None))
        #
        return self.problem.moves(point, value)

    def compute_solution_value(self, point):
        #
        # Compute the value of a solution
        # Returns: float value for the solution
        #
        return self.problem.compute_solution_value(point)
 
    def end_iteration(self):
        # End-of-iteration operations
        pass

    def generate_moves(self, x, f_x, f_best):
        move_ = None
        x_ = None
        f_ = float("inf")
        tabu = False

        for neighbor, move, value in self.moves(x, f_x):
            if value is None:
                value = self.evaluate(neighbor)
            if move in self.tabu_time and self.tabu_time[move] >= self.iteration:
                if self.options.verbose:
                    print("#   TABU Move: {}  TABU Time: {}".format(move, self.tabu_time[move]))
                # Aspiration criteria: Always keep best point found so far
                if value < f_best:
                    f_best = value
                    move_, x_, f_ = move, neighbor, value
                    tabu = True
                    break
            elif value < f_x:
                move_, x_, f_ = move, neighbor, value
                break
            elif value < f_:
                move_, x_, f_ = move, neighbor, value

        if move_ is not None:
            self.tabu_time[move_] = self.iteration + self.options.tabu_tenure

        return x_, f_, tabu

    def evaluate(self, point):
        return self.compute_solution_value(point)

    def run(self):
        x_best = x   = self.initial_solution()
        f_best = f_x = self.evaluate(x)

        self.stall_count = 0
        while True:
            #
            # Find the best neighbor
            #
            x_nbhd, f_nbhd, tabu = self.generate_moves(x, f_x, f_best)
            #
            # Update the best point seen so far
            #
            if tabu or f_nbhd < f_best:
                #
                # Found a tabu point that improved on the globally best
                #
                x_best, f_best = x_nbhd, f_nbhd
                x, f_x = x_nbhd, f_nbhd
                self.stall_count = 0
            else:
                #
                # Update the current point to the point generated
                # in our search of the neighborhood
                #
                if x_nbhd is not None:
                    x, f_x = x_nbhd, f_nbhd
                self.stall_count += 1
            #
            # End iteration
            #
            self.end_iteration()
            self.iteration += 1
            if self.options.verbose:
                print("\n# Iteration: {}\n# Best objective: {}\n# Current Objective: {}\n# Current Point: {}\n".format(self.iteration, f_best, f_x, x))
            else:
                print("# Iteration: {}  Best objective: {}  Current Objective: {}".format(self.iteration, f_best, f_x))
            #
            # Check termination
            #
            if self.iteration >= self.options.max_iterations:
                print("# Termination at iteration {}".format(self.iteration))
                break
            if self.stall_count >= self.options.max_stall_count:
                print("# Termination after {} stalled iterations.".format(self.stall_count))
                break

        return x_best, f_best


class CachedTabuSearch(TabuSearch):

    def __init__(self):
        TabuSearch.__init__(self)
        self.cache = {}
        self.num_moves_evaluated = 0

    def evaluate(self, point):
        self.num_moves_evaluated += 1
        value = self.cache.get(point, None)
        cached = True
        if value is None:
            cached = False
            value = self.cache[point] = self.compute_solution_value(point)
        if self.options.verbose:
            print("POINT: {}  VALUE: {}  Cached: {}".format(point, value, cached))
        return value

    def run(self):
        x_best, f_best = TabuSearch.run(self)
        print("# Final Results")
        print("#   Best Value: {}".format(f_best))
        print("#   Best Solution: {}".format(x_best))
        print("#   Num Unique Solutions Evaluated: {}".format(len(self.cache)))
        print("#   Num Solutions Evaluated: {}".format(self.num_moves_evaluated))

        if self.options.verbose:
            print("\nFinal TABU Table")
            if len(self.tabu_time) > 0:
                for move in sorted(self.tabu_time.keys()):
                    print(move,self.tabu_time[move])
            else:
                print("\n  None")
        return x_best, f_best


class AsyncTabuSearch(TabuSearch):
    """
    An async TABU search method that uses a cache, but asynchronously
    evaluates all neighboring points.
    """

    def __init__(self):
        TabuSearch.__init__(self)
        self.cache = {}
        self.num_moves_evaluated = 0

    def generate_moves(self, x, f_x, f_best):
        #
        # Request evaluations for neighbors that we haven't evaluated
        #
        evaluated = {}
        queued = {}
        for neighbor, move, value in self.moves(x, f_x):
            if value is not None:
                evaluated[neighbor] = move,value
            else:
                self.num_moves_evaluated += 1
                value = self.cache.get(neighbor, None)
                if value is None:
                    queued[neighbor] = move
                    self.problem.request_solution_value(neighbor)
                    if self.options.debug:
                        print("Requested evaluation - Point {}".format(neighbor))
                else:
                    evaluated[neighbor] = move,value
        #
        # Collect evaluated neighbors, and process them
        #
        curr = 0
        while len(queued) > 0:
            if self.options.debug or self.options.verbose:
                if curr % 10 == 0:
                    print("Waiting for {} queued evaluations".format(len(queued)))
                curr += 1
            #
            # Collect evaluated neighbors until there are no more
            #
            while True:
                results = self.problem.get_solution_value()
                if results is None:
                    time.sleep(1)
                    break
                value, neighbor = results
                if self.options.debug:
                    print("Received Results - Point {}  Value {}".format(neighbor, value))
                    print("Queued: {}".format(list(sorted(queued.keys()))))
                evaluated[neighbor] = queued[neighbor],value        # move, value
                del queued[neighbor]
                self.cache[neighbor] = value
                if self.options.debug:
                    print("Evaluation Complete - Point {}  Value {}".format(neighbor, value))

        if self.options.verbose:
            for nhbr in sorted(evaluated.keys()):
                print("Evaluation Complete - Point {}  Value {}".format(nhbr, self.cache[nhbr]))
        #
        # Process the list of evaluated neighbors
        #
        move_ = None
        x_ = None
        f_ = float("inf")
        tabu = False
        for neighbor in sorted(evaluated.keys(), reverse=True):         # Create bias towards solutions with ignored features
            move, value = evaluated[neighbor]
            if move in self.tabu_time and self.tabu_time[move] >= self.iteration:
                if self.options.verbose:
                    print("#   TABU Move: {}  TABU Time: {}".format(move, self.tabu_time[move]))
                # Aspiration criteria: Always keep best point found so far
                if value < f_best:
                    f_best = value
                    move_, x_, f_ = move, neighbor, value
                    tabu = True
                    #break
            elif value < f_x:
                move_, x_, f_ = move, neighbor, value
                tabu = False
                #break
            elif value < f_:
                move_, x_, f_ = move, neighbor, value
                tabu = False
        #
        # Update the tabu time for the best move, and return
        #
        if move_ is not None:
            self.tabu_time[move_] = self.iteration + self.options.tabu_tenure
        return x_, f_, tabu

    def run(self):
        x_best, f_best = TabuSearch.run(self)
        print("# Final Results")
        print("#   Best Value: {}".format(f_best))
        print("#   Best Solution: {}".format(x_best))
        print("#   Num Unique Solutions Evaluated: {}".format(len(self.cache)))
        print("#   Num Solutions Evaluated: {}".format(self.num_moves_evaluated))

        if self.options.verbose:
            print("\nFinal TABU Table")
            for move in sorted(self.tabu_time.keys()):
                print(move,self.tabu_time[move])
        return x_best, f_best


class TabuSearchProblem(object):

    @abc.abstractmethod
    def initial_solution(self):
        #
        # Generate initial solution
        # Returns: the solution
        #
        pass

    @abc.abstractmethod
    def moves(self, point, value):
        #
        # Returns (neighbor, move used to generate the neighbor, value of the neighbor (or None))
        #
        pass

    def compute_solution_value(self, point):
        #
        # Compute the value of a solution
        # Returns: float value for the solution
        #
        raise RuntimeError("Undefined method: TabuSearchProblem.compute_solution_value")

    def request_solution_value(self, point):
        #
        # Async request for the value of a solution
        # Returns: None
        #
        raise RuntimeError("Undefined method: TabuSearchProblem.request_solution_value")

    def get_solution_value(self):
        #
        # Get the value of a solution requested earlier
        # Returns: list containing the point and the float value for the solution
        #
        raise RuntimeError("Undefined method: TabuSearchProblem.get_solution_value")


class LabelSearchProblem(TabuSearchProblem):

    def __init__(self, pm=None, data=None, nresources=None, nfeatures=None):
        if pm is not None:
            self.pm = pm
            self.nresources = len(pm.resources)
            self.nfeatures = len(data)
        else:
            self.nresources = nresources
            self.nfeatures = nfeatures

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
        # This is a dummy value used to test this searcher
        return sum((i+1)*(1+math.sin(i/10.0)) for i in point)
                    

class LabelSearch(CachedTabuSearch):

    def __init__(self, pm=None, data=None, nresources=None, nfeatures=None):
        CachedTabuSearch.__init__(self)
        self.problem = LabelSearchProblem(pm=pm, data=data, nresources=nresources, nfeatures=nfeatures)


class LabelSearchOLD(CachedTabuSearch):

    def __init__(self, pm=None, data=None, nresources=None, nfeatures=None):
        CachedTabuSearch.__init__(self)
        if pm is not None:
            self.pm = pm
            self.nresources = len(pm.resources)
            self.nfeatures = len(data)
        else:
            self.nresources = nresources
            self.nfeatures = nfeatures
        #
        self.options.tabu_tenure = round(0.25 * self.nfeatures) + 1

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
        # This is a dummy value used to test this searcher
        return sum((i+1)*(1+math.sin(i/10.0)) for i in point)


if __name__ == "__main__":
    random.seed(39483098)
    ls = LabelSearchOLD(nresources=6, nfeatures=7)
    ls.options.max_iterations = 100
    ls.options.tabu_tenure = 4
    ls.run()
    #
    random.seed(39483098)
    ls = LabelSearch(nresources=6, nfeatures=7)
    ls.options.max_iterations = 100
    ls.options.tabu_tenure = 4
    ls.run()
    
