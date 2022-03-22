#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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


def show_1():
    """
    ganzer tag (herunterladen)
    mehrere observatories
    korrelationskurve berechnen (plotten)
    peaks suchen, zeitpunkt bestimmen
    """
    year = year_1
    month = month_1
    day = day_1

    obs_list = observatories.observatory_list
    download.downloadFullDay(year, month, day, observatories.observatory_list)
    obs_0 = observatories.observatory_dict[obs_list[0]]
    obs_1 = observatories.observatory_dict[obs_list[1]]
    obs_2 = observatories.observatory_dict[obs_list[2]]
    obs_3 = observatories.observatory_dict[obs_list[3]]

    download.downloadFullDay(year, month, day, obs_list)
    corr0, time0, obs0 = analysis.correlateLightCurveDay(year, month, day, obs_0, obs_1, spec_range,
                                                         _plot=True, _bin_time=False)
    # corr1, time1, obs1 = analysis.correlateLightCurveDay(year, month, day, obs_0, obs_2, spec_range)
    # corr2, time2, obs2 = analysis.correlateLightCurveDay(year, month, day, obs_0, obs_3, spec_range,
    #                                                              _plot=True)
    # corr3, time3, obs3 = analysis.correlateLightCurveDay(year, month, day, obs_1, obs_2, spec_range)
    # corr4, time4, obs4 = analysis.correlateLightCurveDay(year, month, day, obs_1, obs_3, spec_range)
    analysis.getPeaksFromCorrelation(corr0, time0, obs0)
    # analysis.getPeaksFromCorrelation(corr1, time1, obs1)
    # analysis.getPeaksFromCorrelation(corr2, time2, obs2)
    # analysis.getPeaksFromCorrelation(corr3, time3, obs3)
    # analysis.getPeaksFromCorrelation(corr4, time4, obs4)

    corr0, time0, obs0 = analysis.correlateLightCurveDay(year, month, day, obs_0, obs_1, spec_range,
                                                         _plot=True, _no_background=True, _bin_time=False)
    analysis.getPeaksFromCorrelation(corr0, time0, obs0)


"""
http://soleil.i4ds.ch/solarradio/data/BurstLists/2010-yyyy_Monstein/2020/e-CALLISTO_2020_10.txt
03: 24 - 03:24
06: 00 - 06:02    
08: 50 - 08:52   *
10: 57 - 10:58   *
11: 43 - 11:43   *
15: 49 - 15:49
15: 53 - 15:53
16: 35 - 16:35
17: 16 - 17:17
17: 24 - 17:26
"""


def show_2():
    """
    ganzer tag, ein observatory
    plotten
    lightcurve plotten

    background abziehen
    plotten
    """
    year = year_1
    month = month_1
    day = day_1
    # download.downloadFullDay(year, month, day, [observatories.observatory_list[0]])
    data_day = analysis.createDay(year, month, day, observatories.observatory_dict[
        observatories.observatory_list[0]], spec_range)
    data_day = sum(data_day)
    data_day.plot()
    data_day.createSummedLightCurve(spec_range)
    analysis.plot_data_time(data_day.spectrum_data.time_axis, data_day.summedLightCurve,
                            data_day.spectrum_data.start.timestamp())
    data_day.subtract_background()
    data_day.plot()


def show_3():
    """
    single file :
    punkt erstellen, lightcurve berechnen und plotten

    achtung:
    interne struktur erwartet die file im korrekten ordner
    <script>/eCallistoData/<year>/<month>/<day>/

    """
    file = 'AUSTRIA-UNIGRAZ_20201023_113001_01.fit.gz'
    dp = data.DataPoint(file)
    dp.createSummedCurve(spec_range)
    analysis.plot_data_time(dp.spectrum_data.time_axis, dp.summedCurve,
                            dp.spectrum_data.start.timestamp())


def show_4():
    year = year_1
    month = month_1
    day = day_1

    data_day = analysis.createDay(year, month, day, observatories.observatory_dict[
        observatories.observatory_list[3]], spec_range)
    data_day = sum(data_day)
    data_day.plot()


def show_5():
    year = year_2
    month = month_2
    day = day_2

    obs_list = observatories.observatory_list
    download.downloadFullDay(year, month, day, observatories.observatory_list)
    obs_0 = observatories.observatory_dict[obs_list[0]]
    obs_1 = observatories.observatory_dict[obs_list[1]]
    obs_2 = observatories.observatory_dict[obs_list[2]]
    obs_3 = observatories.observatory_dict[obs_list[3]]
    obs_4 = observatories.observatory_dict[obs_list[4]]
    obs_5 = observatories.observatory_dict[obs_list[5]]
    obs_6 = observatories.observatory_dict[obs_list[6]]

    # download.downloadFullDay(year, month, day, obs_list)
    # corr0, time0, obs0 = analysis.correlateLightCurveDay(year, month, day, obs_0, obs_1, spec_range,
    #                                                              _plot=True, _binned=False)
    # analysis.getPeaksFromCorrelation(corr0, time0, obs0)
    #
    # corr0, time0, obs0 = analysis.correlateLightCurveDay(year, month, day, obs_0, obs_1, spec_range,
    #                                                              _plot=True, _no_background=True, _binned=False)
    # analysis.getPeaksFromCorrelation(corr0, time0, obs0)
    # corr0, time0, obs0 = analysis.correlateLightCurveDay(year, month, day, obs_0, obs_1, spec_range,
    #                                                              _plot=True, _binned=True)
    # analysis.getPeaksFromCorrelation(corr0, time0, obs0)
    #
    # corr0, time0, obs0 = analysis.correlateLightCurveDay(year, month, day, obs_0, obs_1, spec_range,
    #                                                              _plot=True, _no_background=True, _binned=True)
    # analysis.getPeaksFromCorrelation(corr0, time0, obs0)
    #
    # -------------------------------------------------------------------------------------------------
    corr0, time0, obs0 = analysis.correlateLightCurveDay(year, month, day, obs_3, obs_6, spec_range,
                                                         _plot=True)
    analysis.getPeaksFromCorrelation(corr0, time0, obs0)

    corr0, time0, obs0 = analysis.correlateLightCurveDay(year, month, day, obs_3, obs_6, spec_range,
                                                         _plot=True, _no_background=True)
    analysis.getPeaksFromCorrelation(corr0, time0, obs0)
    corr0, time0, obs0 = analysis.correlateLightCurveDay(year, month, day, obs_3, obs_6, spec_range,
                                                         _plot=True)
    analysis.getPeaksFromCorrelation(corr0, time0, obs0)

    corr0, time0, obs0 = analysis.correlateLightCurveDay(year, month, day, obs_3, obs_6, spec_range,
                                                         _plot=True, _no_background=True)
    analysis.getPeaksFromCorrelation(corr0, time0, obs0)
    """
    03:06-03:06		Australia-ASSA
    04:57-04:58		Australia-ASSA
    06:18-06:18		Australia-ASSA
    09:49-09:49		GLASGOW, HUMAIN, SWISS-HEITERSWIL
    10:39-10:40		GLASGOW, HUMAIN, SWISS-HEITERSWIL, SWISS-Landschlacht
    10:50-10:52		GLASGOW
    12:29-12:29	*	AUSTRIA-UNIGRAZ, BIR, (EGYPT-Alexandria), GLASGOW, HUMAIN, MRO, SWISS-HEITERSWIL, SWISS-Landschlacht
    13:00-13:04		BIR, DENMARK, EGYPT-Alexandria, GLASGOW, HUMAIN, SWISS-HEITERSWIL, SWISS-Landschlacht, (SWISS-MUHEN)
    13:29-13:31		BIR, DENMARK, EGYPT-Alexandria, GLASGOW, HUMAIN, SWISS-HEITERSWIL, SWISS-Landschlacht
    13:56-13:56		BIR, HUMAIN
    14:04-14:04	*	AUSTRIA-UNIGRAZ, BIR, DENMARK, EGYPT-Alexandria, GLASGOW, HUMAIN, INPE, MEXART, MRO, SWISS-HEITERSWIL, SWISS-IRSOL, SWISS-Landschlacht,  SWISS-MUHEN
    14:34-14:34		BIR, HUMAIN, (SWISS-HEITERSWIL)
    18:34-18:35		ALASKA-COHOE
    18:46-18:47		ALASKA-COHOE, BIR, MEXART
    """


def show_6():
    year = year_2
    month = month_2
    day = day_2
    # download.downloadFullDay(year, month, day, [observatories.observatory_list[0]])
    data_day = analysis.createDay(year, month, day, observatories.observatory_dict[
        observatories.observatory_list[3]], spec_range)
    data_day = sum(data_day)
    data_day.plot()
    # data_day.createSummedLightCurve(spec_range, binned=False)
    # analysis.plot_data_time(data_day.spectrum_data.time_axis, data_day.summedLightCurve,
    #                                  data_day.spectrum_data.start.timestamp())

    data_day.subtract_background()

    data_day.createSummedLightCurve(spec_range, binned=False)
    analysis.plot_data_time(data_day.spectrum_data.time_axis, data_day.summedLightCurve,
                            data_day.spectrum_data.start.timestamp())
    data_day.plot()


def show_6_2():
    year = year_2
    month = month_2
    day = day_2
    # download.downloadFullDay(year, month, day, [observatories.observatory_list[0]])
    data_day = analysis.createDay(year, month, day, observatories.observatory_dict[
        observatories.observatory_list[0]], spec_range)
    data_day = sum(data_day)
    data_day.plot()
    data_day.createSummedLightCurve(spec_range, binned=False)
    analysis.plot_data_time(data_day.spectrum_data.time_axis, data_day.summedLightCurve,
                            data_day.spectrum_data.start.timestamp())
    data_day.subtract_background()
    data_day.plot()


def test1():
    year = year_2
    month = month_2
    day = day_2
    data_day = analysis.createDay(year, month, day, observatories.observatory_dict[
        observatories.observatory_list[6]], spec_range)
    data_day = sum(data_day)
    data_day.createSummedLightCurve(spec_range, binned=False)
    analysis.plot_data_time(data_day.spectrum_data.time_axis, data_day.summedLightCurve,
                            data_day.spectrum_data.start.timestamp())
    analysis.getPeaksFromCorrelation(data_day.summedLightCurve, data_day.spectrum_data.start.timestamp(),
                                     [observatories.observatory_dict[
                                          observatories.stat_uni_graz],
                                      observatories.observatory_dict[
                                          observatories.stat_uni_graz]], _limit=14000)


def show0612_1():
    year = year_2
    month = month_2
    day = day_2

    obs_list = observatories.observatory_list
    download.downloadFullDay(year, month, day, observatories.observatory_list)
    obs_0 = observatories.observatory_dict[obs_list[0]]
    obs_1 = observatories.observatory_dict[obs_list[1]]
    obs_2 = observatories.observatory_dict[obs_list[2]]
    obs_3 = observatories.observatory_dict[obs_list[3]]
    obs_4 = observatories.observatory_dict[obs_list[4]]
    obs_5 = observatories.observatory_dict[obs_list[5]]
    obs_6 = observatories.observatory_dict[obs_list[6]]

    # download.downloadFullDay(year, month, day, obs_list)
    # corr0, time0, obs0 = analysis.correlateLightCurveDay(year, month, day, obs_0, obs_1, spec_range,
    #                                                              _plot=True, _binned=False)
    # analysis.getPeaksFromCorrelation(corr0, time0, obs0)
    #
    # corr0, time0, obs0 = analysis.correlateLightCurveDay(year, month, day, obs_0, obs_1, spec_range,
    #                                                              _plot=True, _no_background=True, _binned=False)
    # analysis.getPeaksFromCorrelation(corr0, time0, obs0)
    # corr0, time0, obs0 = analysis.correlateLightCurveDay(year, month, day, obs_0, obs_1, spec_range,
    #                                                              _plot=True, _binned=True)
    # analysis.getPeaksFromCorrelation(corr0, time0, obs0)
    #
    # corr0, time0, obs0 = analysis.correlateLightCurveDay(year, month, day, obs_0, obs_1, spec_range,
    #                                                              _plot=True, _no_background=True, _binned=True)
    # analysis.getPeaksFromCorrelation(corr0, time0, obs0)
    #
    # -------------------------------------------------------------------------------------------------
    corr0, time0, obs0 = analysis.correlateLightCurveDay(year, month, day, obs_3, obs_6, spec_range,
                                                         _plot=True)
    analysis.getPeaksFromCorrelation(corr0, time0, obs0)

    corr0, time0, obs0 = analysis.correlateLightCurveDay(year, month, day, obs_3, obs_6, spec_range,
                                                         _plot=True, _bin_time=True)
    analysis.getPeaksFromCorrelation(corr0, time0, obs0, _binned_time=True)

    corr0, time0, obs0 = analysis.correlateLightCurveDay(year, month, day, obs_3, obs_6, spec_range,
                                                         _plot=True, _bin_time=True, _bin_freq=True)
    analysis.getPeaksFromCorrelation(corr0, time0, obs0, _binned_time=True)


def testrun1701():
    year = year_2
    month = month_2
    day = day_2
    obs_list = observatories.observatory_list
    download.downloadFullDay(year, month, day, observatories.observatory_list)
    obs_3 = observatories.observatory_dict[obs_list[3]]
    obs_6 = observatories.observatory_dict[obs_list[6]]

    for i in range(20, 360, 20):
        c0, t0, o0 = analysis.correlateLightCurveDay(year, month, day, obs_3, obs_6, spec_range, _plot=False,
                                                     _no_background=False, _bin_freq=False, _bin_time=False,
                                                     _rolling_window=i,
                                                     _bin_time_width=1,
                                                     _flatten_light_curve=False,
                                                     _flatten_light_curve_window=100)
        analysis.getPeaksFromCorrelation(c0, t0, o0)


def testrun1701_2():
    year = year_2
    month = month_2
    day = day_2
    obs_list = observatories.observatory_list
    download.downloadFullDay(year, month, day, observatories.observatory_list)
    obs_3 = observatories.observatory_dict[obs_list[3]]
    obs_6 = observatories.observatory_dict[obs_list[6]]

    for i in range(100, 260, 20):
        c0, t0, o0 = analysis.correlateLightCurveDay(year, month, day, obs_3, obs_6, spec_range, _plot=False,
                                                     _no_background=False, _bin_freq=True, _bin_time=False,
                                                     _rolling_window=i,
                                                     _bin_time_width=1,
                                                     _flatten_light_curve=True,
                                                     _flatten_light_curve_window=200)
        analysis.getPeaksFromCorrelation(c0, t0, o0)


def test2401():
    import matplotlib.pyplot as plt
    import numpy as np
    year = year_2
    month = month_2
    day = day_2
    obs_list = observatories.observatory_list
    obs = [observatories.observatory_dict[obs_list[i]] for i in range(3)]
    day_o = [sum(analysis.createDay(year, month, day, i, spec_range)) for i in obs]

    for i in day_o:
        print(i)
        i.plot()
        i.createSummedLightCurve(spec_range)
        i.flattenSummedLightCurve()
        print(np.nanstd(i.summedLightCurve))

        plt.plot(i.summedLightCurve)
        plt.show()
    print('done')
    for i in day_o:
        print(i)
        i.binDataFreq()
        i.createSummedLightCurve(spec_range)
        i.flattenSummedLightCurve()
        print(np.nanstd(i.summedLightCurve))

        plt.plot(i.summedLightCurve)
        plt.show()


if __name__ == '__main__':
    days = [[18, 10, 11, 2, 4, 6, 7, 8, 9, 27, 8, 27, 20, 21, 22, 27, 30, 24, 26],
            [4, 6, 7, 9, 9, 9, 9, 9, 9, 9, 3, 10, 11, 11, 11, 12, 12, 4, 4],
            [2017, 2017, 2017, 2017, 2017, 2017, 2017, 2017, 2017, 2017, 2017, 2020, 2020, 2020, 2020, 2020, 2020, 2021,
             2021]]
    obs = [observatories.uni_graz, observatories.oe3flb, observatories.swiss_landschlacht, observatories.austria]
    obs_dl = [i.name for i in obs]
    test_2017_04_18 = correlation.Comparison(["09:36:00"])

    download.downloadFullDay(days[2][0], days[1][0], days[0][0], obs_dl)
    d1 = data.createDay(days[2][0], days[1][0], days[0][0], obs[0], spec_range)
    d2 = data.createDay(days[2][0], days[1][0], days[0][0], obs[3], spec_range)
    #d3 = data.createDay(days[2][0], days[1][0], days[0][0], obs[2], spec_range)
    d11, d12 = data.fitTimeFrameDataSample(d1, d2)
    #d21, d22 = data.fitTimeFrameDataSample(d1, d3)
    c1 = correlation.Correlation(d11, d12, False, False, False, False, 1, 1, 160)
    #c2 = correlation.Correlation(d21, d22, False, False, False, False, 1, 1, 160)

    c1.getPeaks()
    c1.printResult()
    #c2.getPeaks()
    #c2.printResult()

    c1.compareToTest(test_2017_04_18)


def a():
    days = [[18, 10, 11, 2, 4, 6, 7, 8, 9, 27, 8, 27, 20, 21, 22, 27, 30, 24, 26],
            [4, 6, 7, 9, 9, 9, 9, 9, 9, 9, 3, 10, 11, 11, 11, 12, 12, 4, 4],
            [2017, 2017, 2017, 2017, 2017, 2017, 2017, 2017, 2017, 2017, 2017, 2020, 2020, 2020, 2020, 2020, 2020, 2021,
             2021]]
    obs = [observatories.uni_graz, observatories.oe3flb, observatories.swiss_landschlacht]
    obs_dl = [i.name for i in obs]
    test_2017_04_18 = correlation.Comparison(["09:36:00"])
    test_2017_06_01 = correlation.Comparison(["11:34:00"])
    test_2017_07_11 = correlation.Comparison(["13:20:00"])
    test_2017_09_02 = correlation.Comparison(["12:28:00"])
    test_2017_09_04 = correlation.Comparison(["08:33:00"])
    test_2017_09_06 = correlation.Comparison(["09:18:00", "15:25:00"])
    test_2017_09_07 = correlation.Comparison(["09:53:00", "10:15:00", "12:55:00"])
    test_2017_09_08 = correlation.Comparison(
        ["07:06:00", "09:20:00", "10:47:00", "10:54:00", "13:22:00", "14:01:00", "15:37:00"])
    test_2017_09_09 = correlation.Comparison(["11:17:00", "11:44:00"])
    test_2017_09_27 = correlation.Comparison(["12:10:00"])
    test_2017_03_08 = correlation.Comparison(["15:33:00", "15:36:00"])
    test_2020_10_27 = correlation.Comparison(["08:52:00", "10:58:00", "11:43:00"])
    test_2020_11_20 = correlation.Comparison(["13:28:00"])
    test_2020_11_21 = correlation.Comparison(["10:46:00", "11:32:00"])
    test_2020_11_22 = correlation.Comparison(["11:00:00", "11:08:00", "14:17:00"])
    test_2020_12_27 = correlation.Comparison(["11:37:00", "12:35:00"])
    test_2020_12_30 = correlation.Comparison(["14:26:00"])
    test_2021_04_24 = correlation.Comparison(["10:23:00"])
    test_2021_04_26 = correlation.Comparison(["13:56:00"])

    # ach fuck
    for i in range(len(days[0])):
        download.downloadFullDay(days[2][i], days[1][i], days[0][i], obs_dl)
        d1 = data.createDay(year_1, month_1, day_1, obs[0], spec_range)
        d2 = data.createDay(year_1, month_1, day_1, obs[1], spec_range)
        d3 = data.createDay(year_1, month_1, day_1, obs[2], spec_range)
        d11, d12 = data.fitTimeFrameDataSample(d1, d2)
        d21, d22 = data.fitTimeFrameDataSample(d1, d3)
        c1 = correlation.Correlation(d11, d12, False, False, False, False, 1, 1, 160)
        c2 = correlation.Correlation(d21, d22, False, False, False, False, 1, 1, 160)

        c1.getPeaks()
        c1.printResult()
        c2.getPeaks()
        c2.printResult()

        c1.compareToTest(test_2017_04_18)
"""


   andere ecallisto auswertungen -> type 3
   warum/wie/welche werte setzen -> i.e. binsize -> ___statistics___ 
   
   ordner -> test files -> known bursts, empties, type 2/3 overlay (anfang november 21), gewitter
   background remove -> yes/no, why - does it get better? 
   
   1/11 10:52-10:52  11:06-11:07
   2/11 10:14-10:15                         | gewitter
   3/11 09:31-09:32  14:06-14:08	        | gewitter
   
   
"""
