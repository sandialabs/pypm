import os.path
import pandas as pd
import yaml
from pypm.util.load import load_process


def label_data(*, feature_label_csvfile, process_yamlfile, obs_csvfile, labeled_obs_csvfile="labeled_obs.csv", dirname=None):
    #
    # Load data
    #
    assert os.path.exists(feature_label_csvfile), "Cannot find CSV file: {}".format(feature_label_csvfile)
    assert os.path.exists(process_yamlfile), "Cannot find YAML file: {}".format(process_yamlfile)
    assert os.path.exists(obs_csvfile), "Cannot find CSV file: {}".format(obs_csvfile)
    #
    tmp = pd.read_csv(feature_label_csvfile, dtype=str).to_dict()
    labels = {tmp['Feature'][k]:tmp['Resource'][k] for k in tmp['Feature']}
    print(labels)
    process = load_process(process_yamlfile, dirname=dirname)
    obs_df = pd.read_csv(obs_csvfile)
    T = len(obs_df['DateTime'])
    df = pd.DataFrame(columns=["DateTime"]+list(sorted(name for name in process.resources)))
    for resource in process.resources:
        df[resource] = [0]*T
    print("")
    for col in obs_df:
        resource = None
        if col == 'DateTime':
            df[col] = obs_df[col]
            continue
        elif col in labels:
            resource = labels[col]
        elif str(col) in labels:
            resource = labels[str(col)]
        else:
            try:
                ival = int(col)
            except:
                ival = None
            if ival in labels:
                resource = labels[ival]

        if resource is None:
            print("Unlabeled column {} - {}".format(col, type(col)))
        elif resource == 'IGNORE':
            print("Ignored column {} - {}".format(col, type(col)))
        else:
            df[resource] = obs_df[col]
    #
    df.set_index('DateTime')

    print("")
    print("Number of features in data:     {}".format(len(obs_df.columns)-1))
    print("Number of resources in process: {}".format(len(process.resources)))
    print("Number of labeled features:     {}".format(len(labels)))
    print("Number of resources in labeled data: {}".format(len(df.columns)-1))

    print("Writing file: {}".format(labeled_obs_csvfile))
    df.to_csv(labeled_obs_csvfile, index=False)

    
