#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from radiospectra.sources.callisto import CallistoSpectrogram
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import copy
from datetime import datetime
import os
from typing import List

# import analysis
import const
import observatories
import download

path_script = const.path_script
path_data = const.path_data
FREQ_MIN = 0
FREQ_MAX = 1
BIN_WIDTH_FREQUENCY = 2
DATA_POINTS_PER_SECOND = const.DATA_POINTS_PER_SECOND
BIN_FACTOR = const.BIN_FACTOR
CURVE_FLATTEN_WINDOW = 100


class DataPoint:
    """
    TODO: shift data by time interval
    """
    file_ending = ".fit.gz"

    def __init__(self, file: str):
        self.spectrum_data = None
        self.number_values = None
        self.summedCurve = []
        self.binned_freq = False
        self.binned_time = False
        self.binned_time_width = 1
        self.background_subtracted = False

        reader = file.rsplit('/')[-1]
        self.file_name = reader
        reader = reader.rsplit('_')

        self.observatory = observatories.observatory_dict[reader[0]]
        self.year = int(reader[1][:4])
        self.month = int(reader[1][4:6])
        self.day = int(reader[1][6:])
        self.hour = int(reader[2][:2])
        self.minute = int(reader[2][2:4])
        self.second = int(reader[2][4:])

        self.spectral_range_id = reader[3][:2]
        self.spectral_range = self.observatory.getSpectralRange(self.spectral_range_id)

        self.path = path_data + str(self.year) + "/" + str(self.month).zfill(2) + "/" + str(self.day).zfill(2) + "/"

        self.readFile()
        self.cleanUpData()

    def __add__(self, other):
        """

        :param other:
        :return:
        """
        temp1 = copy.copy(self)
        temp2 = copy.copy(other)
        temp1.spectrum_data = CallistoSpectrogram.join_many([temp1.spectrum_data, temp2.spectrum_data], maxgap=None)
        temp1.number_values = len(temp1.spectrum_data.time_axis)
        if temp1.binned_freq != temp2.binned_freq:
            temp1.binDataFreq()
            temp2.binDataFreq()
        if temp1.binned_time != temp2.binned_time:
            temp1.binDataTime()
            temp2.binDataTime()

        return temp1

    def __radd__(self, other):
        if other == 0:
            return self
        return self.__add__(other)

    def __str__(self):
        return self.file_name

    def __repr__(self):
        return self.file_name

    def readFile(self):
        """
        reads data from file
        called by __init__
        """
        data_available, stations = download.dataAvailable(self.year, self.month, self.day)
        if data_available:
            if self.observatory.name not in stations:
                download.downloadFullDay(self.year, self.month, self.day, [self.observatory.name])

        self.spectrum_data = CallistoSpectrogram.read(self.path + self.file_name)
        self.number_values = len(self.spectrum_data.time_axis)

    def cleanUpData(self):
        """
        cleans up multiple data entries in frequency range
        called by __init__
        """
        self.spectrum_data.data = self.spectrum_data.data[
                                  np.argmax(self.spectrum_data.freq_axis):np.argmin(self.spectrum_data.freq_axis) + 1,
                                  :]
        self.spectrum_data.freq_axis = self.spectrum_data.freq_axis[np.argmax(self.spectrum_data.freq_axis):np.argmin(
            self.spectrum_data.freq_axis) + 1]

    def binDataFreq(self, bin_width=BIN_WIDTH_FREQUENCY, method='median'):
        """
        bins the data into bigger frequency ranges (2 MHz),
        reduces the impact of outliers and false signals

        :param bin_width: number of data points per bin
        :param method: 'median' or 'mean' as method to average over data
        """
        if method != 'median' and method != 'mean':
            raise Exception
        frequency_min = self.spectral_range[FREQ_MIN]
        frequency_max = self.spectral_range[FREQ_MAX]
        data = self.spectrum_data.data.transpose()
        frequency_range = np.arange(frequency_max, frequency_min - bin_width, -bin_width)

        entries_per_bin = len(self.spectrum_data.freq_axis) / len(frequency_range)
        data_binned = [[] for i in range(self.number_values)]

        if method == 'median':
            for line in range(len(data)):
                for bin_ in range(len(frequency_range)):
                    data_binned[line].append(
                        np.nanmedian(data[line][int(bin_ * entries_per_bin):int((bin_ + 1) * entries_per_bin)]))
        if method == 'mean':
            for line in range(len(data)):
                for bin_ in range(len(frequency_range)):
                    data_binned[line].append(
                        np.nanmean(data[line][int(bin_ * entries_per_bin):int((bin_ + 1) * entries_per_bin)]))

        self.spectrum_data.data = np.array(data_binned).transpose()
        self.spectrum_data.freq_axis = frequency_range
        self.binned_freq = True

    def binDataTime(self, width=DATA_POINTS_PER_SECOND / BIN_FACTOR, method='median'):
        if method != 'median' and method != 'mean':
            raise Exception
        time_min = self.spectrum_data.time_axis[0]
        time_max = self.spectrum_data.time_axis[-1]
        data = self.spectrum_data.data
        time_range = np.arange(time_min, time_max - width, width)

        entries_per_bin = len(self.spectrum_data.time_axis) / len(time_range)
        data_binned = [[] for i in range(len(data))]

        if method == 'median':
            for line in range(len(data)):
                for bin_ in range(len(time_range)):
                    data_binned[line].append(
                        np.nanmedian(data[line][int(bin_ * entries_per_bin):int((bin_ + 1) * entries_per_bin)]))
        if method == 'mean':
            for line in range(len(data)):
                for bin_ in range(len(time_range)):
                    data_binned[line].append(
                        np.nanmean(data[line][int(bin_ * entries_per_bin):int((bin_ + 1) * entries_per_bin)]))

        self.spectrum_data.data = np.array(data_binned)

        self.spectrum_data.time_axis = time_range
        self.binned_time = True
        self.binned_time_width = width
        self.number_values = len(self.spectrum_data.time_axis)

    def plot(self):
        """
        plots the file
        """
        self.spectrum_data.peek()

    def createSummedCurve(self, frequency_range: List):
        """
        creates summed up curve
        """
        freq_high = (np.where(self.spectrum_data.freq_axis == max(
            self.spectrum_data.freq_axis[self.spectrum_data.freq_axis <= frequency_range[1]])))[0][0]
        freq_low = (np.where(self.spectrum_data.freq_axis == min(
            self.spectrum_data.freq_axis[self.spectrum_data.freq_axis >= frequency_range[0]])))[0][0]

        self.summedCurve = [np.nansum(self.spectrum_data.data.transpose()[time][freq_high:freq_low + 1]) for time
                            in range(self.number_values)]

    def subtract_background(self):
        if self.background_subtracted:
            return
        self.spectrum_data = self.spectrum_data.subtract_bg()
        self.background_subtracted = True

    def flattenSummedCurve(self, rolling_window=CURVE_FLATTEN_WINDOW):
        median = np.array(pd.Series(self.summedCurve).rolling(rolling_window).median())
        arr = np.array(self.summedCurve)
        self.summedCurve = arr - median

    def plotSummedCurve(self):
        plotCurve(self.spectrum_data.time_axis, self.summedCurve, self.spectrum_data.start.timestamp(),
                  self.binned_time, self.binned_time_width)


def createDay(_year: int, _month: int, _day: int, _observatory: observatories.Observatory,
              _spectral_range: List[int]):
    """
    Creates a list with DataPoints for a specific day for a Observatory with a specific spectral range

    TODO: function the spectral_id = next() line

    :param _year:
    :param _month:
    :param _day:
    :param _observatory:
    :param _spectral_range: [spectral, range]
    :return: List[DataPoints]
    """
    path = const.pathDataDay(_year, _month, _day)
    files_day = sorted(os.listdir(path))
    spectral_id = observatories.specID(_observatory, _spectral_range)
    files_observatory = []
    data_day = []

    for file in files_day:
        if file.startswith(_observatory.name) and file.endswith(spectral_id + DataPoint.file_ending):
            files_observatory.append(file)

    for file in files_observatory:
        data_day.append(DataPoint(file))  # try except |error -> TRIEST_20210906_234530_57.fit   TODO
    return data_day


def createFromTime(_year, _month, _day, _time, _observatory, _spectral_range):
    path = const.pathDataDay(_year, _month, _day)
    files = sorted(os.listdir(path))
    spectral_id = observatories.specID(_observatory, _spectral_range)
    time_target = int(_time[:2])*3600 + int(_time[3:5])*60 + int(_time[6:])
    files_filtered = []

    for file in files:
        if file.startswith(_observatory.name) and file.endswith(spectral_id + DataPoint.file_ending):
            files_filtered.append(file)

    file_ = files_filtered[0]
    for file in files_filtered:
        time_read = file.rsplit('_')[2]
        time_file = int(time_read[:2])*3600 + int(time_read[2:4])*60 + int(time_read[4:])
        time_diff = time_target - time_file
        if time_diff < 0:
            break
        file_ = file

    return DataPoint(file_)


def fitTimeFrameDataSample(_data_point1: List[DataPoint], _data_point2: List[DataPoint]):
    """
    shortens the list of DataPoints of different timeframe to a single biggest possible timeframe

    TODO: where data is cut, and why

    TODO: throw - no overlap

    :param _data_point1: List[DataPoints]
    :param _data_point2: List[DataPoints]
    :return: DataPoint(timeframe), DataPoint(timeframe)
    """
    while _data_point1[0].hour + _data_point1[0].minute / 60 != _data_point2[0].hour + _data_point2[0].minute / 60:
        if _data_point1[0].hour + _data_point1[0].minute / 60 < _data_point2[0].hour + _data_point2[0].minute / 60:
            _data_point1.pop(0)
        else:
            _data_point2.pop(0)
    while _data_point1[-1].hour + _data_point1[-1].minute / 60 != _data_point2[-1].hour + _data_point2[-1].minute / 60:
        if _data_point1[-1].hour + _data_point1[-1].minute / 60 < _data_point2[-1].hour + _data_point2[-1].minute / 60:
            _data_point2.pop(-1)
        else:
            _data_point1.pop(-1)

    data_merged1 = sum(_data_point1)
    data_merged2 = sum(_data_point2)
    return data_merged1, data_merged2


def plotCurve(_time, _data, _time_start, _bin_time, _bin_time_width, _plot=True, file_name=None):
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
    plt.figure(figsize=(16, 9))
    plt.xticks(rotation=90)
    plt.plot(dataframe)

    if _plot:
        plt.show()
    else:
        plt.savefig(const.path_plots + file_name)
    plt.close()
