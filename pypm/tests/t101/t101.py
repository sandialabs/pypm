#
# Simple process matching
#
from pypm.api import PYPM


def run():
    
    pm = PYPM.tabu_labeling()
    pm.load_config("config.yaml")

    # Configure and run solver
    results = pm.generate_labeling_and_schedule()
    
    # Save labels
    results.write_labels("labels.csv")

    # Save results
    results.write("results.yaml")

    return True


if __name__ == "__main__":  # pragma:nocover
    run()
