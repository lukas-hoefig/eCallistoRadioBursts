#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import timedelta
import copy
import numpy as np

import download
import stations
import analysis
import events
import data
import correlation
import const

# TODO: analysis -> search peaks integrated into calc point


def run1stSearch(*date, days=1, mask_frq=False, nobg=True, bin_f=False, bin_t=False,
                 flatten=True, bin_t_w=4, flatten_w=400, r_w=180):
    date_start = const.getDateFromArgs(*date)
    limit = 0.6
    time_step = timedelta(days=1)

    events_day = []
    for i in range(days):
        date = date_start + time_step * i
        observatories = stations.getStations(date)
        download.downloadFullDay(date, station=observatories)
        sets = []
        for j in observatories:
            sets.extend(data.listDataPointDay(date, station=j))
        e_list = events.EventList([])
        for set1 in range(len(sets)):
            for set2 in range(set1 + 1, len(sets)):
                data1_raw = copy.deepcopy(sets[set1])
                data2_raw = copy.deepcopy(sets[set2])
                data1, data2 = data.fitTimeFrameDataSample(data1_raw, data2_raw)

                if data1 and data2:
                    if mask_frq:
                        mask1 = analysis.maskBadFrequencies(data1)
                        mask2 = analysis.maskBadFrequencies(data2)
                        data1.spectrum_data.data[mask1] = np.nanmean(data1.spectrum_data.data)
                        data2.spectrum_data.data[mask2] = np.nanmean(data2.spectrum_data.data)
                    corr = correlation.Correlation(data1, data2, date.day, no_background=nobg, bin_freq=bin_f,
                                                   bin_time=bin_t, flatten=flatten, bin_time_width=bin_t_w,
                                                   flatten_window=flatten_w, r_window=r_w)
                    corr.calculatePeaks(limit=limit)
                    try:
                        event_peaks = analysis.peaksInData(data1, data2)
                        for peak in corr.peaks:
                            if peak.inList(event_peaks):
                                e_list += peak
                    except AttributeError:
                        pass
                else:
                    pass
        try:
            e_list.sort()
        except AttributeError:
            # empty list
            pass
        events_day.append(e_list)
        analysis.saveData(date, event_list=e_list, step=1)
    return events_day


def run2ndSearch(*date, mask_freq=True, no_bg=True, bin_f=False, bin_t=True, flatten=True, bin_t_w=None, flatten_w=None,
                 r_w=30):
    date = const.getDateFromArgs(*date)
    events_day = analysis.loadData(date, step=1)
    e_list = events.EventList([])
    limit = 0.8

    for event in events_day[:1]:

        obs = stations.StationSet(event.stations)
        set_obs = obs.getSet()
        for i in set_obs:
            dp1, dp2, cor = analysis.calcPoint(date, obs1=i[0], obs2=i[1], mask_frq=mask_freq, r_window=r_w,
                                               flatten=flatten, bin_time=bin_t, bin_freq=bin_f, no_bg=no_bg,
                                               flatten_window=bin_t_w, bin_time_width=flatten_w, limit=limit)

            event_peaks = analysis.peaksInData(dp1, dp2)
            for peak in cor.peaks:
                if peak.inList(event_peaks):
                    e_list += peak

    analysis.saveData(date, event_list=e_list, step=2)
    return e_list


if __name__ == '__main__':
    run1stSearch(2022, 1, 4, days=1, mask_frq=True)
    run2ndSearch(2022, 1, 4)


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
