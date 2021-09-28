import sys
import os
import math
import yaml
from pypm.util import load_process


def update(p, k, K=None):
    if K is None:
        K=k

    max_delay = p['max_delay']
    if max_delay is not None:
        tmp = max_delay / K
        if tmp - int(tmp) > 1e-7:
            print("WARNING: max_delay is not evenly divisible by {}.  Rounding up chunked max_delay.")
            p['max_delay'] = int(math.ceil(tmp))
        else:
            p['max_delay'] = int(tmp)

    min_hours = p['duration']['min_hours']
    tmp = min_hours / k
    if tmp - int(tmp) > 1e-7:
        print("WARNING: min_hours is not evenly divisible by {}.  Rounding up chunked min_hours.")
        p['duration']['min_hours'] = int(math.ceil(tmp))
    else:
        p['duration']['min_hours'] = int(tmp)

    max_hours = p['duration']['max_hours']
    tmp = max_hours / k
    if tmp - int(tmp) > 1e-7:
        print("WARNING: max_hours is not evenly divisible by {}.  Rounding up chunked max_hours.")
        p['duration']['max_hours'] = int(math.ceil(tmp))
    else:
        p['duration']['max_hours'] = int(tmp)


def chunk_process(filename, output, step):
    assert os.path.exists(filename), "Cannot find YAML process file: {}".format(filename)

    process = load_process(filename=filename)
    for name in process:
        p = process[name]

        if step == '2h':
            update(p, 2)
        elif step == '4h':
            update(p, 4)
        elif step == '8h':
            update(p, 8)
        elif step == '3:55554h':
            update(p, 5, 24/5)
        elif step == '1h':
            pass
        else:
            print("ERROR: Unexpected chunk step {}".format(step))
            sys.exit(1)

    print("Writing file: {}".format(output))
    with open(output, 'w') as OUTPUT:
        yaml.dump(process.data(), OUTPUT, default_flow_style=False)
