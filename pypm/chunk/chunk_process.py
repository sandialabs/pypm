import sys
import os
import math
import yaml
from pypm.util import load_process


def update(p, k, K=None, workhours=None):
    #
    # NOTE:  This code does not change the delay_after_hours value, which is not chunked.
    #
    if K is None:
        K = k
    if workhours is None:
        workhours = [0, 24]

    min_hours = p["duration"]["min_timesteps"]
    tmp = min_hours / k
    if tmp - int(tmp) > 1e-7:
        p["duration"]["min_timesteps"] = int(math.ceil(tmp))
        print(
            "WARNING: min_hours {} is not evenly divisible by {}.  Rounding up chunked min_hours: {}".format(
                min_hours, k, p["duration"]["min_timesteps"]
            )
        )
    else:
        p["duration"]["min_timesteps"] = int(tmp)

    max_hours = p["duration"]["max_timesteps"]
    tmp = max_hours / k
    if tmp - int(tmp) > 1e-7:
        p["duration"]["max_timesteps"] = int(math.ceil(tmp))
        print(
            "WARNING: max_hours {} is not evenly divisible by {}.  Rounding up chunked max_hours: {}".format(
                max_hours, k, p["duration"]["max_timesteps"]
            )
        )
    else:
        p["duration"]["max_timesteps"] = int(tmp)

    p["hours_per_timestep"] = int(k)


def chunk_process(filename, output, step):
    assert os.path.exists(filename), "Cannot find YAML process file: {}".format(
        filename
    )

    process = load_process(filename=filename)
    for name in process:
        p = process[name]

        if step == "2h":
            update(p, 2)
        elif step == "2h_workday(7-17)":
            update(p, 2, workhours=[7, 17])
        elif step == "4h":
            update(p, 4)
        elif step == "8h":
            update(p, 8)
        elif step == "3:55554h":
            update(p, 5, 24 / 5)
        elif step == "5h_workday(7-17)":
            update(p, 5, workhours=[7, 17])
        elif step == "10h_workday(7-17)":
            update(p, 10, workhours=[7, 17])
        elif step == "1h":
            pass
        else:
            print("ERROR: Unexpected chunk step {}".format(step))
            sys.exit(1)

    print("Writing file: {}".format(output))
    with open(output, "w") as OUTPUT:
        yaml.dump(process.data(), OUTPUT, default_flow_style=False)
