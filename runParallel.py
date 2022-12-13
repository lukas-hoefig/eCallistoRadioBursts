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

    program = "python3"
    file = config.path_script + "calcMonth.py"
    log_path = config.path_results + config.pathDay(date)
    if not os.path.exists(log_path) or not os.path.isdir(log_path):
        os.system(f"mkdir -p {log_path}")
    log = log_path + "log.txt"  # TODO see if this creates the file / folder / tree
    args = [str(i) for i in default]
    arg_str = " ".join(args)
    log_command = f"> {log} 2>&1"
    ending = "&"
    return " ".join([program, file, arg_str, log_command, ending])


if __name__ == "__main__":
    date_start = datetime.datetime(2022, 1, 1)

    for rw in [100, 130, 180, 220, 400]:
        cmd = command(date_start, [[r_w, rw], [step, 100000 + rw]])
        os.system(cmd)

    for rw in [100, 130, 180, 220, 400]:
        cmd = command(date_start, [[r_w, rw], [sub_bg, 0], [step, 200000 + rw]])
        os.system(cmd)

    for flat_w in [10, 50, 200, 400, 1000, 3000]:
        cmd = command(date_start, [[flatten_w, flat_w], [step, 300000 + flat_w]])
        os.system(cmd)

    for flat_w in [10, 50, 200, 400, 1000, 3000]:
        cmd = command(date_start, [[flatten_w, flat_w], [sub_bg, 0], [step, 400000 + flat_w]])
        os.system(cmd)
