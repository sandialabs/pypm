import argparse
from pypm.util import runsim


def main():
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
    parser_sim.add_argument('config_file', help='YAML configuration file')
    parser_sim.add_argument('process_file', help='YAML process model file')
    parser_sim.set_defaults(func='sim')

    parser_mip = subparsers.add_parser('mip', help='Run a MIP solver')
    parser_mip.add_argument('--baz', choices='XYZ', help='baz help')
    parser_mip.set_defaults(func='mip')

    args = parser.parse_args()

    if args.func == 'sim':
        runsim(configfile=args.config_file, processfile=args.process_file)
    elif args.func == 'mip':
        print("TODO")

if __name__ == "__main__":
    main()
