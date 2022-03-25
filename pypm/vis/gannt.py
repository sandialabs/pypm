# pypm.vis.gannt

import os.path
import yaml


def create_gannt_chart(process_fname, results_fname, output_fname=None, index=0, rescale=False, cmax=None, cmin=None):
    assert os.path.exists(process_fname), "Unknown file {}".format(process_fname)
    assert os.path.exists(results_fname), "Unknown file {}".format(results_fname)
    import pandas as pd
    import plotly.express as px

    print("Reading {}".format(process_fname))
    with open(process_fname, 'r') as INPUT:
        process = yaml.safe_load(INPUT)
    print("Reading {}".format(results_fname))
    with open(results_fname, 'r') as INPUT:
        results = yaml.load(INPUT, Loader=yaml.Loader)

    assert results['solver']['model']['name'] in ['model3', 'model4', 'model5', 'model6', 'model7', 'model8','model10', 'model11', 'model12', 'model13', 'model14'], "Cannot visualize results in {}.  Expects results generated for model3-model8,model10-model14.".format(results_fname)
    assert len(results['results']) > index, "Cannot visualize the {}-th process match in {}.  This file only has {} matches.".format(index, results_fname, len(results['results']))

    print("Processing results")
    if 'datetime_schedule' in results['results'][index]:
        linear = False
        alignment = results['results'][index]['datetime_schedule']
        data = {'Activity':[], 'Start':[], 'Stop':[], 'Match Score':[]}
        for activity in process['activities']:
            name = activity['name']
            if name not in alignment:
                print("Warning: Activity \"{}\" was not included in the process match".format(name))
                #data['Activity'].append(name)
                #data['Start'].append(0)
                #data['Stop'].append(0)
                #data['Match Score'].append(0)
            elif 'pre' in alignment[name] or 'post' in alignment[name]:
                if 'pre' in alignment[name]:
                    print("Warning: Activity \"{}\" omitted because it starts before the data time window.".format(name))
                if 'post' in alignment[name]:
                    print("Warning: Activity \"{}\" omitted because it ends after the data time window.".format(name))
            else:
                data['Activity'].append(name)
                data['Start'].append(alignment[name]['first'])
                data['Match Score'].append(results['results'][index]['goals']['match'].get(name,0))
                if 'stop' in alignment[name]:
                    data['Stop'].append(alignment[name]['stop'])
                elif 'last' in alignment[name]:
                    print("Warning: Using 'last' for activity {} because 'stop' is missing.".format(name))
                    data['Stop'].append(alignment[name]['last'])
                else:
                    print("Warning: Activity \"{}\" does not appear to end".format(name))
                    data['Stop'].append(alignment[name]['first'])

        if rescale:
            data['Match Score'] = [v+10 if v>0 else 0 for v in data['Match Score']]
    else:
        linear = True
        alignment = results['results'][index]['schedule']
        data = {'Activity':[], 'Start':[], 'Stop':[]}
        for activity in process['activities']:
            name = activity['name']
            if name not in alignment:
                print("Warning: Activity \"{}\" was not included in the process match".format(name))
                data['Activity'].append(name)
                data['Start'].append(0)
                data['Stop'].append(0)
            if 'last' not in alignment[name]:
                print("Warning: Activity \"{}\" does not appear to end".format(name))
                data['Activity'].append(name)
                data['Start'].append(alignment[name]['first'])
                data['Stop'].append(alignment[name]['first'])
            else:
                data['Activity'].append(name)
                data['Start'].append(alignment[name]['first'])
                data['Stop'].append(alignment[name]['last']+1)
    df = pd.DataFrame(data)
    print(df)
    #print(df.head())
    #
    # Gannt chart for scheduled tasks
    #
    print("Generating Figure")
    if linear:
        fig = px.timeline(df, x_start="Start", x_end="Stop",  y="Activity", color="Match Score")
        fig.layout.xaxis.type = 'linear'
        df['delta'] = df['Stop']-df['Start']
        fig.data[0].x = df.delta.tolist()
    else:
        if cmax:
            if cmin is None:
                cmin = 0
            cmax = float(cmax)
        else:
            cmin = 0
            cmax = max(data['Match Score'])
        fig = px.timeline(df, x_start="Start", x_end="Stop",  y="Activity", color="Match Score", range_color=(cmin,cmax))
    fig.update_yaxes(autorange="reversed") # otherwise tasks are listed from the bottom up
    if output_fname is None:
        fig.show()
    elif output_fname.endswith(".html"):
        print("Writing {}".format(output_fname))
        fig.write_html(output_fname)
    else:
        print("Writing {}".format(output_fname))
        fig.write_image(output_fname)



def create_gannt_chart_with_separation_metric(process_fname, results_fname, output_fname=None, index=0, cmax=None, cmin=None):
    assert os.path.exists(process_fname), "Unknown file {}".format(process_fname)
    assert os.path.exists(results_fname), "Unknown file {}".format(results_fname)
    import pandas as pd
    import plotly.express as px

    print("Reading {}".format(process_fname))
    with open(process_fname, 'r') as INPUT:
        process = yaml.safe_load(INPUT)
    print("Reading {}".format(results_fname))
    with open(results_fname, 'r') as INPUT:
        results = yaml.load(INPUT, Loader=yaml.Loader)

    assert results['solver']['model']['name'] in ['model3', 'model4', 'model5', 'model6', 'model7', 'model8','model10', 'model11', 'model12', 'model13', 'model14'], "Cannot visualize results in {}.  Expects results generated for model3-model8,model10-model14.".format(results_fname)
    assert len(results['results']) > index, "Cannot visualize the {}-th process match in {}.  This file only has {} matches.".format(index, results_fname, len(results['results']))

    print("Processing results")
    if 'datetime_schedule' in results['results'][index]:
        linear = False
        alignment = results['results'][index]['datetime_schedule']
        data = {'Activity':[], 'Start':[], 'Stop':[], 'Separation Score':[]}
        for activity in process['activities']:
            name = activity['name']
            if name not in alignment:
                print("Warning: Activity \"{}\" was not included in the process match".format(name))
                #data['Activity'].append(name)
                #data['Start'].append(0)
                #data['Stop'].append(0)
                #data['Separation Score'].append(0)
            elif 'pre' in alignment[name] or 'post' in alignment[name]:
                if 'pre' in alignment[name]:
                    print("Warning: Activity \"{}\" omitted because it starts before the data time window.".format(name))
                if 'post' in alignment[name]:
                    print("Warning: Activity \"{}\" omitted because it ends after the data time window.".format(name))
            else:
                data['Activity'].append(name)
                data['Start'].append(alignment[name]['first'])
                data['Separation Score'].append(results['results'][index]['goals']['separation'].get(name,0))
                if 'stop' in alignment[name]:
                    data['Stop'].append(alignment[name]['stop'])
                elif 'last' in alignment[name]:
                    print("Warning: Using 'last' for activity {} because 'stop' is missing.".format(name))
                    data['Stop'].append(alignment[name]['last'])
                else:
                    print("Warning: Activity \"{}\" does not appear to end".format(name))
                    data['Stop'].append(alignment[name]['first'])
    else:
        linear = True
        alignment = results['results'][index]['alignment']
        data = {'Activity':[], 'Start':[], 'Stop':[]}
        for activity in process['activities']:
            name = activity['name']
            if name not in alignment:
                print("Warning: Activity \"{}\" was not included in the process match".format(name))
                data['Activity'].append(name)
                data['Start'].append(0)
                data['Stop'].append(0)
            if 'last' not in alignment[name]:
                print("Warning: Activity \"{}\" does not appear to end".format(name))
                data['Activity'].append(name)
                data['Start'].append(alignment[name]['first'])
                data['Stop'].append(alignment[name]['first'])
            else:
                data['Activity'].append(name)
                data['Start'].append(alignment[name]['first'])
                data['Stop'].append(alignment[name]['last']+1)
    df = pd.DataFrame(data)
    print(df)
    #print(df.head())
    #
    # Gannt chart for scheduled tasks
    #
    print("Generating Figure")
    if linear:
        fig = px.timeline(df, x_start="Start", x_end="Stop",  y="Activity", color="Separation Score")
        fig.layout.xaxis.type = 'linear'
        df['delta'] = df['Stop']-df['Start']
        fig.data[0].x = df.delta.tolist()
    else:
        if cmax:
            if cmin is None:
                cmin = 0
            cmax = float(cmax)
        else:
            cmin = 0
            cmax = max(data['Separation Score'])
        fig = px.timeline(df, x_start="Start", x_end="Stop",  y="Activity", color="Separation Score", range_color=(cmin,cmax))
    fig.update_yaxes(autorange="reversed") # otherwise tasks are listed from the bottom up
    if output_fname is None:
        fig.show()
    elif output_fname.endswith(".html"):
        print("Writing {}".format(output_fname))
        fig.write_html(output_fname)
    else:
        print("Writing {}".format(output_fname))
        fig.write_image(output_fname)

