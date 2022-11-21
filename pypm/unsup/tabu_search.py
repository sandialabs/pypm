#
# Generic Tabu Search Solver
#
import abc
from munch import Munch
import time
import random
import math
import ray


class TabuSearchProblem(object):
    def __init__(self):
        self._requests = set()

    @abc.abstractmethod
    def initial_solution(self):
        #
        # Generate initial solution
        # Returns: the solution
        #
        pass  # pragma: no cover

    @abc.abstractmethod
    def moves(self, point, value):
        #
        # Returns a generator that iteratively yields tuples with values:
        # (neighbor, move used to generate the neighbor, value of the neighbor (or None))
        #
        pass  # pragma: no cover

    def compute_solution_value(self, point):
        #
        # Compute the value of a solution
        # Returns: float value for the solution
        #
        raise RuntimeError(
            "Undefined method: TabuSearchProblem.compute_solution_value"
        )  # pragma: no cover

    def request_solution_value(self, point):
        #
        # Async request for the value of a solution
        # Returns: None
        #
        self._requests.add(point)

    def cancel_request(self, point):
        #
        # Cancel request for the value of a solution
        # Returns: None
        #
        self._requests.discard(point)

    def cancel_all_requests(self):
        #
        # Cancel all request for solution values
        # Returns: None
        #
        self._requests.clear()

    def get_solution_value(self):
        #
        # Get the value of a solution requested earlier
        # Returns: list containing the point and the float value for the solution
        #
        if len(self._requests) == 0:
            return None
        point = self._requests.pop()
        return self.compute_solution_value(point), point


class TabuSearch(object):
    def __init__(self, problem=None):
        self.options = Munch()
        #
        # If greater than zero, then this specifies the maximum number of
        # iterations that Tabu Search is executed
        #
        self.options.max_iterations = 100
        #
        # If greater than zero, then this specifies the maximum number of
        # iterations that Tabu Search is allowed to continue without finding
        # an improving solution.
        #
        self.options.max_stall_count = self.options.max_iterations / 4
        self.options.tabu_tenure = 2
        #
        # Search strategies
        #   first_improving - Consider each move generated by the problem object, and
        #                       accept the first improving solution
        #   best_improving - Consider all moves generated by the problem object, and
        #                       accept the best improving solution
        #
        self.options.search_strategy = "first_improving"
        self.options.verbose = False
        self.options.debug = False
        #
        self.iteration = 0
        self.stall_count = 0
        #
        self.search_strategies = {
            "first_improving": self.search_neighborhood_first_improving,
            "best_improving": self.search_neighborhood_best_improving
            }
        #
        # Mapping from solution to iteration count.  A move is ignored (i.e. it is
        # tabu), if (tabu_time[move] >= self.iteration) is true ... unless it
        # has a better value than the best point seen so far.
        #
        self.tabu_time = {}
        #
        # An object that defines problem-specific operations, including
        # generating an initial solution, generating moves and computing
        # solution values.
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
        # Returns a generator that iteratively yields tuples with values:
        # (neighbor, move used to generate the neighbor, value of the neighbor (or None))
        #
        return self.problem.moves(point, value)

    def compute_solution_value(self, point):
        #
        # Compute the value of a solution
        # Returns: float value for the solution
        #
        return self.problem.compute_solution_value(point)

    def evaluate(self, point):
        return self.compute_solution_value(point)

    def request_solution_value(self, point):
        #
        # Returns None if no results are available
        # Otherwise, returns a tuple (value, neighbor)
        #
        return self.problem.request_solution_value(point)

    def search_neighborhood(self, x, f_x, f_best):
        #
        # Generate moves in the neighborhood to find the best point. Evaluate them
        # if their value is not already known.
        #
        # The default behavior of the TabuSearch class is to use a first-improving
        # search strategy, but the best-improving strategy can also be used.
        #
        return self.search_strategies[self.options.search_strategy](x, f_x, f_best)

    def search_neighborhood_first_improving(self, x, f_x, f_best):
        #
        # This executes search in a greedy manner, updating 
        # the current iterate, x_, as soon as a neighbor with an improving value
        # is found.
        #
        move_ = None
        x_ = None
        f_ = float("inf")
        tabu = False

        for neighbor, move, value in self.moves(x, f_x):
            if value is None:
                value = self.evaluate(neighbor)
            if move in self.tabu_time and self.tabu_time[move] >= self.iteration:
                if self.options.verbose:  # pragma: no cover
                    print( "#   TABU Move: {}  TABU Time: {}".format( move, self.tabu_time[move])
                    )
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
            if self.options.verbose:  # pragma: no cover
                print( "#   TABU UPDATE  X: {}  Move: {}  TABU Time: {}".format( x_, move, self.tabu_time[move_]))

        return x_, f_, tabu

    def search_neighborhood_best_improving(self, x, f_x, f_best):
        """
        Search for all improving neighbors, and keeps the best one.
        """
        #
        # Queue all evaluations and collect them.  This allows for parallel
        # evaluation of neighbors.
        #
        evaluated = {}
        queued = {}
        for neighbor, move, value in self.moves(x, f_x):
            if value is not None:
                evaluated[neighbor] = move, value
            else:
                queued[neighbor] = move
                self.problem.request_solution_value(neighbor)
                if self.options.debug:
                    print("Requested evaluation - Point {}".format(neighbor))
        #
        # Collect evaluated neighbors
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
            results = self.get_solution_value()
            while results is not None:
                value, neighbor = results
                if self.options.debug:
                    print(
                        "Received Results - Point {}  Value {}".format(neighbor, value)
                    )
                    print("Queued: {}".format(list(sorted(queued.keys()))))
                evaluated[neighbor] = queued[neighbor], value  # move, value
                del queued[neighbor]
                if self.options.debug:
                    print(
                        "Evaluation Complete - Point {}  Value {}".format(
                            neighbor, value
                        )
                    )
                results = self.get_solution_value()
            #
            # Sleep if we've collected all available evaluations and need to
            # wait for more
            #
            if len(queued) > 0:                     # pragma: no cover
                time.sleep(0.1)
        #
        if self.options.verbose:
            for nhbr in sorted(evaluated.keys()):
                print(
                    "Evaluation Complete - Point {}  Value {}".format(
                        nhbr, self.cache[nhbr]
                    )
                )
        #
        # Process the list of evaluated neighbors
        #
        # NOTE: Reverse sorting the examination of the neighbor list here creates a bias.  When multiple
        # solutions have the same value, the one that is generated "last" is selected.  This helps
        # encourage diversity of solutions being searched.
        #
        move_ = None
        x_ = None
        f_ = float("inf")
        tabu = False
        for neighbor in sorted(evaluated.keys(), reverse=True):
            move, value = evaluated[neighbor]
            if move in self.tabu_time and self.tabu_time[move] >= self.iteration:
                if self.options.verbose:
                    print(
                        "#   TABU Move: {}  TABU Time: {}".format(
                            move, self.tabu_time[move]
                        )
                    )
                # Aspiration criteria: Always keep best point found so far
                if value < f_best:
                    f_best = value
                    move_, x_, f_ = move, neighbor, value
                    tabu = True
            elif value < f_x:
                move_, x_, f_ = move, neighbor, value
                tabu = False
            elif value < f_:
                move_, x_, f_ = move, neighbor, value
                tabu = False
        #
        # Update the tabu time for the best move, and return
        #
        if move_ is not None:
            self.tabu_time[move_] = self.iteration + self.options.tabu_tenure
        return x_, f_, tabu

    def end_iteration(self):
        # End-of-iteration operations
        pass

    def run(self):
        x_best = x = self.initial_solution()
        f_best = f_x = self.evaluate(x)

        self.stall_count = 0
        while True:
            #
            # Find the best neighbor
            #
            x_nbhd, f_nbhd, tabu = self.search_neighborhood(x, f_x, f_best)
            #
            # Update the best point seen so far
            #
            if tabu or f_nbhd < f_best:
                #
                # Found a tabu point, or a point that improved on the globally best
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
            if self.options.verbose:    #pragma: no cover
                print(
                    "\n# Iteration: {}\n# Best objective: {}\n# Current Objective: {}\n# Current Point: {}\n".format(
                        self.iteration, f_best, f_x, x
                    )
                )
            else:
                print(
                    "# Iteration: {}  Best objective: {}  Current Objective: {}".format(
                        self.iteration, f_best, f_x
                    )
                )
            #
            # Check termination
            #
            if self.iteration >= self.options.max_iterations:   #pragma: no cover
                print("# Termination at iteration {}".format(self.iteration))
                break
            if self.stall_count >= self.options.max_stall_count:    #pragma: no cover
                print(
                    "# Termination after {} stalled iterations.".format(
                        self.stall_count
                    )
                )
                break

        return x_best, f_best


class CachedTabuSearch(TabuSearch):
    """
    Avoid re-evaluating points that are have been previously evaluated.  All values are cached.
    """

    def __init__(self):
        TabuSearch.__init__(self)
        self.cache = {}
        self.num_moves_evaluated = 0

    def moves(self, point, value):
        for n, m, v in self.problem.moves(point, value):
            self.num_moves_evaluated += 1
            if v is None:
                v = self.cache.get(n, None)
                if v is not None and self.options.verbose:  # pragma: no cover
                    print("CACHED:    {}  VALUE: {}".format(point, value))
            yield (n,m,v)
            
    def evaluate(self, point):
        value = self.cache[point] = self.compute_solution_value(point)
        if self.options.verbose:  # pragma: no cover
            print("EVALUATED: {}  VALUE: {}".format(point, value))
        return value

    def get_solution_value(self):
        results = self.problem.get_solution_value()
        if results is not None:
            value, neighbor = results
            self.cache[neighbor] = value
        return results

    def run(self):
        x_best, f_best = TabuSearch.run(self)
        print("# Final Results")
        print("#   Best Value: {}".format(f_best))
        print("#   Best Solution: {}".format(x_best))
        print("#   Num Unique Solutions Evaluated: {}".format(len(self.cache)))
        print("#   Num Solutions Evaluated: {}".format(self.num_moves_evaluated))

        if self.options.verbose:  # pragma: no cover
            print("\nFinal TABU Table")
            if len(self.tabu_time) > 0:
                for move in sorted(self.tabu_time.keys()):
                    print(move, self.tabu_time[move])
            else:
                print("\n  None")
        return x_best, f_best


class AsyncTabuSearch(TabuSearch):
    """
    An asyncronous Tabu Search method that uses a cache, but asynchronously
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
                evaluated[neighbor] = move, value
            else:
                self.num_moves_evaluated += 1
                value = self.cache.get(neighbor, None)
                if value is None:
                    queued[neighbor] = move
                    self.problem.request_solution_value(neighbor)
                    if self.options.debug:
                        print("Requested evaluation - Point {}".format(neighbor))
                else:
                    evaluated[neighbor] = move, value
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
                    print(
                        "Received Results - Point {}  Value {}".format(neighbor, value)
                    )
                    print("Queued: {}".format(list(sorted(queued.keys()))))
                evaluated[neighbor] = queued[neighbor], value  # move, value
                del queued[neighbor]
                self.cache[neighbor] = value
                if self.options.debug:
                    print(
                        "Evaluation Complete - Point {}  Value {}".format(
                            neighbor, value
                        )
                    )

        if self.options.verbose:
            for nhbr in sorted(evaluated.keys()):
                print(
                    "Evaluation Complete - Point {}  Value {}".format(
                        nhbr, self.cache[nhbr]
                    )
                )
        #
        # Process the list of evaluated neighbors
        #
        move_ = None
        x_ = None
        f_ = float("inf")
        tabu = False
        for neighbor in sorted(
            evaluated.keys(), reverse=True
        ):  # Create bias towards solutions with ignored features
            move, value = evaluated[neighbor]
            if move in self.tabu_time and self.tabu_time[move] >= self.iteration:
                if self.options.verbose:
                    print(
                        "#   TABU Move: {}  TABU Time: {}".format(
                            move, self.tabu_time[move]
                        )
                    )
                # Aspiration criteria: Always keep best point found so far
                if value < f_best:
                    f_best = value
                    move_, x_, f_ = move, neighbor, value
                    tabu = True
                    # break
            elif value < f_x:
                move_, x_, f_ = move, neighbor, value
                tabu = False
                # break
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
                print(move, self.tabu_time[move])
        return x_best, f_best
