#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt

import const
import data
import observatories
import download
import analysis
import correlation


def missingThings():
    """
    TODO: unify spectral range declaration of observatories -> search possible

    TODO: save graphic to file (ideally without plotting) plt.savefig('foo.png') -> functn needs info -> naming file

    TODO: import calender -automated run through longer timeframes

    TODO: os module - test linux/windows specifics
    """
    pass


year_1 = 2020
month_1 = 10
day_1 = 27
spec_range = [45, 81]

year_2 = 2021
month_2 = 9
day_2 = 6


def testBacBursts():
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
        corr = correlation.Correlation(dp_1_clean, dp_2_clean, False, False, False, False, 1, 1, 160)
        corr.getPeaks()
        corr.compareToTest(i[3])


def bacBurstFailed():
    eventlist = [[2017, 6, 1, '11:34:00']]
    obs = [observatories.uni_graz, observatories.austria, observatories.triest]

    fig, ax = plt.subplots(figsize=(16, 9))

    for o in obs:
        for i in eventlist:
            download.downloadFullDay(i[0], i[1], i[2], o.name)
            dp = data.createFromTime(i[0], i[1], i[2], i[3], o, spec_range)
            dp.createSummedCurve(spec_range)
            dp.flattenSummedCurve(const.ROLL_WINDOW)
            dp.plotSummedCurve(ax, peaks=i[3])

    plt.tight_layout()
    plt.show()


# TODO test difficult days with others stations -> improvement?


if __name__ == '__main__':
    testBacBursts()
    # bacBurstFailed()

"""


   andere ecallisto auswertungen -> type 3
   warum/wie/welche werte setzen -> i.e. binsize -> ___statistics___ 
   
   ordner -> test files -> known bursts, empties, type 2/3 overlay (anfang november 21), gewitter
   background remove -> yes/no, why - does it get better? 
   
   1/11 10:52-10:52  11:06-11:07
   2/11 10:14-10:15                         | gewitter
   3/11 09:31-09:32  14:06-14:08	        | gewitter
   
   
"""
