#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from radiospectra.sources.callisto import CallistoSpectrogram
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import copy
from datetime import datetime, timedelta
import os
from astropy.io import fits
from typing import List, Union

import const
import observatories
import download

path_script = const.path_script
path_data = const.path_data
file_ending = ".fit.gz"
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

    def __init__(self, file: str):
        self.spectrum_data = None
        self.number_values = None
        self.summedCurve = []
        self.binned_freq = False
        self.binned_time = False
        self.binned_time_width = 1
        self.background_subtracted = False
        self.flattened = False
        self.flattened_window = 1

        reader = file.rsplit('/')[-1]
        self.file_name = reader
        reader = reader.rsplit('_')

        self.observatory = observatories.getObservatory(reader[0])
        self.year = int(reader[1][:4])
        self.month = int(reader[1][4:6])
        self.day = int(reader[1][6:])
        self.hour = int(reader[2][:2])
        self.minute = int(reader[2][2:4])
        self.second = int(reader[2][4:])

        self.spectral_range_id = reader[3][:2]
        self.spectral_range = self.observatory.getSpectralRange(self.spectral_range_id)
        if self.spectral_range is None:
            raise ValueError("File has unknown/invalid Value for Spectral Range ID / FocusCode")

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

        file = self.path + self.file_name

        if self.hour == 23 and self.minute > 30:
            self.spectrum_data = self.readFalseDateFile()
        else:
            self.spectrum_data = CallistoSpectrogram.read(file)

        self.number_values = len(self.spectrum_data.time_axis)

    def readFalseDateFile(self):
        file_open = fits.open(self.path + self.file_name)
        file_copy = copy.deepcopy(file_open)
        file_open.close()
        date_end = file_open[0].header['DATE-END']
        time_end = file_open[0].header['TIME-END']
        if int(time_end[:2]) == 24:
            time_end_proper = '00' + time_end[2:]
            date_end_proper = datetime(int(date_end[:4]), int(date_end[5:7]), int(date_end[8:10]))
            date_end_proper = date_end_proper + timedelta(days=1)
            date_end_proper_str = date_end_proper.strftime("%Y/%m/%d")
        else:
            return CallistoSpectrogram.read(self.path + self.file_name)

        file_copy[0].header['DATE-END'] = date_end_proper_str
        file_copy[0].header['TIME-END'] = time_end_proper
        file_copy.writeto(self.path + self.file_name, overwrite=True)
        return CallistoSpectrogram.read(self.path + self.file_name)

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

    def binDataTime(self, width=BIN_FACTOR, method='median'):
        if method != 'median' and method != 'mean':
            raise Exception
        time_min = self.spectrum_data.time_axis[0]
        time_max = self.spectrum_data.time_axis[-1]
        data = self.spectrum_data.data
        time_range = np.arange(time_min, time_max, width / DATA_POINTS_PER_SECOND)

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
        self.flattened = True
        self.flattened_window = rolling_window

    def plotSummedCurve(self, ax, peaks=None):
        plotCurve(self.spectrum_data.time_axis, self.summedCurve, self.spectrum_data.start.timestamp(),
                  self.binned_time, self.binned_time_width, ax, peaks=peaks, new_ax=True)

    def fileName(self):
        return "{}_{}_{}_{}{}{}{}{}.png"\
            .format(self.year, self.month, self.day, self.observatory,
                    ["", "_nobg"][self.background_subtracted], ["", "_binfreq"][self.binned_freq],
                    ["", "_bintime_{}".format(self.binned_time_width)][self.binned_time],
                    ["", "_flatten_{}".format(self.flattened_window)][self.flattened])

    def dateTime(self):
        return datetime(year=self.year, month=self.month, day=self.day,
                        hour=self.hour, minute=self.minute, second=self.second)


def getSpectralID(_year, _month, _day, _observatory, _spectral_range) -> str:
    spec_ids = observatories.specIDs(_observatory, _spectral_range)

    path = const.pathDataDay(_year, _month, _day)
    files = os.listdir(path)
    for i in spec_ids:
        if any(file.startswith(_observatory.name) and file.endswith(i + file_ending) for file in files):
            return i
    raise ValueError("no valid ID found")


def createDay(_year: int, _month: int, _day: int, _observatory: observatories.Observatory,
              _spectral_range: Union[str, List[int]]) -> List[DataPoint]:
    """
    Creates a list with DataPoints for a specific day for a Observatory with a specific spectral range

    :param _year:
    :param _month:
    :param _day:
    :param _observatory:
    :param _spectral_range: [spectral, range]
    :return: List[DataPoints]
    """
    if isinstance(_spectral_range, str):
        spectral_id = _spectral_range
    else:
        try:
            spectral_id = getSpectralID(_year, _month, _day, _observatory, _spectral_range)
        except ValueError:
            return []
    path = const.pathDataDay(_year, _month, _day)
    files_day = sorted(os.listdir(path))
    files_observatory = []
    data_day = []

    for file in files_day:
        if file.startswith(_observatory.name) and file.endswith(spectral_id + file_ending):
            files_observatory.append(file)

    for file in files_observatory:
        try:
            data_day.append(DataPoint(file))
        except TypeError:
            # corrupt file
            pass
        except ValueError:
            # invalid spectral range id
            pass
    return data_day


def createFromTime(_year, _month, _day, _time, _observatory, _spectral_range: Union[str, List[int]]):
    if isinstance(_spectral_range, str):
        spectral_id = _spectral_range
    else:
        spectral_id = getSpectralID(_year, _month, _day, _observatory, _spectral_range)

    path = const.pathDataDay(_year, _month, _day)
    files = sorted(os.listdir(path))
    time_target = int(_time[:2])*3600 + int(_time[3:5])*60 + int(_time[6:])
    files_filtered = []

    for file in files:
        if file.startswith(_observatory.name) and file.endswith(spectral_id + file_ending):
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


def frqProfile(_list: List[DataPoint]):
    """
    most frequent freq id of a list of datapoints
    """
    fa = [i.spectrum_data.header["FRQFILE"] for i in _list]
    fsets = set(fa)
    count = [fa.count(i) for i in fsets]
    return list(fsets)[count.index(max(count))]


def cutFreqProfile(day: List[DataPoint], frq_profile):
    return [i for i in day if (i.spectrum_data.header["FRQFILE"] == frq_profile)]


def cutDayBefore(day: List[DataPoint], hour_limit: datetime):
    return [i for i in day if (i.hour >= hour_limit.hour)]


def cutDayAfter(day: List[DataPoint], hour_limit: datetime):
    return [i for i in day if (i.hour <= hour_limit.hour)]


def listDataPointDay(year, month, day, observatory: observatories.Observatory, spectral_range):
    date = datetime(year=year, month=month, day=day, hour=int(observatory.obsTime()))
    date_ahead = date - timedelta(days=1)
    date_behind = date + timedelta(days=1)
    midnight = date + timedelta(hours=12)

    download.downloadFullDay(date.year, date.month, date.day, [observatory])
    download.downloadFullDay(date_ahead.year, date_ahead.month, date_ahead.day, [observatory])
    download.downloadFullDay(date_behind.year, date_behind.month, date_behind.day, [observatory])

    day_list = createDay(date.year, date.month, date.day, observatory, spectral_range)
    date_ahead_list = createDay(date_ahead.year, date_ahead.month, date_ahead.day, observatory, spectral_range)
    date_behind_list = createDay(date_behind.year, date_behind.month, date_behind.day, observatory, spectral_range)

    date_ahead_relevant = cutDayBefore(date_ahead_list, midnight)
    date_behind_relevant = cutDayAfter(date_behind_list, midnight)

    if date_ahead_relevant and date_behind_relevant:
        date_ahead_relevant.extend(cutDayAfter(day_list, midnight))
        day_list = cutDayBefore(day_list, midnight)
        day_list.extend(date_behind_relevant)

        frq_profile_1st = frqProfile(date_ahead_list)
        frq_profile_2nd = frqProfile(day_list)
        date_ahead_relevant = cutFreqProfile(date_ahead_relevant, frq_profile_1st)
        day_list = cutFreqProfile(day_list, frq_profile_2nd)

        date_ahead_relevant = date_ahead_relevant
        return [date_ahead_relevant, day_list]

    if not day_list:
        return []

    frq_profile = frqProfile(day_list)
    day_list = cutFreqProfile(day_list, frq_profile)
    return [day_list]


def fitTimeFrameDataSample(_data_point1, _data_point2):
    """
    shortens the list of DataPoints of different timeframe to a single biggest possible timeframe

    TODO: where data is cut, and why

    :param _data_point1: List[DataPoints]
    :param _data_point2: List[DataPoints]
    :return: DataPoint(timeframe), DataPoint(timeframe)
    """
    try:
        while abs((_data_point1[0].dateTime() - _data_point2[0].dateTime()).total_seconds()) >=\
                timedelta(minutes=15).total_seconds():
            if (_data_point1[0].dateTime() - _data_point2[0].dateTime()).total_seconds() < 0:
                _data_point1.pop(0)
            else:
                _data_point2.pop(0)
        while abs((_data_point1[-1].dateTime() - _data_point2[-1].dateTime()).total_seconds()) >= \
                timedelta(minutes=15).total_seconds():
            if (_data_point1[-1].dateTime() - _data_point2[-1].dateTime()).total_seconds() > 0:
                _data_point1.pop(-1)
            else:
                _data_point2.pop(-1)
    except IndexError:
        return [], []
    data_merged1 = sum(_data_point1)
    data_merged2 = sum(_data_point2)
    return data_merged1, data_merged2


def plotCurve(_time, _data, _time_start, _bin_time, _bin_time_width, axis, _plot=True, peaks=None, new_ax=False):
    plotCurve.curve += 1
    if _bin_time:
        data_per_second = DATA_POINTS_PER_SECOND / _bin_time_width
    else:
        data_per_second = DATA_POINTS_PER_SECOND
    time_axis_plot = []
    for i in _time:
        time_axis_plot.append(
            datetime.fromtimestamp(_time_start + i).strftime("%Y %m %d %H:%M:%S"))
    time_axis_plot = pd.to_datetime(time_axis_plot)
    dataframe = pd.DataFrame()
    dataframe['data'] = _data

    if new_ax:
        ax = axis.twinx()
        ax.set_axis_off()
        ax.tick_params(axis='y')
        dataframe = dataframe.set_index(time_axis_plot)
        plt.xticks(rotation=90)
        ax.plot(dataframe, color=const.getColor(), linewidth=1)

        if peaks:
            if type(peaks) == str:
                peaks = [peaks]
            for i in peaks:
                ax.axvline(pd.to_datetime(
                    datetime.strptime(datetime.fromtimestamp(_time_start).strftime("%Y %m %d ") + i,
                                      "%Y %m %d %H:%M:%S")), linestyle='--')
    else:
        dataframe = dataframe.set_index(time_axis_plot)
        plt.xticks(rotation=90)
        plt.plot(dataframe, color=const.getColor(), linewidth=1)

        if peaks:
            if type(peaks) == str:
                peaks = [peaks]
            for i in peaks:
                plt.axvline(pd.to_datetime(
                    datetime.strptime(datetime.fromtimestamp(_time_start).strftime("%Y %m %d ") + i,
                                      "%Y %m %d %H:%M:%S")), linestyle='--')
    # functions this maybe
    # if _plot:
    #     plt.show()
    # else:
    #     plt.savefig(const.path_plots + file_name)
    # plt.close()


plotCurve.curve = 0
