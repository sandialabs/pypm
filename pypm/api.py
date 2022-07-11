import csv
import copy
import yaml
import os.path
from munch import Munch
import pprint
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
            if 'data' in tmp:
                del tmp['data']
            if 'results' in tmp:
                for res in tmp['results']:
                    if 'objective' in res:
                        del res['objective']
                    if 'variables' in res:
                        del res['variables']
            with open(yamlfile, 'w') as OUTPUT:
                print("Writing file: {}".format(yamlfile))
                OUTPUT.write(yaml.dump(tmp, default_flow_style=False))


class SupervisedMIP(object):

    def __init__(self, model=None):
        self.model = model
        self.config = Munch()
        self.constraints = []
        self.objective = Munch(goal="total_match_score")
        self.solver_options = Munch(name="glpk", show_solver_output=None)

    def load_config(self, yamlfile, index=0):
        self.config = load_config(datafile=yamlfile, verbose=PYPM.options.verbose, quiet=PYPM.options.quiet, index=0)

    def generate_schedule(self):
        #
        # Setup the self.config data using class data
        #
        if self.model is None:
            if self.config.model is None:
                if self.objective.goal == "total_match_score":
                    if len(self.config.count_data) > 0:
                        self.config.model = 'GSF-ED'    # model13
                    else:
                        self.config.model = 'GSF'       # model11
                elif self.objective.goal == "minimize_makespan":
                        self.config.model = 'GSF-makespan'
                else:
                    print("Unknown objecive: {}".format(self.objective.goal))
                    return None
        else:
            self.config.model = self.model
        if not hasattr(self.config, 'solver'):
            self.config.solver = self.solver_options.name
        if self.solver_options.show_solver_output is not None:
            self.config.tee = self.solver_options.show_solver_output
        if PYPM.options.verbose is not None:
            self.config.verbose = PYPM.options.verbose
        self.config.objective = self.objective.goal

        if not self.config.quiet:
            print("")
            print("SupervisedMIP Configuration")
            print("---------------------------")
            print("verbose",self.config.verbose)
            print("tee",self.config.tee)
            print("objective",self.config.objective)
            print("model",self.config.model)
            print("solver",self.config.solver)
            print("solver_options")
            pprint.pprint(self.config.solver_options, indent=4)
            print("")

        return Results(runmip(self.config, constraints=self.constraints))

    #
    # Constraint methods
    #

    def add_constraints(self, constraints):
        self.constraints = constraints

    def reset_constraints(self):
        self.constraints = []

    def reset_constraint(self, index):
        self.constraints[index] = None

    def include(self, activity):
        self.constraints.append( Munch(activity=activity, constraint="include") )
        return len(self.constraints)-1

    #def exclude(self, activity):
    #    self.constraints.append( Munch(activity=activity, constraint="exclude") )
    #    return len(self.constraints)-1

    def set_earliest_start_date(self, activity, startdate):
        self.constraints.append( Munch(activity=activity, constraint="earliest_start", startdate=startdate) )
        return len(self.constraints)-1

    def set_latest_start_date(self, activity, startdate):
        self.constraints.append( Munch(activity=activity, constraint="latest_start", startdate=startdate) )
        return len(self.constraints)-1

    def fix_start_date(self, activity, startdate):
        self.constraints.append( Munch(activity=activity, constraint="fix_start", startdate=startdate) )
        return len(self.constraints)-1

    def relax(self, activity):
        self.constraints.append( Munch(activity=activity, constraint="relax") )
        return len(self.constraints)-1

    def relax_start_date(self, activity):
        self.constraints.append( Munch(activity=activity, constraint="relax_start") )
        return len(self.constraints)-1

    def set_activity_duration(self, activity, minval, maxval):
        self.constraints.append( Munch(activity=activity, constraint="activity_duration", minval=minval, maxval=maxval) )
        return len(self.constraints)-1

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

    def minimize_makespan(self):
        """
        Scheduling objective is to minimize the start time of the latest activity
        """
        self.objective = Munch(goal="minimize_makespan")



class UnsupervisedMIP(SupervisedMIP):

    def __init__(self):
        SupervisedMIP.__init__(self)
        self.model = "UPM"

    def generate_schedule(self):
        #
        # Setup the self.config data using class data
        #
        if self.model is None:
            if self.config.model is None:
                if len(self.config.count_data) > 0:
                    self.config.model = 'GSF-ED'    # model13
                else:
                    self.config.model = 'GSF'       # model11
        else:
            self.config.model = self.model
        if not hasattr(self.config, 'solver'):
            self.config.solver = self.solver_options.name
        if self.solver_options.show_solver_output is not None:
            self.config.tee = self.solver_options.show_solver_output
        if PYPM.options.verbose is not None:
            self.config.verbose = PYPM.options.verbose
        self.config.objective = self.objective.goal

        if not self.config.quiet:
            print("")
            print("UnsupervisedMIP Configuration")
            print("-----------------------------")
            print("quiet",self.config.quiet)
            print("verbose",self.config.verbose)
            print("tee",self.config.tee)
            print("objective",self.config.objective)
            print("model",self.config.model)
            print("solver",self.config.solver)
            print("solver_options")
            pprint.pprint(self.config.solver_options, indent=4)
            print("")

        return Results(runmip(self.config, constraints=self.constraints))


class LabelingResults(Results):

    def write_labels(self, csvfile):
        with open(csvfile, 'w') as OUTPUT:
            print("Writing file: {}".format(csvfile))
            writer = csv.writer(OUTPUT)
            writer.writerow(['Feature','Resource'])
            for k,v in self.results['results'][0]['feature_label'].items(): 
                writer.writerow([k,v])


class TabuLabeling(object):

    def __init__(self):
        self.config = Munch()
        self.constraints = []

    def load_config(self, yamlfile, index=0):
        self.config = load_config(datafile=yamlfile, verbose=PYPM.options.verbose, quiet=PYPM.options.quiet, index=0)
        self.config.model = 'tabu'

    def generate_labeling_and_schedule(self, nworkers=1, debug=False):
        return LabelingResults(run_tabu(self.config, constraints=self.constraints, nworkers=nworkers, debug=debug))

    #
    # Constraint methods
    #

    def add_constraints(self, constraints):
        self.constraints = constraints

    def reset_constraints(self):
        self.constraints = []

    def reset_constraint(self, index):
        self.constraints[index] = None

    def include(self, activity):
        self.constraints.append( Munch(activity=activity, constraint="include") )
        return len(self.constraints)-1

    #def exclude(self, activity):
    #    self.constraints.append( Munch(activity=activity, constraint="exclude") )
    #    return len(self.constraints)-1

    def set_earliest_start_date(self, activity, startdate):
        self.constraints.append( Munch(activity=activity, constraint="earliest_start", startdate=startdate) )
        return len(self.constraints)-1

    def set_latest_start_date(self, activity, startdate):
        self.constraints.append( Munch(activity=activity, constraint="latest_start", startdate=startdate) )
        return len(self.constraints)-1

    def fix_start_date(self, activity, startdate):
        self.constraints.append( Munch(activity=activity, constraint="fix_start", startdate=startdate) )
        return len(self.constraints)-1

    def relax(self, activity):
        self.constraints.append( Munch(activity=activity, constraint="relax") )
        return len(self.constraints)-1

    def relax_start_date(self, activity):
        self.constraints.append( Munch(activity=activity, constraint="relax_start") )
        return len(self.constraints)-1

    def set_activity_duration(self, activity, minval, maxval):
        self.constraints.append( Munch(activity=activity, constraint="activity_duration", minval=minval, maxval=maxval) )
        return len(self.constraints)-1


class PYPM_api(object):

    def __init__(self):
        self.options = Munch(verbose=None, quiet=False)

    def supervised_mip(self):
        return SupervisedMIP()

    def unsupervised_mip(self):
        return UnsupervisedMIP()

    def tabu_labeling(self):
        return TabuLabeling()


PYPM = PYPM_api()
