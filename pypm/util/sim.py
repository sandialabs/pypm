# pypm.util.sim
  
import simpy
import random
from .process_model import ProcessModel


class Simulator(object):

    def __init__(self, *, pm, env=None, data=[]):
        if env is None:
            self.env = simpy.Environment()
        else:                               #pragma: no cover
            self.env = env
        self.pm = pm
        self.data = data

    def _delay_start(self, maxdelay):
        yield self.env.timeout(random.randint(0, maxdelay))

    def _sink(self, pred=[]):
        for p in pred:
            yield p
    
    def _execute_activity(self, *, minlen, maxlen, maxdelay, name, pred):
        for p in pred:
            yield p
        if maxdelay > 0:
            yield self.env.process( self._delay_start(maxdelay) )
        for i in range(random.randint(minlen,maxlen)):
            self.data.append((self.env.now, name)) # Collect data
            yield self.env.timeout(1)

    def build_graph(self, g, activity):
        #
        # Collect the processes of the predecessors.  Generate processes using 
        # build_graph if they are not already generated.
        #
        pred = []
        for _pred in activity['dependencies']:
            if not self.pm[_pred]['id'] in g:
                self.build_graph(g, self.pm[_pred])
            pred.append(g[self.pm[_pred]['id']])
        #
        # Execute the process in simpy
        #
        g[activity['id']] = self.env.process( 
                self._execute_activity( 
                        minlen=activity['duration']['min_hours'], 
                        maxlen=activity['duration']['max_hours'], 
                        maxdelay=activity['max_delay'],
                        name=activity['name'],
                        pred=pred) )

    def create(self, seed):
        random.seed(seed)
        #
        # Create simulation processes for each activity in the graph
        #
        g = {}
        for i in self.pm:
            #
            # The build_graph method works iteratively, storing
            # processes in g.  We can skip generation of an activity 
            # if it was previously generated.
            #
            if not self.pm[i]['id'] in g:
                self.build_graph(g, self.pm[i])
        #
        # The sink activity waits for every other activity to finish
        #
        return self.env.process( self._sink(list(g.values())) )

    def run(self, seed):
        self.data.clear()
        self.env.run( self.create(seed) )

    def organize_observations(self, data, ntimes=0):
        """
        Organize the data observations into a dictionary indexed by
        resource name.  For each resource, an array of length ntimes 
        contains 0/1 values indicating whether the resource was observed.
        """
        mini = 0
        maxi = ntimes
        activities = set()
        for obs in data:
            i,a = obs
            activities.add(a)
            if i+1>maxi:
                maxi = i+1
        observations = {a:[0]*maxi for a in activities}
        for obs in data:
            i,a = obs
            observations[a][i] = 1
        return observations
        

