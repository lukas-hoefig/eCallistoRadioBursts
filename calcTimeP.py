#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import sys
import os 
import subprocess

sys.path.append(os.path.join(os.path.dirname("."), "core"))

import config 


#date_start = datetime.datetime(2017, 5, 1)
date_start = datetime.datetime(2022, 3, 19)
date_end = datetime.datetime(2022,3,21)
days = (date_end - date_start).days
cores = 3
day_per_core = int(days/cores) + 1


def command(date):
    program = "python"
    file = os.path.join(config.path_script, "calcTime.py")
    log_path = os.path.join(config.path_results, config.pathDay(date))
    if not os.path.exists(log_path) or not os.path.isdir(log_path):
        os.system(f"mkdir -p {log_path}")
    log = os.path.join(log_path, "log.txt")
    args = [str(date.year), str(date.month), str(date.day)]
    arg_str = " ".join(args)
    log_command = f"> {log} 2>&1"
    ending = "&"
    return " ".join([program, file, arg_str, log_command, ending])


if __name__ == '__main__':
    #for day_s in [date_start + datetime.timedelta(days=i) for i in [0,1,2,3,6,7,9,10]]:
    for day_s in [date_start + datetime.timedelta(days=i) for i in range(cores)]:
        cmd = command(day_s)
        print(cmd)
        #os.system(cmd)
        subprocess.Popen(cmd, shell=True)
