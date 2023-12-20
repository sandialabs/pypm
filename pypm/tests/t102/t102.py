#
# Simple process matching
#
from pypm.api import PYPM
from pypm.util import label_data


def run():
    
    pm = PYPM.tabu_labeling()
    pm.load_config("config.yaml")

    # Configure and run solver
    results = pm.generate_labeling_and_schedule()
    
    # Save labels
    results.write_labels("labels.csv")

    # Save results
    results.write("results.yaml")

    # Generate labeled data
    label_data(feature_label_csvfile='./labels.csv',
                        process_yamlfile='./process.yaml',
                        obs_csvfile='./unlabeled.csv',
                        labeled_obs_csvfile='./labeled.csv')

    return True


if __name__ == "__main__":  # pragma:nocover
    run()
