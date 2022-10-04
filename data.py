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
import stations
import download
import events

file_ending = const.file_ending
FREQ_MIN = 0
FREQ_MAX = 1
BIN_WIDTH_FREQUENCY = 2
DATA_POINTS_PER_SECOND = const.DATA_POINTS_PER_SECOND
BIN_FACTOR = const.BIN_FACTOR
CURVE_FLATTEN_WINDOW = 100


class DataPoint:
    """
    """

    def __init__(self, file: str):
        self.spectrum_data = None
        self.number_values = None
        self.summed_curve = []
        self.binned_freq = False
        self.binned_time = False
        self.binned_time_width = 1
        self.background_subtracted = False
        self.flattened = False
        self.flattened_window = 1

        reader = file.rsplit('/')[-1]
        self.file_name = reader
        reader = reader.rsplit('_')

        self.year = int(reader[1][:4])
        self.month = int(reader[1][4:6])
        self.day = int(reader[1][6:])
        self.hour = int(reader[2][:2])
        self.minute = int(reader[2][2:4])
        self.second = int(reader[2][4:])
        self.date = datetime(self.year, self.month, self.day, self.hour, self.minute, self.second)

        self.observatory = stations.getStationFromFile(const.pathDataDay(self.date) + file)
        self.spectral_range_id = reader[3][:2]
        self.path = const.pathDataDay(self.date)

        self.readFile()
        if not self:
            return
        self.cleanUpData()

    def __add__(self, other):
        """

        :param other:
        :return:
        """
        temp1 = copy.copy(self)
        temp2 = copy.copy(other)
        if temp1.spectrum_data is None:
            return temp2
        if temp2.spectrum_data is None:
            return temp1
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

    def __bool__(self):
        return bool(self.spectrum_data)

    def readFile(self):
        """
        reads data from file
        called by __init__
        """
        data_available, station = download.dataAvailable(self.date)
        if data_available:
            if self.observatory is not None and self.observatory.name not in station:
                download.downloadFullDay(self.date, station=[self.observatory.name])

        file = self.path + self.file_name

        if self.hour == 23 and self.minute > 30:
            self.spectrum_data = self.readFalseDateFile()
        else:
            try:
                self.spectrum_data = CallistoSpectrogram.read(file)
            except TypeError:
                self.spectrum_data = None
                return
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
            try:

                return CallistoSpectrogram.read(self.path + self.file_name)
            except TypeError:
                self.spectrum_data = None
                return None

        file_copy[0].header['DATE-END'] = date_end_proper_str
        file_copy[0].header['TIME-END'] = time_end_proper
        file_copy.writeto(self.path + self.file_name, overwrite=True)

        try:
            return CallistoSpectrogram.read(self.path + self.file_name)
        except TypeError:
            self.spectrum_data = None
            return None

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
        frequency_min = self.observatory.spectral_range[FREQ_MIN]
        frequency_max = self.observatory.spectral_range[FREQ_MAX]
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

    def plot(self):  # TODO if none - skip
        """
        plots the file
        """
        self.spectrum_data.peek()

    def createSummedCurve(self, frequency_range=None):
        """
        creates summed up curve
        """
        if frequency_range is None:
            frequency_range = [self.spectrum_data.freq_axis[-1], self.spectrum_data.freq_axis[0]]

        freq_high = (np.where(self.spectrum_data.freq_axis == max(
            self.spectrum_data.freq_axis[self.spectrum_data.freq_axis <= frequency_range[1]])))[0][0]
        freq_low = (np.where(self.spectrum_data.freq_axis == min(
            self.spectrum_data.freq_axis[self.spectrum_data.freq_axis >= frequency_range[0]])))[0][0]

        self.summed_curve = [np.nansum(self.spectrum_data.data.transpose()[time][freq_high:freq_low + 1]) for time
                             in range(self.number_values)]

    def subtract_background(self):
        if self.background_subtracted:
            return
        self.spectrum_data = self.spectrum_data.subtract_bg()
        self.background_subtracted = True

    def flattenSummedCurve(self, rolling_window=CURVE_FLATTEN_WINDOW):
        if self.number_values > 3 * const.LENGTH_FILES_MINUTES * 60 * const.DATA_POINTS_PER_SECOND:
            median = np.array(pd.Series(self.summed_curve).rolling(rolling_window).median())
            self.flattened_window = rolling_window
        else:
            median = np.nanmedian(self.summed_curve)
            self.flattened_window = 0
        arr = np.array(self.summed_curve)
        self.summed_curve = arr - median
        self.flattened = True

    def plotSummedCurve(self, ax, peaks=None, label=None, color=None):
        plotCurve(self.spectrum_data.time_axis, self.summed_curve, self.spectrum_data.start.timestamp(),
                  self.binned_time, self.binned_time_width, ax, peaks=peaks, new_ax=True, label=label, color=color)

    def fileName(self):
        return f"{self.year}_{self.month:02}_{self.day:02}_{self.observatory}" \
               f"{['', '_nobg'][self.background_subtracted]}" \
               f"{['', '_binfreq'][self.binned_freq]}" \
               f"{['', '_bintime_{}'.format(self.binned_time_width)][self.binned_time]}" \
               f"{['', '_flatten_{}'.format(self.flattened_window)][self.flattened]}.png"

    def dateTime(self):
        return datetime(year=self.year, month=self.month, day=self.day,
                        hour=self.hour, minute=self.minute, second=self.second)


def createDayList(*date, station: Union[stations.Station, str]) -> List[DataPoint]:
    """
    Creates a list with DataPoints for a specific day for a Observatory with a specific spectral range

    :param date: datetime or Ints for year, month, day
    :param station:
    :return: List[DataPoints]
    """
    date_ = const.getDateFromArgs(*date)

    if isinstance(station, str):
        focus_code = stations.getFocusCode(date_, station=station)
        station_name = station
    else:
        focus_code = station.focus_code
        station_name = station.name

    path = const.pathDataDay(date_)
    files_day = sorted(os.listdir(path))
    files_observatory = []
    data_day = []

    for file in files_day:
        if file.startswith(station_name) and file.endswith(focus_code + file_ending):
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
        except AttributeError:
            # data point
            pass
    data_day_return = [i for i in data_day if i]
    return data_day_return


def createDay(*date, station: Union[stations.Station, str]) -> DataPoint:
    return sum(createDayList(*date, station=station))


def createFromTime(*date, station: Union[stations.Station, str], extent=True) -> DataPoint:
    date_ = const.getDateFromArgs(*date)

    if isinstance(station, str):
        spectral_id = stations.getFocusCode(date_, station=station)
        station_name = station
    else:
        spectral_id = station.focus_code
        station_name = station.name

    path = const.pathDataDay(date_)
    files = sorted(os.listdir(path))
    time_target = date_.hour * 3600 + date_.minute * 60 + date_.second
    files_filtered = []
    for file in files:
        if file.startswith(station_name) and file.endswith(spectral_id + file_ending):
            files_filtered.append(file)
    for i, file in enumerate(files_filtered):
        time_read = file.rsplit('_')[2]
        hour = int(time_read[:2])
        minute = int(time_read[2:4])
        second = int(time_read[4:])
        time_file = hour * 3600 + minute * 60 + second
        time_diff = time_target - time_file

        if time_diff < 15 * 60:
            dp0 = DataPoint(file)
            dp = dp0
            if extent and i and ((date_.minute * 60 + date_.second) - (minute * 60 + second) < (5 * 60)):
                dp_ahead = DataPoint(files_filtered[i - 1])
                dp = dp_ahead + dp0
            if extent and i + 1 < len(files_filtered) and (((date_.minute * 60 + date_.second) - (minute * 60 + second)) > (10 * 60)):
                dp_after = DataPoint(files_filtered[i + 1])
                dp = dp0 + dp_after
            return dp
    raise FileNotFoundError("No file for the specified time and station found.")


def createFromEvent(event: events.Event, station=None):
    """
    TODO 
    """
    time_start = event.time_start
    time_end = event.time_end
    if station and station in event.stations:
        obs = station
    elif station and not event.stations:
        obs = station
    else:
        obs = event.stations[0]

    dp = createFromTime(time_start, station=obs)  # TODO this crashes -> whole thing as datetime, Events->datetime
    i = 1
    while dp.spectrum_data.end < time_end:
        new_time = time_start + timedelta(minutes=const.LENGTH_FILES_MINUTES * i)
        dp += createFromTime(new_time, station=obs)
        i += 1
    
    if (event.time_start - event.time_end).total_seconds() < 20:
        delta = 10
    else:
        delta = 0
    del_start = int((event.time_start - dp.spectrum_data.start - timedelta(seconds=delta)).total_seconds()
                    * const.DATA_POINTS_PER_SECOND)
    del_end = int((event.time_end - dp.spectrum_data.start + timedelta(seconds=delta)).total_seconds()
                  * const.DATA_POINTS_PER_SECOND)
    if del_start < 0:
        del_start = 0
    dp.spectrum_data.data = dp.spectrum_data.data[:, del_start:del_end]
    dp.spectrum_data.start = event.time_start
    
    return dp


def frqProfile(_list: List[DataPoint]):
    """
    most frequent freq id of a list of datapoints
    """
    fa = [i.spectrum_data.header["FRQFILE"] for i in _list]
    fsets = set(fa)
    count = [fa.count(i) for i in fsets]
    return list(fsets)[count.index(max(count))]


def cutFreqProfile(day: List[DataPoint], frq_profile):
    return [i for i in day if (i.spectrum_data and i.spectrum_data.header["FRQFILE"] == frq_profile)]


def cutDayBefore(day: List[DataPoint], hour_limit: datetime):
    return [i for i in day if (i.hour >= hour_limit.hour)]


def cutDayAfter(day: List[DataPoint], hour_limit: datetime):
    return [i for i in day if (i.hour <= hour_limit.hour)]


def listDataPointDay(*date, station: stations.Station):
    """

    """

    date_ = const.getDateFromArgs(*date)
    date_ = datetime(year=date_.year, month=date_.month, day=date_.day, hour=int(station.obsTime()))
    date_ahead = date_ - timedelta(days=1)
    date_behind = date_ + timedelta(days=1)
    midnight = date_ + timedelta(hours=12)

    download.downloadFullDay(date_, station=station)
    download.downloadFullDay(date_ahead, station=station)
    download.downloadFullDay(date_behind, station=station)

    day_list = createDayList(date_, station=station)
    date_ahead_list = createDayList(date_ahead, station=station)
    date_behind_list = createDayList(date_behind, station=station)

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


"""
"""

# TODO: obsolete?

"""
"""


def plotCurve(_time, _data, _time_start, _bin_time, _bin_time_width, axis, _plot=True, peaks=None, new_ax=False,
              label=None, color=None):
    plotCurve.curve += 1
    if _bin_time:
        data_per_second = DATA_POINTS_PER_SECOND / _bin_time_width                                  # TODO
    else:
        data_per_second = DATA_POINTS_PER_SECOND
    time_axis_plot = []
    for i in _time:
        time_axis_plot.append(
            datetime.fromtimestamp(_time_start + i).strftime("%Y %m %d %H:%M:%S"))
    time_axis_plot = pd.to_datetime(time_axis_plot)
    dataframe = pd.DataFrame()
    dataframe['data'] = _data
    
    if not color:
        color = const.getColor()
    
    if new_ax:
        ax = axis.twinx()
        ax.set_axis_off()
        ax.tick_params(axis='y')
        dataframe = dataframe.set_index(time_axis_plot)
        plt.xticks(rotation=90)

        curve = ax.plot(dataframe, color=color, linewidth=1, label=label)

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

        curve = plt.plot(dataframe, color=color, linewidth=1, label=label)

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
    return curve

plotCurve.curve = 0
