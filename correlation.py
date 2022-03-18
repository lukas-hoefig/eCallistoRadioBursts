#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import copy
import numpy as np
import pandas as pd
from datetime import datetime

import data
import observatories
import const

LIMIT = 0.70
DATA_POINTS_PER_SECOND = const.DATA_POINTS_PER_SECOND
BIN_FACTOR = const.BIN_FACTOR


# class TimeCurve:
#     def __init__(self, _time, _data, _time_start):
#         raise NotImplementedError
#
#     def plot(self):
#         raise NotImplementedError
#
#     def getPeaks(self):
#         raise NotImplementedError
#
#
# class SummedCurve(TimeCurve):
#     def __init__(self):
#         super().__init__()
#         raise NotImplementedError


class Correlation:
    def __init__(self, data_point_1: data.DataPoint, data_point_2: data.DataPoint,
                 _no_background: bool, _bin_freq: bool, _bin_time: bool, _flatten: bool, 
                 _bin_time_width: int, _flatten_window: int, _r_window: int):
        # default values
        self.data_point_1 = data_point_1
        self.data_point_2 = data_point_2

        self.no_background = _no_background
        self.bin_frequency = _bin_freq
        self.bin_time = _bin_time
        self.flatten = _flatten
        self.flatten_window = _flatten_window
        self.bin_time_width = _bin_time_width
        self.r_window = _r_window

        self.peaks = []
        self.frequency_range = None
        self.time_axis = None
        self.time_start = None
        self.time_start_delta = None
        self.data_curve = None
        self.data_per_second = [DATA_POINTS_PER_SECOND,
                                DATA_POINTS_PER_SECOND / self.bin_time_width][self.bin_time]

        self.setupFreqRange()
        self.setupSummedCurves()
        self.setupTimeAxis()
        self.correlateCurves()

    def __str__(self):
        return  # TODO

    def __repr__(self):
        return  # TODO

    def correlateCurves(self):
        if self.time_start_delta > 0:
            curve1 = self.data_point_1.summedCurve[:-self.time_start_delta]
            curve2 = self.data_point_2.summedCurve[self.time_start_delta:]
            self.time_axis = self.time_axis[:-self.time_start_delta]

        elif self.time_start_delta < 0:
            curve1 = self.data_point_1.summedCurve[-self.time_start_delta:]
            curve2 = self.data_point_2.summedCurve[:self.time_start_delta]
            self.time_axis = self.time_axis[-self.time_start_delta:]

        else:
            curve1 = self.data_point_1.summedCurve
            curve2 = self.data_point_2.summedCurve

        if len(curve1) > len(curve2):
            self.time_axis = self.time_axis[:-abs(len(curve1) - len(curve2))]
            curve1 = curve1[:-abs(len(curve1) - len(curve2))]
        elif len(curve2) > len(curve1):
            curve2 = curve2[:-abs(len(curve2) - len(curve1))]

        self.data_curve = pd.Series(curve1).rolling(self.r_window).corr(pd.Series(curve2))
        self.data_curve.replace([np.inf, -np.inf], np.nan).tolist()

    def getPeaks(self, _limit=LIMIT):
        within_burst = False
        if np.nanmax(self.data_curve) < _limit:
            print("No Bursts {}  {} \n".format(self.data_point_1.observatory.name,
                                               self.data_point_2.observatory.name))
            return
        for point in range(len(self.data_curve)):
            if self.data_curve[point] > _limit and not within_burst:
                self.peaks.append([point, self.data_curve[point]])
                within_burst = True
            if self.data_curve[point] > _limit and within_burst and self.data_curve[point] > self.peaks[-1][1]:
                self.peaks[-1][1] = self.data_curve[point]
            if within_burst and self.data_curve[point] < _limit:
                within_burst = False

        if self.peaks[0]:
            for i in range(len(self.peaks)):
                self.peaks[i][0] = datetime.fromtimestamp(self.peaks[i][0] / self.data_per_second + self.time_start).strftime(
                    "%H:%M:%S")

            print("Burst(s) detected {}  {}  \n".format(self.data_point_1.observatory.name,
                                                        self.data_point_2.observatory.name), self.peaks)

    def fileName(self):
        return "{}_{}_{}_{}_{}_{}{}{}{}{}.png"\
            .format(self.data_point_1.year, self.data_point_1.month, self.data_point_1.day,
                    self.data_point_1.observatory, self.data_point_2.observatory, self.r_window,
                    ["", "_nobg"][self.no_background], ["", "_binfreq"][self.bin_frequency],
                    ["", "_bintime_{}".format(self.bin_time_width)][self.bin_time],
                    ["", "_flatten_{}".format(self.flatten_window)][self.flatten])

    def printResult(self):
        raise NotImplementedError

    def setupFreqRange(self):
        frequency_low = max(self.data_point_1.spectrum_data.freq_axis[-1],
                            self.data_point_2.spectrum_data.freq_axis[-1])
        frequency_high = min(self.data_point_1.spectrum_data.freq_axis[0],
                             self.data_point_2.spectrum_data.freq_axis[0])
        self.frequency_range = [frequency_low, frequency_high]

    def setupTimeAxis(self):
        self.time_axis = copy.copy(self.data_point_1.spectrum_data.time_axis)
        time_start_1 = self.data_point_1.spectrum_data.start.timestamp()
        time_start_2 = self.data_point_2.spectrum_data.start.timestamp()

        if time_start_2 > time_start_1:
            self.time_start = time_start_2
        else:
            self.time_start = time_start_1
        self.time_start_delta = int((time_start_1 - time_start_2) * self.data_per_second)

    def setupSummedCurves(self):
        setupSummedCurve(self.data_point_1, self.frequency_range, self.flatten, self.flatten_window)
        setupSummedCurve(self.data_point_2, self.frequency_range, self.flatten, self.flatten_window)


def setupSummedCurve(data_point, frequency_range, flatten, flatten_window):
    data_point.createSummedCurve(frequency_range)
    if flatten:
        data_point.flattenSummedCurve(flatten_window)
