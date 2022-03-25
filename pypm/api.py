import copy
import yaml
import os.path
from munch import Munch
from .mip.runmip import load_config, runmip
from .unsup.ts_labeling import run_tabu


class Results(object):

    def __init__(self, results):
        self.results = results

    def __getitem__(self, key):
        return self.results[key]

    def __setitem__(self, key, value):
        self.results[key] = value

    def write(self, yamlfile, verbose=False):
        if verbose:
            with open(yamlfile, 'w') as OUTPUT:
                print("Writing file: {}".format(yamlfile))
                OUTPUT.write(yaml.dump(self.results, default_flow_style=None))
        else:
            # 
            # Copy the results and delete extraneous stuff used for debugging
            #
            tmp = copy.deepcopy(self.results)
            del tmp['data']
            for res in tmp['results']:
                del res['objective']
                del res['variables']
            with open(yamlfile, 'w') as OUTPUT:
                print("Writing file: {}".format(yamlfile))
                OUTPUT.write(yaml.dump(tmp, default_flow_style=False))

    def print_stats(self):
        print("Matching Statistics")
        print("-"*40)
        print("TODO")


class SupervisedMIP(object):

    def __init__(self, model=None):
        self.model = model
        self.config = Munch()
        self.constraints = []
        self.objective = Munch(goal="total_match_score")

    def load_config(self, yamlfile, index=0):
        self.config = load_config(datafile=yamlfile, verbose=PYPM.options.verbose, index=0)
        if self.model is None:
            if self.config.model is None:
                self.config.model = 'model13'
        else:
            self.config.model = self.model

    def run(self):
        return Results(runmip(self.config, constraints=self.constraints))

    #
    # Constraint methods
    #

    def reset_constraints(self):
        self.constraints = []

    def reset_constraint(self, index):
        self.constraints[index] = None

    def include(self, activity):
        self.constraints.append( Munch(activity=activity, constraint="include") )

    def exclude(self, activity):
        self.constraints.append( Munch(activity=activity, constraint="exclude") )

    def set_earliest_start_date(self, activity, startdate):
        self.constraints.append( Munch(activity=activity, constraint="earliest_start", startdate=startdate) )

    def set_latest_start_date(self, activity, startdate):
        self.constraints.append( Munch(activity=activity, constraint="latest_start", startdate=startdate) )

    def fix_start_date(self, activity, startdate):
        self.constraints.append( Munch(activity=activity, constraint="fix_start", startdate=startdate) )

    def relax(self, activity):
        self.constraints.append( Munch(activity=activity, constraint="relax") )

    def relax_start_date(self, activity):
        self.constraints.append( Munch(activity=activity, constraint="relax_start") )

    #
    # Matching goals
    #
    # total_match_score
    # total_separation_score
    #

    def maximize_total_match_score(self):
        """
        Scheduling objective is to maximize the sum of match scores for all activities.
        """
        self.objective = Munch(goal="total_match_score")

    def maximize_total_separation_score(self):
        """
        Scheduling objective is to maximize the sum of separation scores for all activities.
        """
        self.objective = Munch(goal="total_separation_score")



class UnsupervisedMIP(SupervisedMIP):
    pass


class TabuLabeling(UnsupervisedMIP):

    def __init__(self):
        self.config = Munch()
        self.constraints = []

    def load_config(self, yamlfile, index=0):
        self.config = load_config(datafile=yamlfile, verbose=PYPM.options.verbose, index=0)
        self.config.model = 'tabu'

    def run(self):
        return Results(run_tabu(self.config, constraints=self.constraints))


class PYPM_api(object):

    def __init__(self):
        self.options = Munch(verbose=False)

    def supervised_mip(self):
        return SupervisedMIP()

    def unsupervised_mip(self):
        return UnsupervisedMIP()

    def tabu_labeling(self):
        return TabuLabeling()


PYPM = PYPM_api()
