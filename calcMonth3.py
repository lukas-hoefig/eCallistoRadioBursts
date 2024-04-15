#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import sys
import os 

sys.path.append(os.path.join(os.path.dirname("."), "core"))

import steps
import analysis

bin_t_w = 3
mask_frq = 4
peak_limit = 5
limit_skip = 6
limit_skip2 = 7
step = 8

if __name__ == '__main__':
    """
    ARGS:
    year month day ~
    
    
    NAME name of save file (int)
    """
    input_arg = sys.argv
    args = [2022, 1, 1,  # date
               12,           # bin_t_width
               True,        # mask_frq
               1.1,         # peak limit for peaksInData function
               0.9,         # events with lower prob are skipped
               1.0,          # limit for peakfinder
               300000000     # step -> name of save file
               ]

    if input_arg and len(input_arg) > 2:
        for i, j in enumerate(input_arg[1:]):
            if isinstance(args[i], bool):
                args[i] = type(args[i])(int(j))    
            else:
                args[i] = type(args[i])(j)

    date_start = datetime.datetime(args[0], args[1], args[2])
    date_end = datetime.datetime(args[0], args[1], 1) + datetime.timedelta(days=6 * 31)
    date_end = datetime.datetime(date_end.year, date_end.month, 1)
    date = date_start
    
    while date <= date_end:
        print(date)
        if os.path.isfile(analysis.filename(date, step=args[step])):
            date = date + datetime.timedelta(days=1)
            print(" skipped ")
            continue
        data_ = analysis.loadData(date, step=200006025)
        data_step_4 = steps.thirdStep(data_, date, peak_limit=args[peak_limit], mask_frq=args[mask_frq], bin_time_w=args[bin_t_w], limit_skip=args[limit_skip], limit_skip2=args[limit_skip2])
        analysis.saveData(date, event_list=data_step_4, step=args[step])
        date = date + datetime.timedelta(days=1)

    # data_step_2 = steps.secondStep(None, date)
    # analysis.saveData(date, event_list=data_step_2, step=2)
    # data_step_3 = steps.thirdStep(None, date)
    # analysis.saveData(date, event_list=data_step_3, step=3)
    # data_step_4 = steps.fourthStep(None, date)
    # analysis.saveData(date, event_list=data_step_4, step=4)
