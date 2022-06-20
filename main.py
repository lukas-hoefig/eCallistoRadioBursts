#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime

import matplotlib.pyplot as plt
import numpy as np
import copy

import const
import data
import observatories
import download
import events
import correlation
import reference


def missingThings():
    """
    TODO: methods binning as variable

    TODO: everything observatory related with Observatory object

    TODO: unify spectral range declaration of observatories -> search possible

    TODO: import calender -automated run through longer timeframes

    TODO: os module - test linux/windows specifics
    """
    pass



def testBacBursts(nobg, bin_f, bin_t, flatten, bin_t_w, flatten_w, r_w):

    reference = [[2017, 4, 18, correlation.Comparison(["09:36:00", "09:43:42"])],
                 [2017, 6, 1, correlation.Comparison(["11:34:00"])],
                 [2017, 7, 11, correlation.Comparison(["13:20:00"])],
                 [2017, 9, 2, correlation.Comparison(["12:28:00", "12:21:39"])],
                 [2017, 9, 4, correlation.Comparison(["08:33:00"])],
                 [2017, 9, 6, correlation.Comparison(["09:18:00", "15:25:00"])],
                 [2017, 9, 7, correlation.Comparison(["09:53:00", "10:15:00", "12:55:00"])],
                 [2017, 9, 8, correlation.Comparison(["07:06:00", "09:20:00", "10:47:00", "10:54:00",
                                                      "13:22:00", "14:01:00", "15:37:00"])],
                 [2017, 9, 9, correlation.Comparison(["11:17:00", "11:44:00"])],
                 [2017, 9, 27, correlation.Comparison(["12:10:00"])],
                 [2020, 3, 8, correlation.Comparison(["15:33:00", "15:36:00"])],
                 [2020, 10, 27, correlation.Comparison(["08:52:00", "10:58:00", "11:43:00"])],
                 [2020, 11, 20, correlation.Comparison(["13:28:00"])],
                 [2020, 11, 21, correlation.Comparison(["10:46:00", "11:32:00"])],
                 [2020, 11, 22, correlation.Comparison(["11:00:00", "11:08:00", "14:17:00"])],
                 [2020, 12, 27, correlation.Comparison(["11:37:00", "12:35:00"])],
                 [2020, 12, 30, correlation.Comparison(["14:26:00"])],
                 [2021, 4, 24, correlation.Comparison(["10:23:00"])],
                 [2021, 4, 26, correlation.Comparison(["13:56:00"])]]

    observatory = [observatories.uni_graz, observatories.triest, observatories.swiss_landschlacht, observatories.oe3flb,
                   observatories.austria, observatories.bir, observatories.swiss_hb9sct]

    print("------------------------------------------------"
          "\nNew try: {}{}{}{}{}\n------------------------------------------------"
          .format(["", "reduced background, "][nobg],
                  ["", "bin_f, "][bin_f],
                  ["", "bin_t:{}".format(bin_t_w)][bin_t],
                  ["", "flatten:{}".format(flatten_w)][flatten],
                  "r_window:{}".format(r_w)))

    for _test in reference:
        events = events.EventList([])
        year = _test[0]
        month = _test[1]
        day = _test[2]
        print("------------------------\n"
              "New Test: {}.{}.{}\n".format(day, month, year))
        download.downloadFullDay(year, month, day, observatory)
        obs_ = download.observatoriesAvailable(year, month, day)[1]
        stations = observatories.ObservatorySet(obs_[:3])            # function this -> prio list
        for pair in stations.getSet():

            print("Observatories: {} & {}".format(pair[0], pair[1]))
            dp_1 = data.createDay(year, month, day, pair[0], spec_range)
            dp_2 = data.createDay(year, month, day, pair[1], spec_range)
            dp_1_clean, dp_2_clean = data.fitTimeFrameDataSample(dp_1, dp_2)
            corr = correlation.Correlation(dp_1_clean, dp_2_clean, _no_background=nobg, _bin_freq=bin_f,
                                           _bin_time=bin_t, _flatten=flatten, _bin_time_width=bin_t_w,
                                           _flatten_window=flatten_w, _r_window=r_w)
            corr.calculatePeaks()
            events += corr.peaks

        total = len(events)
        failed_events = copy.copy(_test[3]) - copy.copy(events)
        false_positives = copy.copy(events) - copy.copy(_test[3])
        print("Total Peaks found: {}\nNot Found\n {}: {}\nFalse peaks\n {} : {}".format(total,
                                                                                        len(failed_events), failed_events,
                                                                                        len(false_positives), false_positives))


def testRun(_year, _month, _day, _days, spec_range=None,
            nobg=False, bin_f=False, bin_t=False, flatten=False, bin_t_w=4, flatten_w=400, r_w=180):

    if spec_range is None:
        spec_range = [45, 81]
    date_start = datetime.datetime(year=_year, month=_month, day=_day)
    time_step = datetime.timedelta(days=1)
    number_days = _days

    observatory = [observatories.uni_graz, observatories.triest, observatories.swiss_landschlacht, observatories.oe3flb,
                   observatories.alaska_haarp, observatories.alaska_cohoe, observatories.roswell, observatories.bir,
                   observatories.indonesia, observatories.assa, observatories.swiss_muhen, observatories.swiss_hb9sct,
                   observatories.egypt_alexandria, observatories.arecibo, observatories.glasgow, observatories.humain]

    for i in range(number_days):
        date = date_start + time_step * i
        year = date.year
        month = date.month
        day = date.day
        download.downloadFullDay(year, month, day, observatory)
        stations = download.observatoriesAvailable(year, month, day)[1]
        sets = []
        for j in stations:
            sets.extend(data.listDataPointDay(year, month, day, j, spec_range))
        events = events.EventList([])
        for set1 in range(len(sets) - 1):
            for set2 in range(set1 + 1, len(sets)):
                data1_raw = copy.deepcopy(sets[set1])
                data2_raw = copy.deepcopy(sets[set2])
                data1, data2 = data.fitTimeFrameDataSample(data1_raw, data2_raw)
                if data1 and data2:
                    corr = correlation.Correlation(data1, data2, day, _no_background=nobg, _bin_freq=bin_f,
                                                   _bin_time=bin_t, _flatten=flatten, _bin_time_width=bin_t_w,
                                                   _flatten_window=flatten_w, _r_window=r_w)
                    corr.calculatePeaks()
                    events += corr.peaks
                else:
                    pass
        events.sort()

        print(f"\n {date.year} {date.month} {date.day}")
        print("mine")
        print(events)
        print("reference SWPC")
        print(reference.listSWPC(year, month, day))
        print("reference Monstein")
        print(reference.listMonstein(year, month, day))
        print("reference Monstein with 2 or more stations")
        print(reference.listMonstein2orMore(year, month, day))


if __name__ == '__main__':
    testRun(2022, 1, 1, 1, nobg=False, bin_f=False, bin_t=False, flatten=False, bin_t_w=4, flatten_w=400, r_w=180)
    # flatten = True
    # flatten_w = 220
    # bin_f = False
    # nobg = True
    # bin_t = False
    # bin_t_w = 4
    # for r_w in range(180, 260, 10):
    #     testBacBursts(nobg, bin_f, bin_t, flatten, bin_t_w, flatten_w, r_w)


# TODO 20.01. bug 9:18
# 16.01. 9:09 bug (flatten)  - 20.01. 9:01
# TODO CTM's -> destroy everything

# 31.01 18:11 why?
"""
if __name__ == '__main__':
    # bacBurstFailed()

    #nobg = False
    #bin_f = False
    #bin_t = False
    #flatten = False
    #bin_t_w = 1
    #flatten_w = 1
    ## nobg = True
    #for r_w in range(20, 260, 20):
    #    testBacBursts(nobg, bin_f, bin_t, flatten, bin_t_w, flatten_w, r_w)
    #
    #r_w = 160
    #flatten = True
    #for flatten_w in range(40, 400, 60):
    #    testBacBursts(nobg, bin_f, bin_t, flatten, bin_t_w, flatten_w, r_w)
    #
    #r_w = 160
    #flatten = False
    #bin_t = True
    #for bin_t_w in range(2, 16, 2):
    #    testBacBursts(nobg, bin_f, bin_t, flatten, bin_t_w, flatten_w, r_w)
    #
    #r_w = 180
    #flatten = True
    #flatten_w = 220
    #bin_f = True
    #for nobg in range(2):
    #    testBacBursts(nobg, bin_f, bin_t, flatten, bin_t_w, flatten_w, r_w)

    flatten = True
    flatten_w = 220
    bin_f = False
    nobg = True
    bin_t = False
    bin_t_w = 4
    for r_w in range(180, 260, 10):
        testBacBursts(nobg, bin_f, bin_t, flatten, bin_t_w, flatten_w, r_w)




   andere ecallisto auswertungen -> type 3
   warum/wie/welche werte setzen -> i.e. binsize -> ___statistics___ 
   
   ordner -> test files -> known bursts, empties, type 2/3 overlay (anfang november 21), gewitter
   background remove -> yes/no, why - does it get better? 
   
   1/11 10:52-10:52  11:06-11:07
   2/11 10:14-10:15                         | gewitter
   3/11 09:31-09:32  14:06-14:08	        | gewitter
   
   
"""


# TODO:
"""

comparison -> [ liste["Events-verpasst"], liste["Events-falsch"]]

datapoint (obs1) 
datapoint (obs2)
datapoint (....)

for each test:
    for each setOfObservatoryCombination
        comparisons (obs1-obs2)
        ... 
        -> merge result listen  # TODO
    print test results 

"""

# TODO:
"""
day, obs1 obs2 -> EventList
day, obs1 obs3 -> EventList
day, obs2 obs3 -> EventList
                      |
                    merge
                  compare to reference 
"""

"""
type ii list 
20200529	07:23
20201016	12:59 (greenland + SWISS-Landschlacht ) 
20201020	13:31 (greenland)

"""
"""
type iv
20110924 12:00 - 14:00
20201121	11:30-    multiple type III 
20201125	23:26     australia-assa
20201129	12:56     unigraz - looks like type 2
20201130	10:56-10:58	VI	BIR, SWISS-Landschlacht    weak, multiple type iii ?
20201229	20:57      roswell - mexart
20201230	02:35      australia india uidaipur, indonesia
20201230	09:12      austria unigraz 
"""
"""
type V < 45 MHz -> not usually measurable with chosen observatories - rare


"""
"""
type i
20201201	04:53-05:53	I	Australia-ASSA   nope


"""
