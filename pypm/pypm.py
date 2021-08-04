import argparse
import yaml
from pypm.util import runsim
from pypm.mip import runmip_from_datafile


def main():                     # pragma: nocover
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

    parser_sim = subparsers.add_parser('sim', help='Run simulations to generate observational data')
    parser_sim.add_argument('--unsupervised', '-u', dest='unsupervised', action='store_true',
                            default=False, help='Anonmize observation results')
    parser_sim.add_argument('config_file', help='YAML configuration file')
    parser_sim.add_argument('process_file', help='YAML process model file')
    parser_sim.set_defaults(func='sim')

    parser_mip = subparsers.add_parser('mip', help='Run a MIP solver')
    parser_mip.add_argument('datafile', help='YAML problem file')
    parser_mip.add_argument('index', help='Index of problem to run', default=0)
    parser_mip.set_defaults(func='mip')

    args = parser.parse_args()

    if args.func == 'sim':
        prefix = processfile[:-5]
        runsim(configfile=args.config_file, processfile=args.process_file, supervised=not args.unsupervised, outputfile=prefix+"_sim.yaml")
    elif args.func == 'mip':
        results = runmip_from_datafile(datafile=args.datafile, index=int(args.index))
        with open('results.yaml', 'w') as OUTPUT:
            print("Writing file: results.yaml")
            OUTPUT.write(yaml.dump(results, default_flow_style=None))

if __name__ == "__main__":      # pragma: nocover
    main()
