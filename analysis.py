#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import copy
from datetime import datetime

from typing import List

import data
import observatories
import const

LIMIT = 0.70
DATA_POINTS_PER_SECOND = const.DATA_POINTS_PER_SECOND
BIN_FACTOR = const.BIN_FACTOR


def correlateLightCurves(_data_point1: data.DataPoint, _data_point2: data.DataPoint,
                         _no_background: bool, _bin_freq: bool, _bin_time: bool, _flatten: bool, _bin_time_width: int,
                         _flatten_window: int, _r_window, _plot=True):
    """
    calculates rolling coefficient of two data samples
    misses first terms (r_window) due to calculation method

    :param _flatten_window:
    :param _bin_time_width:
    :param _flatten:
    :param _bin_time:
    :param _bin_freq:
    :param _no_background:
    :param _data_point1:
    :param _data_point2:
    :param _r_window: size of rolling window ~(160-200)
    :param _plot: bool, if result should be plotted
    :return: list[float] rolling coefficients
    """

    frequency_low = max(_data_point1.spectrum_data.freq_axis[-1], _data_point2.spectrum_data.freq_axis[-1])
    frequency_high = min(_data_point1.spectrum_data.freq_axis[0], _data_point2.spectrum_data.freq_axis[0])
    frequency_range = [frequency_low, frequency_high]
    if not _data_point1.summedCurve:
        _data_point1.createSummedCurve(frequency_range)
        if _flatten:
            _data_point1.flattenSummedCurve(_flatten_window)
    if not _data_point2.summedCurve:
        _data_point2.createSummedCurve(frequency_range)
        if _flatten:
            _data_point2.flattenSummedCurve(_flatten_window)

    time_axis = copy.copy(_data_point1.spectrum_data.time_axis)
    time_start_1 = _data_point1.spectrum_data.start.timestamp()
    time_start_2 = _data_point2.spectrum_data.start.timestamp()

    if _bin_time:
        data_per_second = DATA_POINTS_PER_SECOND / _bin_time_width
    else:
        data_per_second = DATA_POINTS_PER_SECOND

    if time_start_2 > time_start_1:
        time_start = time_start_2
    else:
        time_start = time_start_1

    time_start_delta = int((time_start_1 - time_start_2) * data_per_second)
    if time_start_delta > 0:
        curve1 = _data_point1.summedCurve[:-time_start_delta]
        curve2 = _data_point2.summedCurve[time_start_delta:]
        time_axis = time_axis[:-time_start_delta]

    elif time_start_delta < 0:
        curve1 = _data_point1.summedCurve[-time_start_delta:]
        curve2 = _data_point2.summedCurve[:time_start_delta]
        time_axis = time_axis[-time_start_delta:]

    else:
        curve1 = _data_point1.summedCurve
        curve2 = _data_point2.summedCurve

    if len(curve1) > len(curve2):
        time_axis = time_axis[:-abs(len(curve1) - len(curve2))]
        curve1 = curve1[:-abs(len(curve1) - len(curve2))]
    elif len(curve2) > len(curve1):
        curve2 = curve2[:-abs(len(curve2) - len(curve1))]

    correlation = pd.Series(curve1).rolling(_r_window).corr(pd.Series(curve2))

    plot_data_time(time_axis, correlation, time_start, _data_point1.year, _data_point1.month, _data_point1.day,
                   _data_point1.observatory.name, _data_point2.observatory.name, _no_background, _bin_freq,
                   _bin_time, _flatten, _bin_time_width, _flatten_window, _r_window, _plot=_plot)

    return correlation.replace([np.inf, -np.inf], np.nan).tolist(), time_start, [_data_point1.observatory,
                                                                                 _data_point2.observatory]


# -> data.py
#def createDay(_year: int, _month: int, _day: int, _observatory: observatories.Observatory,
#              _spectral_range: List[int]):
#    """
#    Creates a list with DataPoints for a specific day for a Observatory with a specific spectral range
#
#    TODO: function the spectral_id = next() line
#
#    :param _year:
#    :param _month:
#    :param _day:
#    :param _observatory:
#    :param _spectral_range: [spectral, range]
#    :return: List[DataPoints]
#    """
#    path = const.pathDataDay(_year, _month, _day)
#    files_day = sorted(os.listdir(path))
#    spectral_id = next(key for key, s_range in _observatory.spectral_range.items() if s_range == _spectral_range)
#    files_observatory = []
#    data_day = []
#
#    for file in files_day:
#        if file.startswith(_observatory.name) and file.endswith(spectral_id + data.DataPoint.file_ending):
#            files_observatory.append(file)
#
#    for file in files_observatory:
#        data_day.append(data.DataPoint(file))  # try except |error -> TRIEST_20210906_234530_57.fit   TODO
#    return data_day
#
#
## -> data
#def fitTimeFrameDataSample(_data_point1: List[data.DataPoint], _data_point2: List[data.DataPoint]):
#    """
#    shortens the list of DataPoints of different timeframe to a single biggest possible timeframe
#
#    TODO: where data is cut, and why
#
#    TODO: throw - no overlap
#
#    :param _data_point1: List[DataPoints]
#    :param _data_point2: List[DataPoints]
#    :return: DataPoint(timeframe), DataPoint(timeframe)
#    """
#    while _data_point1[0].hour + _data_point1[0].minute / 60 != _data_point2[0].hour + _data_point2[0].minute / 60:
#        if _data_point1[0].hour + _data_point1[0].minute / 60 < _data_point2[0].hour + _data_point2[0].minute / 60:
#            _data_point1.pop(0)
#        else:
#            _data_point2.pop(0)
#    while _data_point1[-1].hour + _data_point1[-1].minute / 60 != _data_point2[-1].hour + _data_point2[-1].minute / 60:
#        if _data_point1[-1].hour + _data_point1[-1].minute / 60 < _data_point2[-1].hour + _data_point2[-1].minute / 60:
#            _data_point2.pop(-1)
#        else:
#            _data_point1.pop(-1)
#
#    data_merged1 = sum(_data_point1)
#    data_merged2 = sum(_data_point2)
#    return data_merged1, data_merged2


# not in class probably
def correlateLightCurveDay(_year: int, _month: int, _day: int, _observatory1: observatories.Observatory,
                           _observatory2: observatories.Observatory, _spectral_range: List[int],
                           _no_background=False, _bin_freq=False, _bin_time=False,
                           _rolling_window=const.ROLL_WINDOW,
                           _bin_time_width=data.DATA_POINTS_PER_SECOND / data.BIN_FACTOR,
                           _flatten_light_curve=False, _flatten_light_curve_window=data.CURVE_FLATTEN_WINDOW,
                           _plot=False):
    """
    Calculates the correlation of the lightcurve for a whole day for two observatories in the same spectral range

    TODO: throw if spectral range is not available

    :param _rolling_window:
    :param _flatten_light_curve_window:
    :param _flatten_light_curve:
    :param _bin_time_width:
    :param _bin_time:
    :param _bin_freq:
    :param _no_background: removes background from data_points if set
    :param _plot: whether a plot gets printed to screen
    :param _year:
    :param _month:
    :param _day:
    :param _observatory1:
    :param _observatory2:
    :param _spectral_range:
    :return: List, correlation
    """
    data_obs_1 = data.createDay(_year, _month, _day, _observatory1, _spectral_range)
    data_obs_2 = data.createDay(_year, _month, _day, _observatory2, _spectral_range)

    data_sum_obs1, data_sum_obs2 = data.fitTimeFrameDataSample(data_obs_1, data_obs_2)

    if _bin_freq:
        data_sum_obs1.binDataFreq()
        data_sum_obs2.binDataFreq()
    if _bin_time:
        data_sum_obs1.binDataTime(width=_bin_time_width)
        data_sum_obs2.binDataTime(width=_bin_time_width)
    if _no_background:
        data_sum_obs1.subtract_background()
        data_sum_obs2.subtract_background()

    return correlateLightCurves(data_sum_obs1, data_sum_obs2, _no_background, _bin_freq, _bin_time,
                                _flatten_light_curve, _bin_time_width, _flatten_light_curve_window, _rolling_window,
                                _plot=_plot, )


def getPeaksFromCorrelation(correlation: List[float], starting_time: float,
                            observatories: List[observatories.Observatory], _limit=LIMIT, _binned_time=False):
    """

    :param _binned_time:
    :param _limit: correlation level needed to count as burst
    :param observatories:
    :param correlation:
    :param starting_time:
    """
    if _binned_time:
        data_per_second = DATA_POINTS_PER_SECOND / BIN_FACTOR
    else:
        data_per_second = DATA_POINTS_PER_SECOND

    bursts = []
    within_burst = False
    if np.nanmax(correlation) < _limit:
        print("No Bursts {}  {} \n".format(observatories[0].name, observatories[1].name))
        return
    for point in range(len(correlation)):
        if correlation[point] > _limit and not within_burst:
            bursts.append([point, correlation[point]])
            within_burst = True
        if correlation[point] > _limit and within_burst and correlation[point] > bursts[-1][1]:
            bursts[-1][1] = correlation[point]
        if within_burst and correlation[point] < _limit:
            within_burst = False

    if bursts[0]:
        for i in range(len(bursts)):
            bursts[i][0] = datetime.fromtimestamp(bursts[i][0] / data_per_second + starting_time).strftime(
                "%H:%M:%S")

        print("Burst(s) detected {}  {}  \n".format(observatories[0].name, observatories[1].name), bursts)


def plot_data_time(_time: List[float], _data: List[float], _time_start: float,
                   _year: int, _month: int, _day: int, _obs1: str, _obs2: str, _nobg: bool, _bin_freq: bool,
                   _bin_time: bool, _flatten: bool, _bin_time_width: int, _flatten_window: int, _rolling_window: int,
                   _plot=True):
    """

    :param _time:
    :param _data:
    :param _time_start:
    :param _year:
    :param _month:
    :param _day:
    :param _obs1:
    :param _obs2:
    :param _nobg:
    :param _bin_freq:
    :param _bin_time:
    :param _flatten:
    :param _flatten_window:
    :param _bin_time_width:
    :param _rolling_window:
    :param _plot:
    :return:
    """
    if _bin_time:
        data_per_second = DATA_POINTS_PER_SECOND / _bin_time_width
    else:
        data_per_second = DATA_POINTS_PER_SECOND
    time_axis_plot = []
    for i in range(len(_time)):
        time_axis_plot.append(
            datetime.fromtimestamp(_time_start + i / data_per_second).strftime("%D %H:%M:%S.%f")[:-3])
    time_axis_plot = pd.to_datetime(time_axis_plot)
    dataframe = pd.DataFrame()
    dataframe['data'] = _data
    dataframe = dataframe.set_index(time_axis_plot)

    # method this
    file_name = "{}_{}_{}_{}_{}_{}{}{}{}{}.png".format(_year, _month, _day, _obs1, _obs2, _rolling_window,
                                                       ["", "_nobg"][_nobg], ["", "_binfreq"][_bin_freq],
                                                       ["", "_bintime_{}".format(_bin_time_width)][_bin_time],
                                                       ["", "_flatten_{}".format(_flatten_window)][_flatten])

    plt.figure(figsize=(16, 9))
    fig, ax = plt.subplots()
    fig.subplots_adjust(bottom=0.3)
    plt.xticks(rotation=90)
    plt.plot(dataframe)

    if _plot:
        plt.show()
    else:
        plt.savefig(const.path_plots + file_name)
    plt.close()


"""
function -> per day, pick observatories, download data -> correlate for observatories for which there is data
"""
