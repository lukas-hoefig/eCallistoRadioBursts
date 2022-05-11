#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import copy
import numpy as np
import pandas as pd
from datetime import datetime

import analysis
import data
import observatories
import const
from typing import List, Union

CORRELATION_MIN = 0.70
CORRELATION_PEAK_END = CORRELATION_MIN / 7
DATA_POINTS_PER_SECOND = const.DATA_POINTS_PER_SECOND
BIN_FACTOR = const.BIN_FACTOR
LENGTH_TYPE_III_AVG = 200    # TODO definition type II / III
TYPE_III = "III"
TYPE_II = "II"

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

class Comparison(analysis.EventList):
    def __init__(self, events: Union[str, List[str]]):
        if isinstance(events, str):
            events = [events]
        _events = [analysis.Event(event) for event in events]
        super().__init__(_events)


class Correlation:
    def __init__(self, data_point_1: data.DataPoint, data_point_2: data.DataPoint,
                 _no_background=False, _bin_freq=False, _bin_time=False, _flatten=False,
                 _bin_time_width=4, _flatten_window=100, _r_window=180, method_bin_t='median', method_bin_f='median'):

        self.data_point_1 = data_point_1
        self.data_point_2 = data_point_2

        self.no_background = _no_background
        self.bin_frequency = _bin_freq
        self.bin_time = _bin_time
        self.flatten = _flatten
        self.flatten_window = _flatten_window
        self.bin_time_width = _bin_time_width
        self.r_window = _r_window
        self.method_bin_f = method_bin_f
        self.method_bin_t = method_bin_t

        self.peaks = analysis.EventList([])
        self.frequency_range = None
        self.time_axis = None
        self.time_start = None
        self.time_start_delta = None
        self.data_curve = None
        self.data_per_second = [DATA_POINTS_PER_SECOND,
                                DATA_POINTS_PER_SECOND / self.bin_time_width][self.bin_time]

        self.setupFreqRange()
        self.modulateData()
        self.setupSummedCurves()
        self.setupTimeAxis()
        self.correlateCurves()

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

    def calculatePeaks(self, _limit=CORRELATION_MIN):
        within_burst = False
        peaks = []
        # if np.nanmax(self.data_curve) < _limit:
        #     print("No Bursts {}  {} \n".format(self.data_point_1.observatory.name,
        #                                        self.data_point_2.observatory.name))
        #     return
        for point in range(len(self.data_curve)):
            if self.data_curve[point] > _limit and not within_burst:
                time_start = datetime.fromtimestamp(point / self.data_per_second + self.time_start).strftime(
                    const.even_time_format)
                burst = analysis.Event(time_start, self.data_curve[point])
                peaks.append(burst)
                within_burst = True

            # peak or starting time ?
            if self.data_curve[point] > _limit and within_burst and self.data_curve[point] > peaks[-1].probability:
                peaks[-1].probability = self.data_curve[point]
            if within_burst and self.data_curve[point] < CORRELATION_PEAK_END:
                time_end = datetime.fromtimestamp(point / self.data_per_second + self.time_start).strftime(
                    const.even_time_format)
                peaks[-1].time_end = analysis.Time(time_end)

                # TODO better differentiation
                if (peaks[-1].time_end.float - peaks[-1].time_start.float) < LENGTH_TYPE_III_AVG:
                    peaks[-1].burst_type = TYPE_III
                else:
                    peaks[-1].burst_type = TYPE_II
                within_burst = False

        if peaks:
            self.peaks = analysis.EventList(peaks)

    def fileName(self):
        return "{}_{}_{}_{}_{}_{}{}{}{}{}.png"\
            .format(self.data_point_1.year, self.data_point_1.month, self.data_point_1.day,
                    self.data_point_1.observatory, self.data_point_2.observatory, self.r_window,
                    ["", "_nobg"][self.no_background], ["", "_binfreq"][self.bin_frequency],
                    ["", "_bintime_{}".format(self.bin_time_width)][self.bin_time],
                    ["", "_flatten_{}".format(self.flatten_window)][self.flatten])

    def printResult(self):
        if not self.peaks:
            print("No bursts detected")
            return
        print("Burst(s) detected at: {} & {}".format(self.data_point_1.observatory.name,
                                                     self.data_point_2.observatory.name))
        for i in self.peaks:
            print(i)

    def compareToTest(self, test: Comparison):
        """
        :return: [not found, false found]
        """
        peaks = copy.copy(self.peaks)
        events = copy.copy(test.events)
        for event in test.events:
            if event.inList(self.peaks.events):
                events.remove(event)
        for peak in self.peaks:
            if peak.inList(test.events):
                peaks -= peak

        if peaks:
            print("peaks mistakenly found: ")
            for p in peaks:
                print(p.time, "c: ", p.probability)
        else:
            print("No false peaks found")
        if events:
            print("Events not found ({}/{}): \n".format(len(events), len(test.events)), events)
        else:
            print("All events found ({})".format(len(test.events)))
        # -> return number_found, number_to_find,
        return [events, peaks]

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

    def plotCurve(self, ax, peaks=None):
        data.plotCurve(self.time_axis, self.data_curve, self.time_start, self.bin_time, self.bin_time_width,
                       ax, peaks=peaks, new_ax=False)

    def modulateData(self):
        if self.bin_time:
            self.data_point_1.binDataTime(width=self.bin_time_width, method=self.method_bin_t)
            self.data_point_2.binDataTime(width=self.bin_time_width, method=self.method_bin_t)
        if self.bin_frequency:
            self.data_point_1.binDataFreq(method=self.method_bin_f)
            self.data_point_2.binDataFreq(method=self.method_bin_f)


def setupSummedCurve(data_point, frequency_range, flatten, flatten_window):
    data_point.createSummedCurve(frequency_range)
    if flatten:
        data_point.flattenSummedCurve(flatten_window)
