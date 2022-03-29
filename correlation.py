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

class Comparison:
    def __init__(self, events):
        self.events = [analysis.Event(event) for event in events]


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

    def getPeaks(self, _limit=CORRELATION_MIN):
        # TODO set min delta t for times
        within_burst = False
        peaks = []
        # if np.nanmax(self.data_curve) < _limit:
        #     print("No Bursts {}  {} \n".format(self.data_point_1.observatory.name,
        #                                        self.data_point_2.observatory.name))
        #     return
        for point in range(len(self.data_curve)):
            if self.data_curve[point] > _limit and not within_burst:
                peaks.append([point, self.data_curve[point]])
                within_burst = True

            # peak or starting time ?
            if self.data_curve[point] > _limit and within_burst and self.data_curve[point] > peaks[-1][1]:
                peaks[-1][1] = self.data_curve[point]
            if within_burst and self.data_curve[point] < CORRELATION_PEAK_END:
                within_burst = False

        if peaks:
            for i in peaks:
                i[0] = datetime.fromtimestamp(i[0] / self.data_per_second + self.time_start).strftime(
                    "%H:%M:%S")
                self.peaks.append(analysis.Event(i[0], probability=i[1]))

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
            if event.inList(self.peaks):
                events.remove(event)
        for peak in self.peaks:
            if peak.inList(test.events):
                peaks.remove(peak)

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


def setupSummedCurve(data_point, frequency_range, flatten, flatten_window):
    data_point.createSummedCurve(frequency_range)
    if flatten:
        data_point.flattenSummedCurve(flatten_window)


def addEventsToList(to_add: List[analysis.Event], add_to: List[analysis.Event]):
    for i in to_add:
        if not i.inList(add_to):
            add_to.append(i)


def removeEventFromList(to_remove: List[analysis.Event], remove_from: List[analysis.Event]):
    for i in to_remove:
        if i.inList(remove_from):
            remove_from.pop(i.inList(remove_from))
