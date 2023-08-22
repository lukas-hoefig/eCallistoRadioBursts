#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import datetime
import reference
import analysis
import events
import config

step = 3


def getReference(*date, europeUT=True):
    date_ = config.getDateFromArgs(*date)
    ref_load = reference.listSWPC(date_)
    # ref_strong = [i for i in ref_load if i.burst_type.endswith("II/2") or i.burst_type.endswith("II/3")]
    if europeUT:
        ref = events.EventList([i for i in ref_load if config.EU_time_lower <=
                               i.time_start.hour < config.EU_time_upper], date_)
    else:
        ref = ref_load
    return ref


def compareToRef(data: events.EventList, ref: events.EventList, *date):
    """
    returns list of events: TP, TN, FP
    """
    ref_strong = events.EventList([i for i in ref if i.burst_type.endswith(
        "II/2") or i.burst_type.endswith("II/3")], *date)
    event_match_all = events.EventList([], *date)
    false_positives = events.EventList([], *date)
    missed_swpc = ref_strong
    for i in data:
        missed_swpc = missed_swpc - i

    for i in data:
        if i.inList(ref):
            event_match_all += i
        else:
            false_positives += i
    return len(missed_swpc), len(event_match_all), len(false_positives), len(data)


if __name__ == '__main__':
    """
    ARGS:
    year month day limit  r_w  subtr_bg  mask_frq  flat  flat_w  bin_t  bin_t_w  NAME

    step            step size
    """
    input_arg = sys.argv
    args = [2022, 1, 1,         # date
            0                   # step
            ]
    if input_arg and len(input_arg) > 2:
        for i, j in enumerate(input_arg[1:]):
            args[i] = type(args[i])(j)

    file = config.path_script + f"/results/all_summed_results2_{args[step]}.txt"
    date_start = datetime.datetime(args[0], args[1], args[2])
    # date_end = datetime.datetime(args[0], args[1], 1) + 6 * datetime.timedelta(days=31)
    # date_end = datetime.datetime(date_end.year, date_end.month, 1)
    date_end = datetime.datetime(2023, 4, 1)
    date = date_start
    while date < date_end:
        data = analysis.loadData(date, step=args[step])
        try:
            ref = getReference(date)
        except FileNotFoundError:
            date = date + datetime.timedelta(days=1)
            continue
        result = compareToRef(data, ref, date)
        with open(file, "a+") as f:
            f.write(f"{date}\t")
            for i in result:
                f.write(str(i) + "\t")
            f.write("\n")
        date = date + datetime.timedelta(days=1)
