import sys
import os
import math
import yaml
from pypm.util import load_process


def update(p, k, K=None, workhours=None):
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

    if p.get("delay_after_timesteps",None) is not None:
        delay = p["delay_after_timesteps"]
        tmp = delay / k
        p["delay_after_timesteps"] = tmp

    return int(k)


def chunk_process(filename, output, step):
    assert os.path.exists(filename), "Cannot find YAML process file: {}".format(
        filename
    )

    process = load_process(filename=filename)
    for name in process:
        p = process[name]

        if step == "2h":
            process.hours_per_timestep = update(p, 2)
            process.timesteps_per_day = 12

        elif step == "2h_workday(7-17)":
            process.hours_per_timestep = update(p, 2, workhours=[7, 17])
            process.timesteps_per_day = 5

        elif step == "4h":
            process.hours_per_timestep = update(p, 4)
            process.timesteps_per_day = 6

        elif step == "8h":
            process.hours_per_timestep = update(p, 8)
            process.timesteps_per_day = 6

        elif step == "3:55554h":
            process.hours_per_timestep = update(p, 5, 24 / 5)
            process.timesteps_per_day = 5

        elif step == "5h_workday(7-17)":
            process.hours_per_timestep = update(p, 5, workhours=[7, 17])
            process.timesteps_per_day = 2

        elif step == "10h_workday(7-17)":
            process.hours_per_timestep = update(p, 10, workhours=[7, 17])
            process.timesteps_per_day = 1

        elif step == "1h":
            process.hours_per_timestep = 1
            process.timesteps_per_day = 24

        else:
            print("ERROR: Unexpected chunk step {}".format(step))
            sys.exit(1)

    print("Writing file: {}".format(output))
    with open(output, "w") as OUTPUT:
        yaml.dump(process.data(), OUTPUT, default_flow_style=False)
