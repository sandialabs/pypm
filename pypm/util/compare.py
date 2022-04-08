import sys
import yaml
import math

def compare_results(process_file, results_baseline, results_new):
    with open(process_file, 'r') as INPUT:
        p = yaml.safe_load(INPUT)

    activities = [activity['name']   for activity in p['activities']]

    f1 = results_baseline
    f2 = results_new

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

    print("Activity,Match Score Difference,Separation Score Difference")
    for a in activities:
        if a in diff:
            v = diff[a]
            print("{},{},{}".format(a,v[0],v[1]))
        else:
            print("{},0,0".format(a))

