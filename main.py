#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt
import numpy as np

import const
import data
import observatories
import download
import analysis
import correlation


def missingThings():
    """
    TODO: everything observatory related with Observatory object

    TODO include GLASGOW + BIR , 3 indias,

    TODO: unify spectral range declaration of observatories -> search possible

    TODO: import calender -automated run through longer timeframes

    TODO: os module - test linux/windows specifics
    """
    pass


spec_range = [45, 81]


def testBacBursts(nobg, bin_f, bin_t, flatten, bin_t_w, flatten_w, r_w):
    reference = [[2017, 4, 18, correlation.Comparison(["09:36:00"])],
                 [2017, 6, 1, correlation.Comparison(["11:34:00"])],
                 [2017, 7, 11, correlation.Comparison(["13:20:00"])],
                 [2017, 9, 2, correlation.Comparison(["12:28:00"])],
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
    obs = [observatories.uni_graz, observatories.oe3flb, observatories.swiss_landschlacht, observatories.austria]
    obs_dl = [i.name for i in obs]

    print("------------------------------------------------"
          "\nNew try: {}{}{}{}{}\n------------------------------------------------"
          .format(["", "reduced background, "][nobg],
                  ["", "bin_f, "][bin_f],
                  ["", "bin_t:{}".format(bin_t_w)][bin_t],
                  ["", "flatten:{}".format(flatten_w)][flatten],
                  "r_window:{}".format(r_w)))

    events = np.array([0, 0])
    for i in reference:
        year = i[0]
        month = i[1]
        day = i[2]
        print("------------------------\n"
              "New Test: {}.{}.{}\n".format(day, month, year))
        download.downloadFullDay(i[0], i[1], i[2], obs_dl)
        obs_ = download.observatoriesAvailable(year, month, day)[1]
        print("Observatories: {} & {}".format(obs_[0], obs_[1]))
        dp_1 = data.createDay(year, month, day, obs_[0], spec_range)
        dp_2 = data.createDay(year, month, day, obs_[1], spec_range)
        dp_1_clean, dp_2_clean = data.fitTimeFrameDataSample(dp_1, dp_2)
        corr = correlation.Correlation(dp_1_clean, dp_2_clean, nobg, bin_f, bin_t, flatten, bin_t_w, flatten_w, r_w)
        corr.getPeaks()
        result = corr.compareToTest(i[3])
        correlation.addEventsToList(result[0], events[0])
        correlation.addEventsToList(result[1], events[1])
    print("Not Found\n {}\nFalse peaks\n {}".format(len(events[0]), len(events[1])))


def bacBurstFailed():
    failed = [[2017, 6, 1, correlation.Comparison(["11:34:00"])],
              [2017, 7, 11, correlation.Comparison(["13:20:00"])],
              [2017, 9, 7, correlation.Comparison(["09:53:00"])],
              [2017, 9, 7, correlation.Comparison(["10:15:00"])],
              [2017, 9, 7, correlation.Comparison(["12:55:00"])],
              [2017, 9, 8, correlation.Comparison(["15:37:00"])],
              [2017, 9, 9, correlation.Comparison(["11:17:00"])],
              [2017, 9, 9, correlation.Comparison(["11:44:00"])],
              [2017, 9, 27, correlation.Comparison(["12:10:00"])],
              [2020, 3, 8, correlation.Comparison(["15:33:00"])],
              [2020, 3, 8, correlation.Comparison(["15:36:00"])],
              [2020, 11, 20, correlation.Comparison(["13:28:00"])],
              [2020, 11, 22, correlation.Comparison(["14:17:00"])],
              [2020, 12, 27, correlation.Comparison(["11:37:00"])],
              [2020, 12, 27, correlation.Comparison(["12:35:00"])],
              [2020, 12, 30, correlation.Comparison(["14:26:00"])],
              [2021, 4, 26, correlation.Comparison(["13:56:00"])]]
    obs = [observatories.uni_graz, observatories.austria, observatories.triest]

    fig, ax = plt.subplots(figsize=(16, 9))

    for o in obs:
        for i in failed:
            download.downloadFullDay(i[0], i[1], i[2], o.name)
            dp = data.createFromTime(i[0], i[1], i[2], i[3], o, spec_range)
            dp.createSummedCurve(spec_range)
            dp.flattenSummedCurve(const.ROLL_WINDOW)
            dp.plotSummedCurve(ax, peaks=i[3])

    plt.tight_layout()
    plt.show()

    fig, ax = plt.subplots(figsize=(16, 9))

    for i in failed:
        download.downloadFullDay(i[0], i[1], i[2], obs[0].name)
        download.downloadFullDay(i[0], i[1], i[2], obs[1].name)
        dp1 = data.createFromTime(i[0], i[1], i[2], i[3], obs[0], spec_range)
        dp2 = data.createFromTime(i[0], i[1], i[2], i[3], obs[1], spec_range)
        corr = correlation.Correlation(dp1, dp2, False, False, True, True, 16, 500, 180)
        corr.getPeaks()
        corr.plotCurve(ax, i[3])
        corr.compareToTest(correlation.Comparison([i[3]]))

    plt.tight_layout()
    plt.show()


# TODO test difficult days with others stations -> improvement?


if __name__ == '__main__':
    bacBurstFailed()

    # nobg = False
    # bin_f = False
    # bin_t = False
    # flatten = False
    # bin_t_w = 1
    # flatten_w = 1
    # nobg = True
    # for r_w in range(20, 260, 20):
    #     testBacBursts(nobg, bin_f, bin_t, flatten, bin_t_w, flatten_w, r_w)
    #
    # r_w = 160
    # flatten = True
    # for flatten_w in range(40, 400, 60):
    #     testBacBursts(nobg, bin_f, bin_t, flatten, bin_t_w, flatten_w, r_w)
    #
    # r_w = 160
    # flatten = False
    # bin_t = True
    # for bin_t_w in range(2, 16, 2):
    #     testBacBursts(nobg, bin_f, bin_t, flatten, bin_t_w, flatten_w, r_w)

    # r_w = 180
    # flatten = True
    # flatten_w = 220
    # bin_f = True
    # for nobg in range(2):
    #     testBacBursts(nobg, bin_f, bin_t, flatten, bin_t_w, flatten_w, r_w)

    # flatten = True
    # flatten_w = 220
    # bin_f = True
    # nobg = True
    # bin_t = True
    # bin_t_w = 4
    # for r_w in range(120, 260, 10):
    #     testBacBursts(nobg, bin_f, bin_t, flatten, bin_t_w, flatten_w, r_w)

"""


   andere ecallisto auswertungen -> type 3
   warum/wie/welche werte setzen -> i.e. binsize -> ___statistics___ 
   
   ordner -> test files -> known bursts, empties, type 2/3 overlay (anfang november 21), gewitter
   background remove -> yes/no, why - does it get better? 
   
   1/11 10:52-10:52  11:06-11:07
   2/11 10:14-10:15                         | gewitter
   3/11 09:31-09:32  14:06-14:08	        | gewitter
   
   
"""

hard_reference = [[2017, 6, 1, correlation.Comparison(["11:34:00"])],
                  [2017, 7, 11, correlation.Comparison(["13:20:00"])],
                  [2017, 9, 7, correlation.Comparison(["09:53:00", "10:15:00", "12:55:00"])],
                  [2017, 9, 8, correlation.Comparison(["07:06:00", "09:20:00", "10:47:00", "10:54:00",
                                                       "13:22:00", "14:01:00", "15:37:00"])],
                  [2017, 9, 9, correlation.Comparison(["11:17:00", "11:44:00"])],
                  [2017, 9, 27, correlation.Comparison(["12:10:00"])],
                  [2020, 3, 8, correlation.Comparison(["15:33:00", "15:36:00"])],
                  [2020, 11, 20, correlation.Comparison(["13:28:00"])],
                  [2020, 11, 22, correlation.Comparison(["11:00:00", "11:08:00", "14:17:00"])],
                  [2020, 12, 27, correlation.Comparison(["11:37:00", "12:35:00"])],
                  [2020, 12, 30, correlation.Comparison(["14:26:00"])],
                  [2021, 4, 26, correlation.Comparison(["13:56:00"])]]

failed = [[2017, 6, 1, correlation.Comparison(["11:34:00"])],
          [2017, 7, 11, correlation.Comparison(["13:20:00"])],
          [2017, 9, 7, correlation.Comparison(["09:53:00"])],
          [2017, 9, 7, correlation.Comparison(["10:15:00"])],
          [2017, 9, 7, correlation.Comparison(["12:55:00"])],
          [2017, 9, 8, correlation.Comparison(["15:37:00"])],
          [2017, 9, 9, correlation.Comparison(["11:17:00"])],
          [2017, 9, 9, correlation.Comparison(["11:44:00"])],
          [2017, 9, 27, correlation.Comparison(["12:10:00"])],
          [2020, 3, 8, correlation.Comparison(["15:33:00"])],
          [2020, 3, 8, correlation.Comparison(["15:36:00"])],
          [2020, 11, 20, correlation.Comparison(["13:28:00"])],
          [2020, 11, 22, correlation.Comparison(["14:17:00"])],
          [2020, 12, 27, correlation.Comparison(["11:37:00"])],
          [2020, 12, 27, correlation.Comparison(["12:35:00"])],
          [2020, 12, 30, correlation.Comparison(["14:26:00"])],
          [2021, 4, 26, correlation.Comparison(["13:56:00"])]]

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