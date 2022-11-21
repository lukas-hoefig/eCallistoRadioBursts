#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import sys
import os

import steps
import analysis
import config


if __name__ == '__main__':
    """
    args: year month day #days 
    """
    input_arg = sys.argv
    args = [2022, 1, 1, 1]
    if input_arg and len(input_arg) > 2:
        for i, j in enumerate(input_arg[1:]):
            args[i] = int(j)

    date_start = datetime.datetime(args[0], args[1], args[2])
    year = args[0]
    month = args[1]
    day = args[2]

    os.system(f"python {config.path_script}calcDay.py {year} {month:02} {day:02} &")
