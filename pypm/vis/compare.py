import sys
import yaml
import math
import plotly.express as px
import pandas

def compare_results(process_file, results_baseline, results_new, text=True, csvfile=None, output_fname=None, vis=True):
    with open(process_file, 'r') as INPUT:
        p = yaml.safe_load(INPUT)

    activities = [activity['name']   for activity in p['activities']]

    f1 = results_baseline+"_results.yaml"
    f2 = results_new+"_results.yaml"

    print("Comparing {} against {}".format(f2, f1))

    with open(f1, 'r') as INPUT:
        d1 = yaml.safe_load(INPUT)
        g1 = d1['results'][0]['goals']

    with open(f2, 'r') as INPUT:
        d2 = yaml.safe_load(INPUT)
        g2 = d2['results'][0]['goals']

    same = 0
    diff = {}
    for a in activities:
        diff_match = g2['match'].get(a,0) - g1['match'].get(a,0)
        diff_sep   = g2['separation'][a] - g1['separation'][a]
        if math.fabs(diff_match) < 1e-7 and math.fabs(diff_sep) < 1e-7:
            same += 1
        else:    
            diff[a] = (diff_match, diff_sep)

    print("Total Match:       {}".format(g2['total_match'] - g1['total_match']))
    print("Total Separation:  {}".format(g2['total_separation'] - g1['total_separation']))
    print("# Activities Same: {}".format(same))
    print("# Activities Diff: {}".format(len(diff)))

    if text:
        print("Activity,Match Score Difference,Separation Score Difference")
        for a in activities:
            if a in diff:
                v = diff[a]
                print("{},{},{}".format(a,v[0],v[1]))
            else:
                print("{},0,0".format(a))

    if vis:
        data = {"Activity":[], "Match Score":[], "Separation Score":[]}
        for a in activities:
            data["Activity"].append(a)
            if a in diff:
                v = diff[a]
                data["Match Score"].append(v[0])
                data["Separation Score"].append(v[1])
            else:
                data["Match Score"].append(0)
                data["Separation Score"].append(0)
        df = pandas.DataFrame.from_dict(data)
    
        fig = px.bar(df, x="Activity", y="Match Score", title="Difference in activity match scores: {} - {}".format(results_new,results_baseline))
        if output_fname is None:
            fig.show()
        elif output_fname.endswith(".html"):
            print("Writing {}".format(output_fname))
            fig.write_html(output_fname)
        else:
            print("Writing {}".format(output_fname))
            fig.write_image(output_fname)

