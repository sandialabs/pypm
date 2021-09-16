# pypm.vis.gannt

import os.path
import yaml


def create_gannt_chart(process_fname, results_fname, output_fname=None, index=0, linear=True):
    assert os.path.exists(process_fname), "Unknown file {}".format(process_fname)
    assert os.path.exists(results_fname), "Unknown file {}".format(results_fname)
    import pandas as pd
    import plotly.express as px

    with open(process_fname, 'r') as INPUT:
        process = yaml.safe_load(INPUT)
    with open(results_fname, 'r') as INPUT:
        results = yaml.load(INPUT)

    assert results['model'] in ['model3', 'model4'], "Cannot visualize results in {}.  Expects results generated for model3 or model4.".format(results_fname)
    assert len(results['results']) > index, "Cannot visualize the {}-th process match in {}.  This file only has {} matches.".format(index, results_fname, len(results['results']))

    alignment = results['results'][index]['alignment']
    data = {'Activity':[], 'Start':[], 'Stop':[]}
    for activity in process['activities']:
        name = activity['name']
        if name not in alignment:
            print("Warning: Activity {} was not included in the process match".format(name))
            data['Activity'].append(name)
            data['Start'].append(0)
            data['Stop'].append(0)
        if 'last' not in alignment[name]:
            print("Warning: Activity {} does not appear to end".format(name))
            data['Activity'].append(name)
            data['Start'].append(alignment[name]['first'])
            data['Stop'].append(alignment[name]['first'])
        else:
            data['Activity'].append(name)
            data['Start'].append(alignment[name]['first'])
            data['Stop'].append(alignment[name]['last']+1)
    df = pd.DataFrame(data)
    #print(df.head())
    #
    # Gannt chart for scheduled tasks
    #
    fig = px.timeline(df, x_start="Start", x_end="Stop",  y="Activity", color="Start")
    if linear:
        fig.layout.xaxis.type = 'linear'
        df['delta'] = df['Stop']-df['Start']
        fig.data[0].x = df.delta.tolist()
    fig.update_yaxes(autorange="reversed") # otherwise tasks are listed from the bottom up
    if output_fname is None:
        fig.show()
    elif output_fname.endswith(".html"):
        print("Writing {}".format(output_fname))
        fig.write_html(output_fname)
    else:
        print("Writing {}".format(output_fname))
        fig.write_image(output_fname)

