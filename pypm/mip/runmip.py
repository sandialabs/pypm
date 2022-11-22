# pymp.mip.runmip


import datetime
import yaml
import pprint
import csv
import sys
from munch import Munch
import pandas as pd
from os.path import join
import os.path
from pypm.util.load import load_process
from pypm.mip.models import create_model
import pyomo.environ as pe
from pyomo.opt import TerminationCondition as tc


def load_observations(*, data, dirname, index, count_data, strict=False):
    observations_ = {}
    header = []
    if type(data) is list:
        observations = data[index]["observations"]
        assert (
            type(observations) is dict
        ), "Expected observations to be a dictionary or a list of CSV files"
        for key in observations:
            ntimesteps = len(observations[key])
            break
        dt = {
            i: str(datetime.datetime(year=2020, month=1, day=i // 24 + 1, hour=i % 24))
            for i in range(ntimesteps)
        }
        observations_ = observations
    else:
        fname = data["filename"]
        if not dirname is None:
            fname = join(dirname, fname)
        index = data.get("index", "DateTime")
        if fname.endswith(".csv"):
            df = pd.read_csv(fname)
            observations_ = df.to_dict(orient="list")
            header = list(df.columns)
        else:  # pragma: no cover
            raise "Unknown file format"
        dt = observations_.get(index, None)
        if not dt is None:
            del observations_[index]
            header.remove(index)
            dt = dict(zip(range(len(dt)), dt))

    #
    # Check that dates are strictly increasing
    #
    if not dt is None:
        prev = dt[0]
        for i in range(1, len(dt)):
            assert (
                prev < dt[i]
            ), "Expecting date-time values to be strictly increasing.  The date {} appears before {} in the data set.".format(
                prev, dt[i]
            )
            prev = dt[i]
    #
    # Check that observations are in the interval [0,1]
    #
    for key in observations_:
        if key in count_data:
            for row in range(len(observations_[key])):
                val = observations_[key][row]
                if val < 0:  # pragma: no cover
                    print(
                        "WARNING: invalid observation value {} (col={}, row={}). Moving value to 0.".format(
                            val, key, row
                        )
                    )
                    observations_[key][row] = 0
                elif type(val) is float and not val.is_integer():  # pragma: no cover
                    print(
                        "WARNING: invalid observation value {} (col={}, row={}). Moving value to {}.".format(
                            val, key, row, int(val)
                        )
                    )
                    observations_[key][row] = int(val)
        else:
            for row in range(len(observations_[key])):
                val = observations_[key][row]
                # print(key,row,val)
                if val < 0 or val > 1:
                    if strict:  # pragma: no cover
                        print(
                            "ERROR: invalid observation value {} (col={}, row={}). Must be in the interval [0,1].".format(
                                val, key, row
                            )
                        )
                        sys.exit(1)
                    else:
                        if val < 0:  # pragma: no cover
                            print(
                                "WARNING: invalid observation value {} (col={}, row={}). Moving value to 0.".format(
                                    val, key, row
                                )
                            )
                            observations_[key][row] = 0
                        if val > 1:  # pragma: no cover
                            print(
                                "WARNING: invalid observation value {} (col={}, row={}). Moving value to 1.".format(
                                    val, key, row
                                )
                            )
                            observations_[key][row] = 1
    #
    # Get the value of 'timesteps'
    #
    # NOTE: we are ignoring the value of 'timesteps'
    #
    for key in observations_:
        timesteps = len(observations_[key])
        break

    return Munch(
        observations=observations_, header=header, timesteps=timesteps, datetime=dt
    )


def perform_optimization(*, M, solver, options, tee, debug):
    opt = pe.SolverFactory(solver)
    if tee:  # pragma: no cover
        print("-- Solver Output Begins --")
    if options:
        results = opt.solve(M.M, options=options, tee=tee)
    else:
        results = opt.solve(M.M, tee=tee)
    if tee:  # pragma: no cover
        print("-- Solver Output Ends --")
    if debug:  # pragma:nocover
        M.M.pprint()
        M.M.display()
    if results.solver.termination_condition not in {
        tc.optimal,
        tc.locallyOptimal,
        tc.feasible,
    }:
        return None
    return M.summarize()


def load_config(
    *,
    datafile=None,
    data=None,
    index=0,
    model=None,
    tee=None,
    solver=None,
    dirname=None,
    debug=False,
    verbose=None,
    quiet=None,
    seed=123456789237498
):
    if data is None:
        assert datafile is not None
        with open(datafile, "r") as INPUT:
            data = yaml.safe_load(INPUT)

    options = data["_options"]
    savefile = options.get("write", None)
    tee = options.get("tee", False) if tee is None else tee
    seed = options.get("seed", False) if seed is None else seed
    verbose = options.get("verbose", False) if verbose is None else verbose
    quiet = options.get("quiet", False) if quiet is None else quiet
    if verbose:
        quiet = False
    if quiet:  # pragma: no cover
        verbose = False
    model = options.get("model", None) if model is None else model
    solver = options.get("solver", "glpk") if solver is None else solver
    solver_options = options.get("solver_options", {})
    count_data = set(options.get("count_data", []))
    search_strategy = options.get("search_strategy", "mip")

    if dirname is None and datafile is not None:
        dirname = os.path.dirname(os.path.abspath(datafile))
    pm = load_process(options["process"], dirname=dirname)
    label_representation = options.get("label_representation", None)
    labeling_restrictions = options.get("labeling_restrictions", None)
    if labeling_restrictions is not None:
        if os.path.exists(os.path.join(dirname, labeling_restrictions)):
            labeling_restrictions = os.path.join(dirname, labeling_restrictions)

    obs = load_observations(
        data=data["data"], dirname=dirname, index=index, count_data=count_data
    )

    if model in ["model11", "GSF", "model13", "GSF-ED", "GSF-makespan", "XSF"]:
        #
        # For supervised matching, we can confirm that the observations
        # have the right labels
        #
        tmp1 = set(obs.observations.keys())
        tmp2 = set([name for name in pm.resources])
        assert tmp1.issubset(tmp2), (
            "For supervised process matching, we expect the observations to have labels in the process model.  The following are unknown resource labels: "
            + str(tmp1 - tmp2)
        )

    return Munch(
        savefile=savefile,
        tee=tee,
        verbose=verbose,
        quiet=quiet,
        model=model,
        solver=solver,
        solver_options=solver_options,
        pm=pm,
        search_strategy=search_strategy,
        obs=obs,
        options=options,
        datafile=datafile,
        index=index,
        debug=debug,
        seed=seed,
        process=options["process"],
        count_data=count_data,
        labeling_restrictions=labeling_restrictions,
        label_representation=label_representation,
    )


def runmip(config, constraints=[]):
    if not config.quiet:
        print("Creating model")
    M = create_model(config.model)
    if M is None:  # pragma: no cover
        print(
            'ERROR: using deprecated model "'
            + config.model
            + '".  Use the old_runmip() function.'
        )
        sys.exit(0)

    M(config, constraints=constraints)

    #
    # Save the optimization formulation.  This is used for
    # debugging.
    #
    if config.savefile:  # pragma: no cover
        if not config.quiet:
            print("Writing file:", config.savefile)
        M.M.write(config.savefile, io_options=dict(symbolic_solver_labels=True))
        return dict()

    #
    # Setup results YAML data
    #
    res = dict(
        solver=dict(
            search_strategy=config.search_strategy, model=dict(name=config.model)
        ),
        data=dict(
            datafile=config.datafile,
            timesteps=config.obs.timesteps,
            indicators=config.obs.header,
            index=config.index,
        ),
        results=[],
    )
    res["data"]["datetime"] = config.obs.datetime

    if config.search_strategy == "mip":
        #
        # Perform optimization
        #
        if not config.quiet:
            print("Optimizing model")
        results = perform_optimization(
            M=M,
            solver=config.solver,
            options=config.solver_options,
            tee=config.tee,
            debug=config.debug,
        )

        #
        # Append results to YAML data
        #
        res["results"].append(results)

    return res
