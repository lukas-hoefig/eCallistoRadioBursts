#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import datetime

import config

limit = 3
r_w = 4
sub_bg = 5
mask_frq = 6
flatten = 7
flatten_w = 8
bin_t = 9
bin_t_w = 10
step = 11


def command(date, new_args):
    """
    new args: [[pos, value]]
    """
    default = [2022, 1, 1,                  # date
               config.correlation_start,    # limit
               config.ROLL_WINDOW,          # rolling window
               True,                        # subtract_bg
               False,                       # mask frq
               True, 500,                   # subtract mean
               False, 4,                    # time binning
               1                            # step -> name of save file
               ]
    for i in new_args:
        default[i[0]] = type(default[i[0]])(i[1])

    for i in enumerate(default):
        if type(i[1]) == bool:
            default[i[0]] = int(i[1])

    default[0] = date.year
    default[1] = date.month
    default[2] = date.day

    program = "python3"
    file = config.path_script + "calcMonth.py"
    log_path = config.path_results + config.pathDay(date)
    if not os.path.exists(log_path) or not os.path.isdir(log_path):
        os.system(f"mkdir -p {log_path}")
    log = log_path + f"log{date.day}.txt"  # TODO see if this creates the file / folder / tree
    args = [str(i) for i in default]
    arg_str = " ".join(args)
    log_command = f"> {log} 2>&1"
    ending = "&"
    return " ".join([program, file, arg_str, log_command, ending])


if __name__ == "__main__":
    date_start = datetime.datetime(2022, 1, 1)

    months = 6
    days = (datetime.datetime(2022, 1 + months, 1) - datetime.datetime(2022, 1, 1)).days
    cores = 37
    day_per_core = int(days/cores) + 1

    #for day_s in [date_start + datetime.timedelta(days=i * day_per_core) for i in range(cores)]:
    #    print(day_s)
    #    cmd = command(day_s, [[r_w, 160], [step, 1], [flatten_w, 300]])
    #    os.system(cmd)

    for rw in [100, 130, 150, 160, 170, 180, 200, 220, 400]:
        cmd = command(date_start, [[r_w, rw], [step, 10200000 + rw]])        # 9100000 + rw
        os.system(cmd)

    for flat_w in [10, 50, 100, 150, 200, 300, 400, 600, 1000, 3000]:
        cmd = command(date_start, [[flatten_w, flat_w], [step, 11200000 + flat_w]])      # 9200000 + rw
        os.system(cmd)

    for rw in [100, 130, 150, 160, 170, 180, 200, 220, 400]:
        cmd = command(date_start, [[r_w, rw], [limit, 0.7],  [step, 12200000 + rw]])        # 9100000 + rw
        os.system(cmd)

    for flat_w in [10, 50, 100, 150, 200, 300, 400, 600, 1000, 3000]:
        cmd = command(date_start, [[flatten_w, flat_w], [limit, 0.7], [step, 13200000 + flat_w]])      # 9200000 + rw
        os.system(cmd)

