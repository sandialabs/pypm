import csv
import copy
import yaml
import os.path
from munch import Munch
import pprint
from .mip.runmip import load_config, runmip
from .unsup.run_labeling import run_tabu_labeling


class MatchingResults(object):
    """
    This class contains results generated from the :any:`SupervisedMIP` optimizer.

    TODO: More detail about the nature of these results?
    """

    def __init__(self, results):
        self.results = results

    def __getitem__(self, key):
        """
        Get the results for the specified key.

        Return
        ------
        : Any
            Data for the specified results key.
        """
        return self.results[key]

    def __setitem__(self, key, value):
        """
        Set the results for the specified key.
        """
        self.results[key] = value

    def __delitem__(self, key):
        """
        Delete the results for the specified key.
        """
        del self.results[key]

    def write(self, yamlfile, verbose=False):
        """
        Write a YAML file containing results from process matching.

        Arguments
        ---------
        yamlfile: `str`
            The filename of the YAML results file.
        verbose: `bool`
            If `true`, then print all data in the results object.  Otherwise,
            selectively print the *data* and *results* data.
        """
        if verbose:
            with open(yamlfile, "w") as OUTPUT:
                print("Writing file: {}".format(yamlfile))
                OUTPUT.write(yaml.dump(self.results, default_flow_style=None))
        else:
            #
            # Copy the results and delete extraneous stuff used for debugging
            #
            tmp = copy.deepcopy(self.results)
            if "data" in tmp:
                del tmp["data"]
            if "results" in tmp:
                for res in tmp["results"]:
                    if "objective" in res:
                        del res["objective"]
                    if "variables" in res:
                        del res["variables"]
            with open(yamlfile, "w") as OUTPUT:
                print("Writing file: {}".format(yamlfile))
                OUTPUT.write(yaml.dump(tmp, default_flow_style=False))


class SupervisedMIP(object):
    """
    This class contains coordinates the execution of an integer programming optimizer to 
    find a feasible schedule of process activities that best aligns with data observations.
    """

    def __init__(self, model=None):
        self.model = model
        self.config = Munch()
        self.constraints = []
        self.objective = Munch(goal="total_match_score")
        self.solver_options = Munch(name=None, show_solver_output=None)

    def activities(self):
        """
        Return a generator for the names of the activities in the process model.

        Yields
        ------
        activity: `str`
        """
        for activity in self.config.pm:
            yield activity

    def load_config(self, yamlfile):
        """
        Load a YAML configuration file.

        Arguments
        ---------
        yamlfile: `str`
            The filename of the YAML configuration file.
        """
        self.config = load_config(
            datafile=yamlfile,
            verbose=PYPM.options.verbose,
            quiet=PYPM.options.quiet,
            index=0,
        )
        if self.config.labeling_restrictions:
            for activity in self.activities():
                dummyname = "dummy " + activity
                self.config.pm.resources.add(dummyname, 1)

    def generate_schedule(self):
        """
        Generate a schedule (TODO)

        Returns
        -------
        :any:`pypm.api.MatchingResults`
        """
        #
        # Setup the self.config data using class data
        #
        if self.model is None:
            if self.config.model is None:
                if self.objective.goal == "total_match_score":
                    if len(self.config.count_data) > 0:
                        self.config.model = "GSF-ED"  # model13
                    else:
                        self.config.model = "GSF"  # model11
                elif self.objective.goal == "minimize_makespan":
                    self.config.model = "GSF-makespan"
                else:
                    print("Unknown objecive: {}".format(self.objective.goal))
                    return None
        else:
            self.config.model = self.model
        if self.solver_options.name is not None:
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
            print("verbose", self.config.verbose)
            print("tee", self.config.tee)
            print("debug", self.config.debug)
            print("objective", self.config.objective)
            print("model", self.config.model)
            print("solver", self.config.solver)
            print("solver_options")
            pprint.pprint(self.config.solver_options, indent=4)
            print("")

        return MatchingResults(runmip(self.config, constraints=self.constraints))

    #
    # Constraint methods
    #

    def add_constraints(self, constraints):
        """
        Add the given constraints on the schedule.

        Arguments
        ---------
        constraints: List
            A list of tuples that define constraints on the schedule.
        """
        self.constraints = constraints

    def remove_constraints(self):
        """
        Remove all constraints on the schedule.
        """
        self.constraints = []

    def remove_constraint(self, index):
        """
        Remove the specified constraint on the schedule.

        Arguments
        ---------
        index: `int`
            The index of the constraint that will be removed.
        """
        self.constraints[index] = None

    def include(self, activity):
        """
        Include the specified activity in the schedule.

        Arguments
        ---------
        activity: `str`
            The name of the activity that is included in the schedule.

        Returns
        -------
        : `int`
            The index of the constraint that is added.
        """
        self.constraints.append(Munch(activity=activity, constraint="include"))
        return len(self.constraints) - 1

    def include_all(self):
        """
        Include all activities in the schedule.
        """
        for activity in self.activities():
            self.include(activity)

    def set_earliest_start_date(self, activity, startdate):
        """
        Set the earliest start date for the specified activity in the schedule.

        Arguments
        ---------
        activity: `str`
            The name of the activity.
        startdate: `str`
            The ISO string representation of the earliest start date.

        Returns
        -------
        : `int`
            The index of the constraint that is added.
        """
        self.constraints.append(
            Munch(activity=activity, constraint="earliest_start", startdate=startdate)
        )
        return len(self.constraints) - 1

    def set_earliest_start_dates(self, startdate):
        """
        Set the earliest start date for all activities in the schedule.

        Arguments
        ---------
        startdate: `str`
            The ISO string representation of the earliest start date.
        """
        for activity in self.activities():
            self.set_earliest_start_date(activity, startdate)

    def set_latest_start_date(self, activity, startdate):
        """
        Set the latest start date for the specified activity in the schedule.

        Arguments
        ---------
        activity: `str`
            The name of the activity.
        startdate: `str`
            The ISO string representation of the latest start date.

        Returns
        -------
        : `int`
            The index of the constraint that is added.
        """
        self.constraints.append(
            Munch(activity=activity, constraint="latest_start", startdate=startdate)
        )
        return len(self.constraints) - 1

    def set_latest_start_dates(self, startdate):
        """
        Set the latest start date for all activities in the schedule.

        Arguments
        ---------
        startdate: `str`
            The ISO string representation of the latest start date.
        """
        for activity in self.activities():
            self.set_latest_start_date(activity, startdate)

    def fix_start_date(self, activity, startdate):
        """
        Fix the start date for the specified activity in the schedule.

        Arguments
        ---------
        activity: `str`
            The name of the activity.
        startdate: `str`
            The ISO string representation of the start date.

        Returns
        -------
        : `int`
            The index of the constraint that is added.
        """
        self.constraints.append(
            Munch(activity=activity, constraint="fix_start", startdate=startdate)
        )
        return len(self.constraints) - 1

    def relax(self, activity):
        """
        Relax (unfix) the schedule of the specified activity.

        This method remove constraints associated with the ``include*``, ``set*`` and ``fix*`` methods, for the 
        specified activity.

        Arguments
        ---------
        activity: `str`
            The name of the activity.

        Returns
        -------
        : `int`
            The index of the constraint that is added.
        """
        self.constraints.append(Munch(activity=activity, constraint="relax"))
        return len(self.constraints) - 1

    def relax_all(self):
        """
        Relax (unfix) the schedule of all activities.

        This method remove constraints associated with the ``include*``, ``set*`` and ``fix*`` methods, for all
        activities.
        """
        for activity in self.activities():
            self.relax(activity)

    def relax_start_date(self, activity):
        """
        Relax (unfix) the start date in the schedule of the specified activity.

        This method remove constraints associated with the start date, for the 
        specified activity.

        Arguments
        ---------
        activity: `str`
            The name of the activity.

        Returns
        -------
        : `int`
            The index of the constraint that is added.
        """
        self.constraints.append(Munch(activity=activity, constraint="relax_start"))
        return len(self.constraints) - 1

    def relax_start_dates(self):
        """
        Relax (unfix) the start date in the schedule of all activities.

        This method remove constraints associated with the start date, for all
        activities.
        """
        for activity in self.activities():
            self.relax_start_date(activity)

    def set_activity_duration(self, activity, minval, maxval):
        """
        Set the activity duration in the schedule of the specified activity.

        Arguments
        ---------
        activity: `str`
            The name of the activity.
        minval: `int`
            The minimum number of hours for the activity.
        maxval: `int`
            The maximum number of hours for the activity.

        Returns
        -------
        : `int`
            The index of the constraint that is added.
        """
        self.constraints.append(
            Munch(
                activity=activity,
                constraint="activity_duration",
                minval=minval,
                maxval=maxval,
            )
        )
        return len(self.constraints) - 1

    #
    # Matching goals
    #
    # total_match_score
    # total_separation_score
    #

    def maximize_total_match_score(self):
        """
        Set the scheduling objective to maximize the sum of match scores for all activities.
        """
        self.objective = Munch(goal="total_match_score")

    def maximize_total_separation_score(self):
        """
        Set the scheduling objective to maximize the sum of separation scores for all activities.
        """
        self.objective = Munch(goal="total_separation_score")

    def minimize_makespan(self):
        """
        Set the scheduling objective to minimize the start time of the latest activity
        """
        self.objective = Munch(goal="minimize_makespan")


class UnsupervisedMIP(SupervisedMIP):
    """
    This is a deprecated strategy for performing process matching with unlabeled data.

    The Tabu search method is demonstrably better.
    """
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
                    self.config.model = "GSF-ED"  # model13
                else:
                    self.config.model = "GSF"  # model11
        else:
            self.config.model = self.model
        if not hasattr(self.config, "solver"):
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
            print("quiet", self.config.quiet)
            print("verbose", self.config.verbose)
            print("debug", self.config.debug)
            print("tee", self.config.tee)
            print("objective", self.config.objective)
            print("model", self.config.model)
            print("solver", self.config.solver)
            print("solver_options")
            pprint.pprint(self.config.solver_options, indent=4)
            print("")

        return MatchingResults(runmip(self.config, constraints=self.constraints))


class LabelingResults(MatchingResults):
    """
    This class contains results generated from the :any:`TabuLabeling` optimizer.

    TODO: More detail about the nature of these results?
    """

    def write_labels(self, csvfile):
        """
        Write a CSV file containing results from labeling optimization.

        TODO: document the columns

        TODO: document feature_label and resource_feature_list options.

        Arguments
        ---------
        csvfile: `str`
            The filename of the CSV results file.
        """
        if "feature_label" in self.results["results"][0]:
            with open(csvfile, "w") as OUTPUT:
                print("Writing file: {}".format(csvfile))
                writer = csv.writer(OUTPUT)
                writer.writerow(["Feature", "Resource"])
                for k, v in self.results["results"][0]["feature_label"].items():
                    writer.writerow([k, v])
        elif "resource_feature_list" in self.results["results"][0]:
            with open(csvfile, "w") as OUTPUT:
                print("Writing file: {}".format(csvfile))
                writer = csv.writer(OUTPUT)
                writer.writerow(["Resource", "Feature"])
                for k, v in self.results["results"][0]["resource_feature_list"].items():
                    for f in v:
                        writer.writerow([k, f])


class TabuLabeling(object):
    """
    This class contains coordinates the execution of a tabu search optimizer to 
    find the association of data observations features to resources in a process model that
    maximizes an information separation score.
    """

    def __init__(self):
        self.config = Munch()
        self.constraints = []

    def activities(self):
        """
        Return a generator for the names of the activities in the process model.

        Yields
        ------
        activity: `str`
        """
        for activity in self.config.pm:
            yield activity

    def load_config(self, yamlfile):
        """
        Load a YAML configuration file.

        Arguments
        ---------
        yamlfile: `str`
            The filename of the YAML configuration file.
        """
        self.config = load_config(
            datafile=yamlfile,
            verbose=PYPM.options.verbose,
            quiet=PYPM.options.quiet,
            index=0,
        )
        self.config.model = "tabu"
        #
        # Process the labeling restrictions file
        #
        if self.config.labeling_restrictions:
            for activity in self.activities():
                dummyname = "dummy " + activity
                self.config.pm.resources.add(dummyname, 1)

            if not os.path.exists(self.config.labeling_restrictions):
                raise RuntimeError(
                    "Unknown labeling restrictions file: {}".format(
                        self.config.labeling_restrictions
                    )
                )

            tmp = {}
            with open(self.config.labeling_restrictions, "r") as INPUT:
                restrictions = yaml.load(INPUT, Loader=yaml.Loader)
                for r in restrictions:
                    assert (
                        "resourceName" in r
                    ), "Missing data field 'resourceName' in {}-th labeling restriction declared in {}".format(
                        i, self.config.labeling_restrictions
                    )
                    name = r["resourceName"]
                    assert (
                        name in self.config.pm.resources
                    ), "Missing resource {} in process resource list".format(name)
                    assert name not in tmp, "Resource {} declared twice in {}".format(
                        name, self.config.labeling_restrictions
                    )
                    tmp[name] = dict(required=[], optional=[])

                    assert (
                        "like" in r or "knownFeature" in r
                    ), "Missing data field 'knownFeature' for resource {} declared in {}".format(
                        name, self.config.labeling_restrictions
                    )
                    assert (
                        "like" in r or "possibleFeature" in r
                    ), "Missing data field 'knownFeature' for resource {} declared in {}".format(
                        name, self.config.labeling_restrictions
                    )
                    if "knownFeature" in r:
                        for f in r["knownFeature"]:
                            assert (
                                f in self.config.obs["observations"]
                            ), "Missing feature {} in data observations (known features for resource {})".format(
                                f, name
                            )
                            tmp[name]["required"].append(f)
                    if "possibleFeature" in r:
                        for f in r["possibleFeature"]:
                            assert (
                                f in self.config.obs["observations"]
                            ), "Missing feature {} in data observations (possible features for resource {})".format(
                                f, name
                            )
                            tmp[name]["optional"].append(f)

                for r in restrictions:
                    name = r["resourceName"]
                    if "like" in r:
                        tmp[name] = tmp[r["like"]]

            self.config.labeling_restrictions = tmp

    def generate_labeling_and_schedule(self, nworkers=None, debug=None, setup_ray=True):
        """
        Generate a labeling and optimal schedule (TODO)

        Returns
        -------
        :any:`pypm.api.LabelingResults`
        """
        nworkers = nworkers
        if nworkers is None:
            nworkers = self.config.nworkers
        if nworkers is None:
            nworkers = 1
        debug = debug
        if debug is None:
            debug = self.config.debug
        if debug is None:
            debug = False
    
        if not self.config.quiet:
            print("")
            print("Tabu Labeling Configuration")
            print("---------------------------")
            print("quiet", self.config.quiet)
            print("verbose", self.config.verbose)
            print("debug", debug)
            print("tee", self.config.tee)
            print("process", self.config.process)
            print("tabu_model", self.config.tabu_model)
            print("solver", self.config.solver)
            print("nworkers", nworkers)
            print("setup_ray", setup_ray)
            print("label_representation", self.config.label_representation)
            print("labeling_restrictions", self.config.labeling_restrictions is not None)
            print("max_iterations", self.config.max_iterations)
            print("stall_count", self.config.stall_count)
            print("solver_options")
            pprint.pprint(self.config.solver_options, indent=4)
            print("")

        return LabelingResults(
            run_tabu_labeling(
                self.config,
                constraints=self.constraints,
                nworkers=nworkers,
                debug=debug,
                setup_ray=setup_ray,
            )
        )

    #
    # Constraint methods
    #

    def add_constraints(self, constraints):
        """
        Add the given constraints on the schedule.

        Arguments
        ---------
        constraints: List
            A list of tuples that define constraints on the schedule.
        """
        self.constraints = constraints

    def remove_constraints(self):
        """
        Remove all constraints on the schedule.
        """
        self.constraints = []

    def remove_constraint(self, index):
        """
        Remove the specified constraint on the schedule.

        Arguments
        ---------
        index: `int`
            The index of the constraint that will be removed.
        """
        self.constraints[index] = None

    def include(self, activity):
        """
        Include the specified activity in the schedule.

        Arguments
        ---------
        activity: `str`
            The name of the activity that is included in the schedule.

        Returns
        -------
        : `int`
            The index of the constraint that is added.
        """
        self.constraints.append(Munch(activity=activity, constraint="include"))
        return len(self.constraints) - 1

    def include_all(self):
        """
        Include all activities in the schedule.
        """
        for activity in self.activities():
            self.include(activity)

    def set_earliest_start_date(self, activity, startdate):
        """
        Set the earliest start date for the specified activity in the schedule.

        Arguments
        ---------
        activity: `str`
            The name of the activity.
        startdate: `str`
            The ISO string representation of the earliest start date.

        Returns
        -------
        : `int`
            The index of the constraint that is added.
        """
        self.constraints.append(
            Munch(activity=activity, constraint="earliest_start", startdate=startdate)
        )
        return len(self.constraints) - 1

    def set_earliest_start_dates(self, startdate):
        """
        Set the earliest start date for all activities in the schedule.

        Arguments
        ---------
        startdate: `str`
            The ISO string representation of the earliest start date.
        """
        for activity in self.activities():
            self.set_earliest_start_date(activity, startdate)

    def set_latest_start_date(self, activity, startdate):
        """
        Set the latest start date for the specified activity in the schedule.

        Arguments
        ---------
        activity: `str`
            The name of the activity.
        startdate: `str`
            The ISO string representation of the latest start date.

        Returns
        -------
        : `int`
            The index of the constraint that is added.
        """
        self.constraints.append(
            Munch(activity=activity, constraint="latest_start", startdate=startdate)
        )
        return len(self.constraints) - 1

    def set_latest_start_dates(self, startdate):
        """
        Set the latest start date for all activities in the schedule.

        Arguments
        ---------
        startdate: `str`
            The ISO string representation of the latest start date.
        """
        for activity in self.activities():
            self.set_latest_start_date(activity, startdate)

    def fix_start_date(self, activity, startdate):
        """
        Fix the start date for the specified activity in the schedule.

        Arguments
        ---------
        activity: `str`
            The name of the activity.
        startdate: `str`
            The ISO string representation of the start date.

        Returns
        -------
        : `int`
            The index of the constraint that is added.
        """
        self.constraints.append(
            Munch(activity=activity, constraint="fix_start", startdate=startdate)
        )
        return len(self.constraints) - 1

    def relax(self, activity):
        """
        Relax (unfix) the schedule of the specified activity.

        This method remove constraints associated with the ``include*``, ``set*`` and ``fix*`` methods, for the 
        specified activity.

        Arguments
        ---------
        activity: `str`
            The name of the activity.

        Returns
        -------
        : `int`
            The index of the constraint that is added.
        """
        self.constraints.append(Munch(activity=activity, constraint="relax"))
        return len(self.constraints) - 1

    def relax_all(self):
        """
        Relax (unfix) the schedule of all activities.

        This method remove constraints associated with the ``include*``, ``set*`` and ``fix*`` methods, for all
        activities.
        """
        for activity in self.activities():
            self.relax(activity)

    def relax_start_date(self, activity):
        """
        Relax (unfix) the start date in the schedule of the specified activity.

        This method remove constraints associated with the start date, for the 
        specified activity.

        Arguments
        ---------
        activity: `str`
            The name of the activity.

        Returns
        -------
        : `int`
            The index of the constraint that is added.
        """
        self.constraints.append(Munch(activity=activity, constraint="relax_start"))
        return len(self.constraints) - 1

    def relax_start_dates(self):
        """
        Relax (unfix) the start date in the schedule of all activities.

        This method remove constraints associated with the start date, for all
        activities.
        """
        for activity in self.activities():
            self.relax_start_date(activity)

    def set_activity_duration(self, activity, minval, maxval):
        """
        Set the activity duration in the schedule of the specified activity.

        Arguments
        ---------
        activity: `str`
            The name of the activity.
        minval: `int`
            The minimum number of hours for the activity.
        maxval: `int`
            The maximum number of hours for the activity.

        Returns
        -------
        : `int`
            The index of the constraint that is added.
        """
        self.constraints.append(
            Munch(
                activity=activity,
                constraint="activity_duration",
                minval=minval,
                maxval=maxval,
            )
        )
        return len(self.constraints) - 1


class PYPM_api(object):
    def __init__(self):
        self.options = Munch(verbose=None, quiet=False)

    def supervised_mip(self):
        """ Initialize a solver interface for labeled process matching.

        Returns
        -------
        :any:`pypm.api.SupervisedMIP`
        """
        return SupervisedMIP()

    def unsupervised_mip(self):
        return UnsupervisedMIP()

    def tabu_labeling(self):
        """ Initialize a solver interface for unlabeled process matching.

        Returns
        -------
        :any:`pypm.api.TabuLabeling`
        """
        return TabuLabeling()


PYPM = PYPM_api()
""" The main pypm interface object (:any:`pypm.api.PYPM_api`).

`PYPM` is a global object that contains methods to initialize
different process matching solvers.

Examples
--------

A process matching solver is created for labeled data using the `supervised_mip` method:

>>> pm = PYPM.supervised_mip()
"""
