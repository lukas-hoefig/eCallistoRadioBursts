#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import sys
import os 

sys.path.append(os.path.join(os.path.dirname("."), "core"))

import steps
import analysis

limit = 3
r_w = 4
sub_bg = 5
mask_frq = 6
flatten = 7
flatten_w = 8
bin_t = 9
bin_t_w = 10
step = 11

if __name__ == '__main__':
    """
    ARGS:
    year month day limit  r_w  subtr_bg  mask_frq  flat  flat_w  bin_t  bin_t_w  NAME
    
    limit           limit correlation detection
    rw_             rolling window
    subtr_bg        subtract background
    mask_frq        mask frequency
    flat            subtract mean
    flat_w          flatten rolling window
    bin_t           I/O bin time axis
    bin_t_w         bin time width 
    NAME name of save file (int)
    """
    input_arg = sys.argv
    args = [2022, 1, 1,         # date
            0.6,                # limit
            180,                # rolling window
            True,               # subtract_bg
            0,                  # mask frq
            True, 500,          # subtract mean
            False, 4,           # time binning
            1                   # step -> name of save file
            ]
    if input_arg and len(input_arg) > 2:
        for i, j in enumerate(input_arg[1:]):
            args[i] = type(args[i])(j)

    date_start = datetime.datetime(args[0], args[1], args[2])
    date_end = datetime.datetime(args[0], args[1], 1) + datetime.timedelta(days=31)
    date_end = datetime.datetime(date_end.year, date_end.month, 1)

    # months = 6
    # days = (datetime.datetime(2022, 1 + months, 1) - datetime.datetime(2022, 1, 1)).days
    # cores = 37
    # day_per_core = int(days/cores)
    # date_end = date_start + datetime.timedelta(days=day_per_core)
    date = date_start
    while date <= date_end:
        print(date)
        if os.path.isfile(analysis.filename(date, step=args[step])):
            date = date + datetime.timedelta(days=1)
            print(" skipped ")
            continue
        data_raw = steps.dataSetDay(date, run=True, eu_ut=True)
        data_step_1 = steps.firstStep(date, data_sets=data_raw,
                                      limit=args[limit], r_w=args[r_w], nobg=args[sub_bg], mask_frq=args[mask_frq],
                                      flatten=args[flatten], flatten_w=args[flatten_w],
                                      bin_t=args[bin_t], bin_t_w=args[bin_t_w])
        analysis.saveData(date, event_list=data_step_1, step=args[step])
        date = date + datetime.timedelta(days=1)

    # data_step_2 = steps.secondStep(None, date)
    # analysis.saveData(date, event_list=data_step_2, step=2)
    # data_step_3 = steps.thirdStep(None, date)
    # analysis.saveData(date, event_list=data_step_3, step=3)
    # data_step_4 = steps.fourthStep(None, date)
    # analysis.saveData(date, event_list=data_step_4, step=4)
