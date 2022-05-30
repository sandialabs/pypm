import sys
import argparse
import yaml
from pypm.api import PYPM
from pypm.util import runsim
from pypm.vis import create_gannt_chart
from pypm.vis import create_gannt_chart_with_separation_metric
from pypm.vis import create_labelling_matrix
from pypm.chunk import chunk_process, chunk_csv


def main():                     # pragma: nocover
    """
    The entry point for the 'pypm' command-line tool
    """
    #
    # Setup a command-line parser
    #
    parser = argparse.ArgumentParser(description='inference models')
    parser.add_argument('-c', '--catch-errors', action='store_true', default=False,
                    help='Catch exceptions')
    parser.add_argument('-q', '--quiet', action='store_true', default=False,
                    help='Suppress diagnostic')
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
                    help='Verbosity flag')

    subparsers = parser.add_subparsers(title='pypm script',
                                        description='pypm subcommands',
                                        help='sub-command help')

    #
    # Subparser for 'pypm sim'
    #
    # This runs the simulator to generate synthetic observations
    #
    parser_sim = subparsers.add_parser('sim', help='Run simulations to generate observational data')
    parser_sim.add_argument('--unsupervised', '-u', dest='unsupervised', action='store_true',
                            default=False, help='Anonymize observation results')
    parser_sim.add_argument('config_file', help='YAML configuration file')
    parser_sim.add_argument('process_file', help='YAML process model file')
    parser_sim.set_defaults(func='sim')

    #
    # Subparser for 'pypm mip'
    #
    # This runs a MIP to optimize the process match
    #
    parser_mip = subparsers.add_parser('mip', help='Run a MIP solver')
    parser_mip.add_argument('datafile', help='YAML problem file')
    parser_mip.add_argument('-i', '--index', help='Index of problem to run', default=0)
    parser_mip.add_argument('-o', '--output', help='YAML file where results are stored', default="results.yaml")
    parser_mip.add_argument('-v', '--verbose', help='Output verbose results', action="store_true", default=False)
    parser_mip.set_defaults(func='mip')

    #
    # Subparser for 'pypm sup'
    #
    # Perform supervised process matching
    #
    parser_sup = subparsers.add_parser('sup', help='Supervised process matching')
    parser_sup.add_argument('datafile', help='YAML problem file')
    parser_sup.add_argument('-i', '--index', help='Index of problem to run', default=0)
    parser_sup.add_argument('-o', '--output', help='YAML file where results are stored', default="results.yaml")
    parser_sup.add_argument('-v', '--verbose', help='Output verbose results', action="store_true", default=False)
    parser_sup.set_defaults(func='sup')

    #
    # Subparser for 'pypm unsup'
    #
    # Perform unsupervised process matching
    #
    parser_unsup = subparsers.add_parser('unsup', help='Unsupervised process matching')
    parser_unsup.add_argument('datafile', help='YAML problem file')
    parser_unsup.add_argument('-i', '--index', help='Index of problem to run', default=0)
    parser_unsup.add_argument('-o', '--output', help='YAML file where results are stored', default="results.yaml")
    parser_unsup.add_argument('-v', '--verbose', help='Output verbose results', action="store_true", default=False)
    parser_unsup.set_defaults(func='unsup')

    #
    # Subparser for 'pypm vis'
    #
    # Visualize a process match
    #
    parser_vis = subparsers.add_parser('vis', help='Visualize a process match')
    parser_vis.add_argument('process', help='YAML process file')
    parser_vis.add_argument('results', help='YAML results file')
    parser_vis.add_argument('-o', '--output', help='HTML file where results are stored', default=None)
    parser_vis.add_argument('-i', '--index', help='Index of alignment that is visualized', default=0)
    parser_vis.add_argument('-t', '--type', help='Indicates the type of visualization generated: gannt, gannt-separation or labelling', default='gannt')
    parser_vis.add_argument('-r', '--rescale', help='Flag that indicates a rescaling of the y-axis', action='store_true', default=False)
    parser_vis.add_argument('--cmax', help='The max value on the y-axis', default=None)
    parser_vis.add_argument('--cmin', help='The min value on the y-axis', default=None)
    parser_vis.set_defaults(func='vis')

    #
    # Subparser for 'pypm chunk'
    #
    # Reduce the time steps in a process or observations
    #
    parser_chunk = subparsers.add_parser('chunk', help='Chunk the time steps in a process or observations')
    parser_chunk.add_argument('-s', '--step', help='Chunk step.  This is a string describing the chunking step: 2h, 4h, 3:55554h, 8h', default='3:55554')
    parser_chunk.add_argument('-c', '--csv', help='CSV file of observations', default=None)
    parser_chunk.add_argument('-i', '--index', help='Name of the date-time column in the CSV file', default=None)
    parser_chunk.add_argument('-p', '--process', help='YAML process file', default=None)
    parser_chunk.add_argument('-o', '--output', help='Name of output file', default=None)
    parser_chunk.set_defaults(func='chunk')

    args = parser.parse_args()

    if args.func == 'sim':
        prefix = args.process_file[:-5]
        runsim(configfile=args.config_file, processfile=args.process_file, supervised=not args.unsupervised, outputfile=prefix+"_sim.yaml")

    elif args.func == 'mip':
        print("ERROR: The 'pypm mip' sub-command is disabled.")
        print("")
        print("  Use the 'pypm sup' sub-command for supervised process matching.")
        print("  Use the 'pypm unsup' sub-command for unsupervised process matching.")
        print("")
        sys.exit(1)
        #driver = PYPM.supervised_mip()
        #driver.load_config(args.datafile, index=int(args.index))
        #results = driver.generate_schedule()
        #results.write(args.output, verbose=args.verbose)

    elif args.func == 'sup':
        driver = PYPM.supervised_mip()
        driver.load_config(args.datafile, index=int(args.index))
        results = driver.generate_schedule()
        results.write(args.output, verbose=args.verbose)

    elif args.func == 'unsup':
        with open(args.datafile, 'r') as INPUT:
            config = yaml.safe_load(INPUT)
        search_strategy = config['_options'].get('search_strategy','mip')
        if search_strategy == 'tabu':
            driver = PYPM.tabu_labeling()
            driver.load_config(args.datafile, index=int(args.index))
            nworkers = config['_options'].get('nworkers',1)
            results = driver.generate_labeling_and_schedule(nworkers=nworkers)
            results.write(args.output, verbose=args.verbose)

        elif search_strategy == 'mip':
            driver = PYPM.unsupervised_mip()
            driver.load_config(args.datafile, index=int(args.index))
            results = driver.generate_schedule()
            results.write(args.output, verbose=args.verbose)

    elif args.func == 'vis':
        if args.type == 'gannt':
            create_gannt_chart(args.process, args.results, output_fname=args.output, index=int(args.index), cmax=args.cmax, cmin=args.cmin, rescale=args.rescale)
        elif args.type == 'gannt-separation':
            assert args.rescale is False, "Cannot rescale with separation scores"
            create_gannt_chart_with_separation_metric(args.process, args.results, output_fname=args.output, index=int(args.index), cmax=args.cmax, cmin=args.cmin)
        elif args.type == 'labelling':
            create_labelling_matrix(args.process, args.results, output_fname=args.output, index=int(args.index))
        else:
            print("ERROR: Unknown type of visualization '{}'".format(args.type))

    elif args.func == 'chunk':
        if args.csv is not None:
            chunk_csv(args.csv, args.output, args.index, args.step)
        elif args.process is not None:
            chunk_process(args.process, args.output, args.step)
        else:
            print("pypm chunk - expected --csv or --process option!")

    else:
        print("ERROR: unexpected sub-command '{}'".format(args.func))

#
# This is used for interactive testing
#
if __name__ == "__main__":      # pragma: nocover
    main()
