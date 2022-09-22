#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import copy
import pickle

import download
import stations
import analysis
import events
import data
import correlation
import reference
import const

_year = 2022
_month = 1
_day = 3
_days = 3

nobg = True
bin_f = False
bin_t = False
flatten = True
bin_t_w = 4
flatten_w = 400
r_w = 180

limit = 0.6

date_start = datetime(year=_year, month=_month, day=_day)
time_step = timedelta(days=1)
number_days = _days

observatory = stations.getStations(date_start)

events_day = []
for i in range(number_days):
    date = date_start + time_step * i
    year = date.year
    month = date.month
    day = date.day
    download.downloadFullDay(date_start, station=observatory)
    sets = []
    for j in observatory:
        sets.extend(data.listDataPointDay(date_start, station=j))
    e_list = events.EventList([])
    for set1 in range(len(sets)):
        for set2 in range(set1 + 1, len(sets)):
            data1_raw = copy.deepcopy(sets[set1])
            data2_raw = copy.deepcopy(sets[set2])
            data1, data2 = data.fitTimeFrameDataSample(data1_raw, data2_raw)
            if data1 and data2:
                corr = correlation.Correlation(data1, data2, day, _no_background=nobg, _bin_freq=bin_f,
                                               _bin_time=bin_t, _flatten=flatten, _bin_time_width=bin_t_w,
                                               _flatten_window=flatten_w, _r_window=r_w)
                corr.calculatePeaks(_limit=limit)
                e_list += corr.peaks
            else:
                pass
    e_list.sort()
    events_day.append(e_list)
    #print(f"\n {date.year} {date.month} {date.day}")
    #print("mine")
    #print(e_list)
    #print("reference SWPC")
    #print(reference.referenceSWPC(year, month, day))
    #print("reference Monstein")
    #print(reference.referenceMonstein(year, month, day))
    #print("reference Monstein with 2 or more stations")
    #print(reference.referenceMonstein2orMore(year, month, day))
    print(events_day)
# return events_day

if __name__ == '__main__':
    pass


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
