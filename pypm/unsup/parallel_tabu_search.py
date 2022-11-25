import time
import random
import ray
import ray.util.queue
from .tabu_search import TabuSearchProblem


@ray.remote(num_cpus=1)
class TabuSearchWorker(object):
    def __init__(self, problem):
        self.problem = problem

    def run(self, point_queue, results_queue):
        #
        # NOTE - Need to rework this to allow overlapping communication
        #           and computation
        while True:
            point = point_queue.get(block=True)
            value, results = self.problem.compute_results(point)
            results_queue.put((point, value, results))


class RayTabuSearchProblem(TabuSearchProblem):
    def __init__(self, *, problem, nworkers):
        TabuSearchProblem.__init__(self)
        self.problem = problem
        #
        nworkers = ray.available_resources() if nworkers is None else nworkers
        problem_obj = ray.put(problem)
        self.workers = [TabuSearchWorker.remote(problem_obj) for i in range(nworkers)]
        self.requests_queue = ray.util.queue.Queue()
        self.results_queue = ray.util.queue.Queue()
        for w in self.workers:
            w.run.remote(self.requests_queue, self.results_queue)

    def initial_solution(self):
        return self.problem.initial_solution()

    def moves(self, solution, value):
        return self.problem.moves(solution, value)

    def compute_results(self, solution):
        self.request_results(solution)
        solution_results = self.get_requested_results()
        while solution_results == None:
            time.sleep(0.01)
            solution_results = self.get_requested_results()
        return solution_results[1], solution_results[2]

    def request_results(self, solution):
        return self.requests_queue.put_nowait(solution)

    def cancel_request(self, solution):
        #
        # Cancel a request to compute results for a solution
        # Returns: None
        #
        # TODO - Can we do this with Ray?
        #
        pass

    def cancel_all_requests(self):
        #
        # Cancel all requests to compute results for solutions
        # Returns: None
        #
        # TODO - Can we do this with Ray?
        #
        pass

    def get_requested_results(self):
        if self.results_queue.empty():
            return None
        return self.results_queue.get()

    def write_solution_to_file(self, iteration, point, value, filename):
        self.problem.write_solution_to_file(iteration, point, value, filename)
