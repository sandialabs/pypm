import argparse
import yaml
from pypm.util import runsim
from pypm.mip import runmip_from_datafile
from pypm.vis import create_gannt_chart
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
    parser_mip.set_defaults(func='mip')

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
    parser_vis.set_defaults(func='vis')

    #
    # Subparser for 'pypm chunk'
    #
    # Reduce the time steps in a process or observations
    #
    parser_vis = subparsers.add_parser('chunk', help='Chunk the time steps in a process or observations')
    parser_vis.add_argument('-s', '--step', help='Chunk step.  This is a string describing the chunking step: 2h, 4h, 3:55554h, 8h', default='3:55554')
    parser_vis.add_argument('-c', '--csv', help='CSV file of observations', default=None)
    parser_vis.add_argument('-i', '--index', help='Name of the date-time column in the CSV file', default=None)
    parser_vis.add_argument('-p', '--process', help='YAML process file', default=None)
    parser_vis.add_argument('-o', '--output', help='Name of output file', default=None)
    parser_vis.set_defaults(func='chunk')

    args = parser.parse_args()

    if args.func == 'sim':
        prefix = args.process_file[:-5]
        runsim(configfile=args.config_file, processfile=args.process_file, supervised=not args.unsupervised, outputfile=prefix+"_sim.yaml")

    elif args.func == 'mip':
        results = runmip_from_datafile(datafile=args.datafile, index=int(args.index))
        with open(args.output, 'w') as OUTPUT:
            print("Writing file: {}".format(args.output))
            OUTPUT.write(yaml.dump(results, default_flow_style=None))

    elif args.func == 'vis':
        create_gannt_chart(args.process, args.results, output_fname=args.output, index=args.index)

    elif args.func == 'chunk':
        if args.csv is not None:
            chunk_csv(args.csv, args.output, args.index, args.step)
        elif args.process is not None:
            chunk_process(args.process, args.output, args.step)
        else:
            print("pypm chunk - expected --csv or --process option!")

#
# This is used for interactive testing
#
if __name__ == "__main__":      # pragma: nocover
    main()
