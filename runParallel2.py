#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import datetime

import config

r_w = 3
bin_t_w = 4
mask_frq = 5
flatten = 6
step = 7


def command(date, new_args):
    """
    new args: [[pos, value]]
    """
    default = [2022, 1, 1,  # date
               30,  # r_w
               4,  # bin_t_width
               0,  # mask_frq boolean
               0,  # flatten boolean
               30000000  # step -> name of save file
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
    file = config.path_script + "calcMonth3.py"
    log_path = config.path_results + config.pathDay(date)
    if not os.path.exists(log_path) or not os.path.isdir(log_path):
        os.system(f"mkdir -p {log_path}")
    log = log_path + f"log{new_args[-1][1]}.txt"
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
    day_per_core = int(days / cores) + 1

    for day_s in [date_start + datetime.timedelta(days=i * day_per_core) for i in range(cores)]:
        print(day_s)
        cmd = command(day_s, [[r_w, 20],
                              [mask_frq, 1],
                              [bin_t_w, 8],
                              [step, 2]])
        os.system(cmd)

    """ 
    date_start = datetime.datetime(2022, 1, 1)

    for bin_t_w_ in [2,4,6, 8]:

        for r_w_ in [10, 15, 20, 25, 30,35, 40,45, 50]:
            cmd = command(date_start, [[r_w, r_w_],
                                       [mask_frq, 1],
                                       [bin_t_w, bin_t_w_],
                                       [step, 330000000 + bin_t_w_ * 1000 + r_w_]])

            os.system(cmd)
    # now missing mask frq and flatten - do with best parameters
    """
