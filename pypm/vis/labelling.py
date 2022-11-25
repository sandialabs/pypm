# pypm.vis.gannt

import os.path
import yaml


def create_labelling_matrix(process_fname, results_fname, output_fname=None, index=0):
    assert os.path.exists(process_fname), "Unknown file {}".format(process_fname)
    assert os.path.exists(results_fname), "Unknown file {}".format(results_fname)
    import pandas as pd

    # import plotly.express as px
    import plotly.graph_objects as go

    print("Reading {}".format(process_fname))
    with open(process_fname, "r") as INPUT:
        process = yaml.safe_load(INPUT)
    print("Reading {}".format(results_fname))
    with open(results_fname, "r") as INPUT:
        results = yaml.load(INPUT, Loader=yaml.Loader)

    assert results["model"] in [
        "model3",
        "model4",
        "model5",
        "model6",
        "model7",
        "model8",
        "model10",
    ], "Cannot visualize results in {}.  Expects results generated for model3-model8,model10.".format(
        results_fname
    )
    assert (
        len(results["results"]) > index
    ), "Cannot visualize the {}-th process match in {}.  This file only has {} matches.".format(
        index, results_fname, len(results["results"])
    )

    print("Processing results")
    mmap = {v: i for i, v in enumerate(results["indicators"])}
    m = {r: {i: "" for i in results["indicators"]} for r in process["resources"]}
    # print(mmap)
    # print(m)
    for mopt, v in results["results"][index]["variables"]["m"].items():
        # print("HERE",mopt)
        if v > 0:
            m[mopt[0]][mopt[1]] = v

    header = ["Resources"] + results["indicators"]
    data = {h: [] for h in header}
    # print(m)
    for i in m:
        data["Resources"].append(i)
        for ii, v in enumerate(results["indicators"]):
            data[v].append(m[i][v])

    df = pd.DataFrame(data)
    print(df)
    #
    # Gannt chart for scheduled tasks
    #
    print("Generating Figure")
    headerColor = "grey"
    rowEvenColor = "lightgrey"
    rowOddColor = "white"
    if len(df["Resources"]) % 2 == 1:
        fill_colors = [
            ["lightgrey"] + ["white", "lightgrey"] * (len(df["Resources"]) // 2)
        ]
    else:
        fill_colors = [["white", "lightgrey"] * (len(df["Resources"]) // 2)]
    fig = go.Figure(
        data=[
            go.Table(
                header=dict(
                    values=header,
                    fill_color="grey",
                    line_color="darkslategray",
                    font=dict(color="white", size=12),
                ),
                cells=dict(
                    values=[df[h] for h in header],
                    fill_color=fill_colors,
                    line_color="darkslategray",
                ),
            )
        ]
    )
    if output_fname is None:
        fig.show()
    elif output_fname.endswith(".html"):
        print("Writing {}".format(output_fname))
        fig.write_html(output_fname)
    else:
        print("Writing {}".format(output_fname))
        fig.write_image(output_fname)
