#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import copy
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

import events
import data
import config

CORRELATION_MIN = config.correlation_limit_2
CORRELATION_PEAK_END = config.correlation_end
DATA_POINTS_PER_SECOND = config.DATA_POINTS_PER_SECOND
BIN_FACTOR = config.BIN_FACTOR
LENGTH_TYPE_III_AVG = 120    # TODO definition type II / III | seconds ?
TYPE_III = "III"
TYPE_II = " II"
TYPE_IV = " IV"
TYPE_UNKNOWN = "???"                                    # TODO
BURST_TYPE_UNKNOWN = events.BURST_TYPE_UNKNOWN          # TODO
default_time_window = config.BIN_FACTOR
default_flatten_window = 2000
default_r_window = config.ROLL_WINDOW


class Correlation:
    def __init__(self, data_point_1: data.DataPoint, data_point_2: data.DataPoint, day: int,
                 no_background=False, bin_freq=False, bin_time=False, flatten=False,
                 bin_time_width=default_time_window,
                 flatten_window=default_flatten_window,
                 r_window=default_r_window,
                 method_bin_t='median',
                 method_bin_f='median'):

        self.data_point_1 = copy.deepcopy(data_point_1)
        self.data_point_2 = copy.deepcopy(data_point_2)

        self.data_per_second_1 = None       # TODO -> datapoint
        self.data_per_second_2 = None       # TODO -> datapoint

        self.day = day

        if self.data_point_1.spectrum_data.start.day == self.day:
            self.date = self.data_point_1.spectrum_data.start
        elif (self.data_point_1.spectrum_data.start + timedelta(days=1)).day == self.day:
            self.date = self.data_point_1.spectrum_data.start + timedelta(days=1)
        else:
            self.date = self.data_point_1.spectrum_data.start - timedelta(days=1)

        self.no_background = no_background
        self.bin_frequency = bin_freq
        self.bin_time = bin_time
        self.flatten = flatten
        self.flatten_window = flatten_window
        if bin_time_width is None:
            self.bin_time_width = 1
        else:
            self.bin_time_width = bin_time_width
        self.r_window = r_window
        self.method_bin_f = method_bin_f
        self.method_bin_t = method_bin_t

        self.peaks = events.EventList([], self.date)
        self.frequency_range = None
        self.time_axis = None
        time_start_1 = self.data_point_1.spectrum_data.start.timestamp()
        time_start_2 = self.data_point_2.spectrum_data.start.timestamp()
        time_end_1 = self.data_point_1.spectrum_data.end.timestamp()
        time_end_2 = self.data_point_2.spectrum_data.end.timestamp()
        self.time_start = max(time_start_2, time_start_1)
        self.time_end = min(time_end_2, time_end_1)
        self.time_start_delta = None
        self.data_curve = None
        self.data_per_second = [DATA_POINTS_PER_SECOND,
                                DATA_POINTS_PER_SECOND / self.bin_time_width][self.bin_time]

        self.setupFreqRange()
        self.modulateData()
        self.setupSummedCurves()
        self.correlateCurves()
        self.calculateTimeAxis()

    def correlateCurves(self):
        delta_t_start = (self.data_point_1.spectrum_data.start - self.data_point_2.spectrum_data.start).total_seconds()
        delta_t_end = (self.data_point_1.spectrum_data.end - self.data_point_2.spectrum_data.end).total_seconds()

        curve1 = self.data_point_1.summed_curve
        curve2 = self.data_point_2.summed_curve

        if delta_t_start and self.data_point_1.spectrum_data.start < self.data_point_2.spectrum_data.start:
            curve1 = curve1[int(self.data_per_second_1 * abs(delta_t_start)):]
        elif delta_t_start and self.data_point_1.spectrum_data.start > self.data_point_2.spectrum_data.start:
            curve2 = curve2[int(self.data_per_second_2 * abs(delta_t_start)):]

        if delta_t_end and self.data_point_1.spectrum_data.end > self.data_point_2.spectrum_data.end and \
                int(self.data_per_second_1 * abs(delta_t_end)):
            curve1 = curve1[:-int(self.data_per_second_1 * abs(delta_t_end))]
        elif delta_t_end and self.data_point_1.spectrum_data.end < self.data_point_2.spectrum_data.end and \
                int(self.data_per_second_2 * abs(delta_t_end)) > 0:
            curve2 = curve2[:-int(self.data_per_second_2 * abs(delta_t_end))]

        if self.data_per_second_1 < self.data_per_second_2:
            curve1 = np.array([curve1[int(i / (self.data_per_second_2 / self.data_per_second_1))] for i in
                               range(int(self.data_per_second_2 / self.data_per_second_1 * len(curve1)))])
        if self.data_per_second_1 > self.data_per_second_2:
            curve2 = np.array([curve2[int(i / (self.data_per_second_1 / self.data_per_second_2))] for i in
                               range(int(self.data_per_second_1 / self.data_per_second_2 * len(curve2)))])

        self.data_curve = pd.Series(curve1).rolling(self.r_window).corr(pd.Series(curve2))\
                            .replace([np.inf, -np.inf], np.nan).tolist()

    def calculatePeaks(self, limit=CORRELATION_MIN):
        within_burst = False
        high_correlation = False
        peaks = []
        if self.data_point_1.observatory == self.data_point_2.observatory:
            return
        time_start = datetime.fromtimestamp(self.time_start)
        for point in range(len(self.data_curve)):
            if self.data_curve[point] > config.correlation_start and not within_burst and not high_correlation:
                time_start = datetime.fromtimestamp(point / self.data_per_second + self.time_start)
                high_correlation = True

            if self.data_curve[point] > limit and not within_burst:
                burst = events.Event(time_start, probability=self.data_curve[point],
                                     stations=[self.data_point_1.observatory, self.data_point_2.observatory])
                if burst.time_start.day == self.day:
                    peaks.append(burst)
                    within_burst = True

            if self.data_curve[point] > limit and within_burst and self.data_curve[point] > peaks[-1].probability:
                peaks[-1].probability = self.data_curve[point]
            if within_burst and self.data_curve[point] < CORRELATION_PEAK_END:
                time_end = datetime.fromtimestamp(point / self.data_per_second + self.time_start)
                peaks[-1].setTimeEnd(time_end)

                # TODO better differentiation
                if (peaks[-1].time_end - peaks[-1].time_start).total_seconds() <\
                        timedelta(seconds=LENGTH_TYPE_III_AVG).total_seconds():
                    peaks[-1].burst_type = TYPE_III
                else:
                    peaks[-1].burst_type = TYPE_UNKNOWN
                within_burst = False
            if self.data_curve[point] < config.correlation_start:
                high_correlation = False

        if peaks:
            if peaks[-1].burst_type == BURST_TYPE_UNKNOWN:  # TODO
                if peaks[-1].probability == np.around(1, 3):
                    peaks.pop(-1)
                else:
                    peaks[-1].burst_type = TYPE_III
            for peak in peaks:
                if np.isinf(peak.probability):
                    peaks.remove(peak)
            self.peaks = events.EventList(peaks, self.date)

    def fileName(self):
        # TODO time of day ??
        background = ['', '_nobg'][self.no_background]
        bin_frq = ['', '_binfreq'][self.bin_frequency]
        bin_time = ['', '_bintime_{}'.format(self.bin_time_width)][self.bin_time]
        flatten = ['', '_flatten_{}'.format(self.flatten_window)][self.flatten]
        return f"{self.data_point_1.year}_{self.data_point_1.month}_{self.data_point_1.day}_" \
               f"{self.data_point_1.observatory}_{self.data_point_2.observatory}_" \
               f"{self.r_window}{background}{bin_frq}{bin_time}{flatten}.png"

    def printResult(self):
        if not self.peaks:
            print("No bursts detected")
            return
        print(f"Burst(s) detected at: {self.data_point_1.observatory.name} & {self.data_point_2.observatory.name}")
        for i in self.peaks:
            print(i)

    def compareToTest(self, test: events.EventList):
        """
        :return: [not found, false found]
        """
        peaks = copy.copy(self.peaks)
        events_ = copy.copy(test.events)
        for event in test.events:
            if event.inList(self.peaks.events):
                events_.remove(event)
        for peak in self.peaks:
            if peak.inList(test.events):
                peaks -= peak

        if peaks:
            print("peaks mistakenly found: ")
            for p in peaks:
                print(p.time, "c: ", p.probability)
        else:
            print("No false peaks found")
        if events_:
            print("Events not found ({}/{}): \n".format(len(events_), len(test.events)), events_)
        else:
            print("All events found ({})".format(len(test.events)))
        # -> return number_found, number_to_find,
        return [events_, peaks]

    def setupFreqRange(self):
        frequency_low = max(self.data_point_1.spectrum_data.freq_axis[-1],
                            self.data_point_2.spectrum_data.freq_axis[-1])
        frequency_high = min(self.data_point_1.spectrum_data.freq_axis[0],
                             self.data_point_2.spectrum_data.freq_axis[0])
        self.frequency_range = [frequency_low, frequency_high]

    def calculateTimeAxis(self):
        data_per_second = max(self.data_per_second_1, self.data_per_second_2)
        self.time_axis = [i / data_per_second for i in range(len(self.data_curve))]

    def setupSummedCurves(self):
        setupSummedCurve(self.data_point_1, self.frequency_range, self.flatten, self.flatten_window)
        setupSummedCurve(self.data_point_2, self.frequency_range, self.flatten, self.flatten_window)

    def plotCurve(self, ax, peaks=None, label=None, color=None):
        return data.plotCurve(self.time_axis, self.data_curve, self.time_start, self.bin_time, self.bin_time_width,
                              ax, peaks=peaks, new_ax=False, label=label, color=color)

    def modulateData(self):
        self.data_per_second_1 = np.round(self.data_point_1.number_values /
                                          (self.data_point_1.spectrum_data.end - self.data_point_1.spectrum_data.start)
                                          .total_seconds(), 2)
        self.data_per_second_2 = np.round(self.data_point_2.number_values /
                                          (self.data_point_2.spectrum_data.end - self.data_point_2.spectrum_data.start)
                                          .total_seconds(), 2)

        if self.no_background:
            self.data_point_1.subtractBackground()
            self.data_point_2.subtractBackground()
        if self.bin_time:
            self.data_point_1.binDataTime(width=self.bin_time_width, method=self.method_bin_t)
            self.data_point_2.binDataTime(width=self.bin_time_width, method=self.method_bin_t)
            self.data_per_second_1 = self.data_per_second_1 / self.bin_time_width
            self.data_per_second_2 = self.data_per_second_2 / self.bin_time_width
            self.time_axis = np.arange(self.time_start, self.time_end, self.bin_time_width / self.data_per_second)
        if self.bin_frequency:
            self.data_point_1.binDataFreq(method=self.method_bin_f)
            self.data_point_2.binDataFreq(method=self.method_bin_f)


def setupSummedCurve(data_point: data.DataPoint, frequency_range, flatten: bool, flatten_window):
    data_point.createSummedCurve(frequency_range)
    if flatten:
        data_point.flattenSummedCurve(flatten_window)
