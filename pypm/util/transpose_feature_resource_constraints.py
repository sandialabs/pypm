import yaml
import pandas as pd


def get_resources_from_process(process):

    resources = list(process["resources"].keys())

    # Add proxy resources for activities without resources
    for activity in process["activities"]:
        # TODO: Do we want just the empty activities or all the activities?
        # if len(activity["resources"]) == 0:
        resources.append("dummy " + activity["name"])

    return set(resources)


def get_features_from_data(dataframe):

    return set(dataframe.columns.tolist())


def _infer_input(mapping):
    """Infer if input mapping is features-to-resources or resources-to-features."""
    if "featureName" in mapping[0]:
        return "Feature"
    elif "resourceName" in mapping[0]:
        return "Resource"
    else:
        raise ValueError("Unknown mapping")


def transpose(f2r, dest_items, src="Feature"):
    """Transpose a mapping to the reversed frame (e.g. features-to-resources to resources-to-features).

    >>> f2r = [{"featureName": "foo", "knownResource": ["bar"], "possibleResource": []},
    ...        {"featureName": "baz", "knownResource": [], "possibleResource": []}]
    >>> transpose(f2r, ["bar", "qux"], src="Feature")
    [{'resourceName': 'bar', 'knownFeature': ['foo'], 'possibleFeature': []},
     {'resourceName': 'qux', 'knownFeature': [], 'possibleFeature': []}]
    """
    if src == "Feature":
        dest = "Resource"
        src_name_key = "featureName"
        dest_name_key = "resourceName"
    elif src == "Resource":
        dest = "Feature"
        src_name_key = "resourceName"
        dest_name_key = "featureName"
    else:
        raise ValueError(f"Unknown src {src}")

    r2f = {entry: {f"known{src}": [], f"possible{src}": []} for entry in dest_items}

    for entry in f2r:
        for resource in entry[f"known{dest}"]:
            r2f[resource][f"known{src}"].append(entry[src_name_key])

        for resource in entry[f"possible{dest}"]:
            r2f[resource][f"possible{src}"].append(entry[src_name_key])

    # Roll dict into list mapping
    return [{**{dest_name_key: key}, **value} for key, value in r2f.items()]


def expand_like(mapping, name_key="featureName"):
    """Expand the 'like' entries present in the mapping.

    >>> mapping = [{"featureName": "foo", "knownResource": ["bar"], "possibleResource": []},
    ...            {"featureName": "baz", "like": "foo"}]
    >>> expand_like(mapping, name_key="featureName")
    [{'featureName': 'foo', 'knownResource': ['bar'], 'possibleResource': []},
     {'featureName': 'baz', 'knownResource': ['bar'], 'possibleResource': []}]
    """

    dict_mapping = {entry[name_key]: entry for entry in mapping}

    new_mapping = []

    for entry in mapping:
        if "like" in entry:
            # Copy the fields over
            this = dict_mapping[entry[name_key]]
            that = dict_mapping[entry["like"]]
            new_this = {k: this.get(k, that[k]) for k in that}
            new_mapping.append(new_this)
        else:
            new_mapping.append(entry)

    return new_mapping


def contract_like(mapping, name_key="featureName"):
    """Contract the 'like' entries present in the mapping.

    >>> mapping = [{"featureName": "foo", "knownResource": ["bar"], "possibleResource": []},
    ...            {"featureName": "baz", "knownResource": ["bar"], "possibleResource": []}]
    >>> contract_like(mapping, name_key="featureName")
    [{'featureName': 'foo', 'knownResource': ['bar'], 'possibleResource': []},
     {'featureName': 'baz', 'like': 'foo'}]
    """
    entry_hash = {}

    new_mapping = []

    for entry in mapping:
        # Create a hash for all the items in the entry except the name
        name_filtered_entry = frozenset(
            {k: tuple(v) for k, v in entry.items() if k != name_key}.items()
        )

        # If it is already in the hash, add a "like" entry to the mapping
        if name_filtered_entry in entry_hash:
            new_mapping.append(
                {name_key: entry[name_key], "like": entry_hash[name_filtered_entry]}
            )
        # If it is not in the hash, update the hash and add the entry to the mapping
        else:
            entry_hash[name_filtered_entry] = entry[name_key]
            new_mapping.append(entry)

    return new_mapping


_name_key = {"Feature": "featureName", "Resource": "resourceName"}


def transpose_constraints_file(
    constraints_file, data_file, process_file, output_file, contract_transpose=True
):

    # Load the list of declared resources in the process
    with open(process_file, "r") as f:
        process = yaml.safe_load(f)
    resources = get_resources_from_process(process)

    # Load the list of declared features in the input data
    dataframe = pd.read_csv(data_file, index_col="DateTime")
    features = get_features_from_data(dataframe)

    # Load the defined constraints
    with open(constraints_file, "r") as f:
        constraints = yaml.safe_load(f)

    # Infer if features-to-resources or resources-to-features
    src = _infer_input(constraints)

    # Expand any "like" entries
    expanded_constraints = expand_like(constraints, name_key=_name_key[src])

    constraints_transpose = transpose(
        expanded_constraints,
        dest_items={"Feature": resources, "Resource": features}[src],
        src=src,
    )

    if contract_transpose:
        src = _infer_input(constraints_transpose)
        constraints_transpose = contract_like(
            constraints_transpose, name_key=_name_key[src]
        )

    with open(output_file, "w") as f:
        yaml.dump(constraints_transpose, f)

    return constraints_transpose


def main():
    """Entry point for transpose constraints file."""
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "constraints_file",
        type=str,
        help="YAML file containing constraints to transpose",
    )
    parser.add_argument(
        "data_file", type=str, help="CSV file containing input features data"
    )
    parser.add_argument(
        "process_file",
        type=str,
        help="YAML file containing process model specification",
    )
    parser.add_argument(
        "output_file", type=str, help="YAML output file for transposed constraints"
    )
    parser.add_argument(
        "--dont-contract-transpose",
        action="store_false",
        dest="contract_transpose",
        help="do not simplify output transpose with like semantic",
    )
    args = parser.parse_args()

    output = transpose_constraints_file(
        constraints_file=args.constraints_file,
        data_file=args.data_file,
        process_file=args.process_file,
        output_file=args.output_file,
        contract_transpose=args.contract_transpose,
    )


if __name__ == "__main__":
    main()
