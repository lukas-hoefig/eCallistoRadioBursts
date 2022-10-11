#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from scipy.signal import find_peaks
import matplotlib.pylab as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import copy
import os
import pickle
from typing import Union

import const
import data
import correlation
import events
import stations

plot_size_x = 19
plot_size_y = 12
mask_frq_limit = 1.5

# TODO make plot() its own function - code duplication


def maskBadFrequencies(datapoint: Union[data.DataPoint, np.ndarray], limit=mask_frq_limit):
    if isinstance(datapoint, data.DataPoint):
        dpt = copy.deepcopy(datapoint)
        dpt.subtract_background()
        data_ = dpt.spectrum_data.data
    elif isinstance(datapoint, np.ndarray):
        data_ = datapoint
    else:
        raise ValueError
    if isinstance(data_, np.ma.masked_array):
        data_ = data_.data

    summed = np.array([np.nansum(data_[f]) for f in range(len(data_))])
    summed_lim = limit * np.nanstd(summed)
    summed_mean = np.nanmean(summed)

    mean_ = []
    for i in data_:
        mean_.append(np.nanstd(i))
    mean = np.nanmedian(mean_)

    mask = np.array([(abs(j - summed_mean) > summed_lim) or (mean_[i] > mean * 10) for i, j in enumerate(summed)])
    return mask


def maskBadFrequenciesPlot(datapoint: data.DataPoint, limit=mask_frq_limit):
    data_ = datapoint.spectrum_data.data
    frq = datapoint.spectrum_data.freq_axis
    summed = np.array([np.nansum(f) for f in data_])
    summed_max = np.nanmax(summed)
    summed_min = np.nanmin(summed)

    mask = maskBadFrequencies(datapoint, limit=limit)
    summed_masked = copy.copy(summed)
    summed_masked[mask] = np.nanmean(summed)

    fig, ax = plt.subplots(figsize=(plot_size_x, plot_size_y))
    plt.imshow(datapoint.spectrum_data.data, extent=[summed_min, summed_max, frq[0], frq[-1]],
               aspect='auto', origin='lower')
    ax.set_ylim(frq[0], frq[-1])
    ax.set_xlim([np.nanmin(summed), np.nanmax(summed)])

    plt.xlabel("Intensity [arbitrary units]")
    plt.ylabel("frequency [MHz]")

    ax.plot(summed, frq, color='red', label="Dropped Frequency Regime")
    ax.plot(summed_masked, frq, color='orange', label="Summed Intensity")

    ax.legend(loc="lower left")
    plt.show()

    return mask


def calcPoint(*date, obs1: stations.Station, obs2: stations.Station, data_point_1=None, data_point_2=None,
              mask_frq=False, limit_frq=mask_frq_limit, extent=True, limit=correlation.CORRELATION_MIN,
              flatten=None, bin_time=None, bin_freq=None, no_bg=None, r_window=None,
              flatten_window=None, bin_time_width=None, method_bin_t=None, method_bin_f=None):
    """
    TODO -> corrupt data -> skip 
    """
    if flatten is None:
        flatten = True
    if flatten_window is None:
        flatten_window = correlation.default_flatten_window
    if bin_time is None:
        bin_time = True
    if bin_freq is None:
        bin_freq = False
    if no_bg is None:
        no_bg = True
    if r_window is None:
        r_window = int(correlation.default_r_window/correlation.default_time_window)
    if bin_time_width is None:
        bin_time_width = correlation.default_time_window
    if method_bin_t is None:
        method_bin_t = 'median'
    if method_bin_f is None:
        method_bin_f = 'median'

    if data_point_1 is None and data_point_2 is None:
        date_ = const.getDateFromArgs(*date)
        data_point_1 = data.createFromTime(date_, station=obs1, extent=extent)
        data_point_2 = data.createFromTime(date_, station=obs2, extent=extent)
    else:
        date_ = data_point_1.spectrum_data.start

    if mask_frq:
        mask1 = maskBadFrequencies(data_point_1, limit=limit_frq)
        mask2 = maskBadFrequencies(data_point_2, limit=limit_frq)
        data_point_1.spectrum_data.data[mask1, :] = np.nanmean(data_point_1.spectrum_data.data)

        data_point_2.spectrum_data.data[mask2, :] = np.nanmean(data_point_2.spectrum_data.data)
    else:
        pass

    dp1_cor = copy.deepcopy(data_point_1)
    dp2_cor = copy.deepcopy(data_point_2)

    cor = correlation.Correlation(dp1_cor, dp2_cor, day=date_.day,
                                  flatten=flatten, bin_time=bin_time, bin_freq=bin_freq, no_background=no_bg,
                                  r_window=r_window, flatten_window=flatten_window, bin_time_width=bin_time_width,
                                  method_bin_t=method_bin_t, method_bin_f=method_bin_f)
    cor.calculatePeaks(limit=limit)

    data_point_1.createSummedCurve()
    data_point_2.createSummedCurve()
    data_point_1.flattenSummedCurve(rolling_window=correlation.default_flatten_window)
    data_point_2.flattenSummedCurve(rolling_window=correlation.default_flatten_window)
    return data_point_1, data_point_2, cor


def plotDatapoint(datapoint: data.DataPoint):
    t = np.arange(datapoint.spectrum_data.start.strftime("%Y-%m-%dT%H:%M:%S.%z"),
                  datapoint.spectrum_data.end.strftime("%Y-%m-%dT%H:%M:%S.%z"), dtype='datetime64[s]').astype(datetime)
    mt = mdates.date2num((t[0], t[-1]))

    fig, ax = plt.subplots(figsize=(plot_size_x, plot_size_y))
    fig.suptitle(f"{datapoint.day}.{datapoint.month}.{datapoint.year} Radio Flux Data {datapoint.observatory.name}")
    ax.set_xlabel("Time")
    ax.set_ylabel("Frequency [MHz]")
    plt.imshow(datapoint.spectrum_data.data, extent=[mt[0], mt[1], 0, int(900 / plot_size_x * plot_size_y)],
               aspect='auto', origin='lower')
    cbar = plt.colorbar(location='right', anchor=(.15, 0.0))
    cbar.set_label("Intensity")
    ax.set_yticks([int(900 / plot_size_x * plot_size_y / 9) * i for i in range(0, 10)],
                  np.around(datapoint.spectrum_data.freq_axis[::int(len(datapoint.spectrum_data.freq_axis) / 9)], 1))
    ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.xticks(rotation=45)

    plt.tight_layout()
    plt.show()


def plotEverything(dp1: data.DataPoint, dp2: data.DataPoint, cor: correlation.Correlation):
    if cor.day == dp1.day:
        year = dp1.year
        month = dp1.month
        day = cor.day
    else:
        date = datetime(dp1.year, dp1.month, dp1.day) + timedelta(days=1)
        year = date.year
        month = date.month
        day = date.day

    if len(cor.data_curve) < len(dp1.spectrum_data.time_axis[::4]):
        _time = dp1.spectrum_data.time_axis[::4][:len(cor.data_curve)]
    else:
        _time = dp1.spectrum_data.time_axis[::4]
    _time2 = dp1.spectrum_data.time_axis
    _time3 = dp2.spectrum_data.time_axis
    _time_start = cor.time_start
    _data = cor.data_curve
    unscientific_shift = 0   # 45/4

    t = np.arange(dp1.spectrum_data.start.strftime("%Y-%m-%dT%H:%M:%S.%z"),
                  dp1.spectrum_data.end.strftime("%Y-%m-%dT%H:%M:%S.%z"), dtype='datetime64[s]').astype(datetime)
    mt = mdates.date2num((t[0], t[-1]))

    fig, ax = plt.subplots(figsize=(plot_size_x, plot_size_y))
    fig.suptitle(f"{day}.{month}.{year} Radio Flux Data "
                 f"{dp1.observatory.name} and overlap with {cor.data_point_2.observatory.name}")
    ax.set_xlabel("Time")
    ax.set_ylabel("Frequency [MHz]")
    plt.imshow(dp1.spectrum_data.data, extent=[mt[0], mt[1], 0, int(900/plot_size_x * plot_size_y)],
               aspect='auto', origin='lower')
    cbar = plt.colorbar(location='right', anchor=(.15, 0.0))
    cbar.set_label("Intensity")
    ax.set_yticks([int(900/plot_size_x * plot_size_y/9) * i for i in range(0, 10)],
                  np.around(dp1.spectrum_data.freq_axis[::int(len(dp1.spectrum_data.freq_axis)/9)], 1))
    ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.xticks(rotation=60)

    ax2 = plt.twinx(ax)
    plot_limit = ax2.axhline(0.8, color="yellow", linestyle='--', label='Correlation Limit')
    time_axis_plot = []
    for i in _time:
        time_axis_plot.append(datetime.fromtimestamp(_time_start + i).strftime("%Y %m %d %H:%M:%S"))
    time_axis_plot = pd.to_datetime(time_axis_plot)
    dataframe = pd.DataFrame()
    dataframe['data'] = _data
    dataframe = dataframe.set_index(time_axis_plot)
    plot_cor = ax2.plot(dataframe, color="red", linewidth=2,
                        label=f"Correlation: {cor.data_point_1.observatory.name} | {cor.data_point_2.observatory.name}")
    ax2.set_ylabel("Correlation")
    ax2.set_ylim(-0.4, 1)

    ax3 = plt.twinx(ax)
    # ax3.spines["right"].set_position(("axes", 1.2))
    # ax3.yaxis.get_offset_text().set_position((1.2,1))
    # ax3.set_ylabel("data")
    ax3.set_axis_off()
    time_axis_plot2 = []
    for i in _time2:
        time_axis_plot2.append(datetime.fromtimestamp(_time_start + i).strftime("%Y %m %d %H:%M:%S"))
    time_axis_plot2 = pd.to_datetime(time_axis_plot2)
    dataframe2 = pd.DataFrame()
    dataframe2['data'] = dp1.summed_curve
    dataframe2 = dataframe2.set_index(time_axis_plot2)
    plot_dat = ax3.plot(dataframe2, color="blue", linewidth=1, label=f"Summed Intensity Curve {dp1.observatory.name}")

    ax4 = plt.twinx(ax)
    ax4.set_axis_off()
    time_axis_plot3 = []
    for i in _time3:
        time_axis_plot3.append(datetime.fromtimestamp(_time_start + i).strftime("%Y %m %d %H:%M:%S"))
    time_axis_plot3 = pd.to_datetime(time_axis_plot3)
    dataframe3 = pd.DataFrame()
    dataframe3['data'] = dp2.summed_curve
    dataframe3 = dataframe3.set_index(time_axis_plot3)
    plot_dat2 = ax4.plot(dataframe3, color="cyan", linewidth=1, label=f"Summed Intensity Curve {dp2.observatory.name}")

    plots = plot_cor + plot_dat + plot_dat2
    plots.append(plot_limit)

    _peaks_start = []
    _peaks_end = []
    for j, i in enumerate(cor.peaks):
        start = mdates.date2num(i.time_start-timedelta(seconds=unscientific_shift))
        end = mdates.date2num(i.time_end-timedelta(seconds=unscientific_shift))
        _peaks_start.append(start)
        _peaks_end.append(end)

        plot_b_start = plt.axvline(start, color="darkgrey", linestyle='--', label='Burst start')
        plot_b_end = plt.axvline(end, color="black", linestyle='--', label='Burst end')

        if not j:
            plots.extend([plot_b_start, plot_b_end])

    labs = [i.get_label() for i in plots]
    plt.legend(plots, labs, loc="lower right")     # -> TODO position
    plt.tight_layout()
    plt.show()


def peaksInData(dp1: data.DataPoint, dp2: data.DataPoint, plot=False, peak_limit=2):
    """

    """
    x1 = np.array(dp1.summed_curve)
    lim1 = peak_limit * np.nanstd(x1)
    scipy_peaks1 = find_peaks(x1, height=lim1)[0]

    x2 = np.array(dp2.summed_curve)
    lim2 = peak_limit * np.nanstd(x2)
    scipy_peaks2 = find_peaks(x2, height=lim2)[0]

    _time_start = dp1.spectrum_data.start.timestamp()

    new3 = []
    peaks = []
    if len(scipy_peaks1) and len(scipy_peaks2):
        new = [scipy_peaks1[0]]
        for kk in scipy_peaks1:
            if all(np.around(kk - new, -2)):
                new.append(kk)

        new2 = [scipy_peaks2[0]]
        for kk in scipy_peaks2:
            if all(np.around(kk - new2, -2)):
                new2.append(kk)
        for kk in new:
            if not all(np.around(kk - new2, -2)):
                new3.append(kk)
        for i in new3:
            peak = datetime.fromtimestamp(_time_start + i / 4)
            event = events.Event(peak, probability=correlation.CORRELATION_MIN)
            peaks.append(event)
    events_ = events.EventList(peaks, dp1.spectrum_data.start)

    if plot:
        _time1_ = dp1.spectrum_data.time_axis
        _time2_ = dp2.spectrum_data.time_axis
        fig, ax = plt.subplots(figsize=(plot_size_x, plot_size_y))
        plt.xlabel("Time")
        plt.ylabel("Summed Intensity")

        time_axis_plot1 = []
        for i in _time1_:
            time_axis_plot1.append(datetime.fromtimestamp(_time_start + i).strftime("%Y %m %d %H:%M:%S"))
        time_axis_plot1 = pd.to_datetime(time_axis_plot1)
        dataframe1 = pd.DataFrame()
        dataframe1['data'] = dp1.summed_curve
        dataframe1 = dataframe1.set_index(time_axis_plot1)
        plt.plot(dataframe1, color="red", linewidth=2, label=f"{dp1.observatory}")
        for i in scipy_peaks1:
            plt.plot(mdates.date2num(datetime.fromtimestamp(_time_start + i / 4)), x1[i], "x", color="red")

        time_axis_plot2 = []
        for i in _time2_:
            time_axis_plot2.append(datetime.fromtimestamp(_time_start + i).strftime("%Y %m %d %H:%M:%S"))
        time_axis_plot2 = pd.to_datetime(time_axis_plot2)
        dataframe2 = pd.DataFrame()
        dataframe2['data'] = dp2.summed_curve
        dataframe2 = dataframe2.set_index(time_axis_plot2)
        plt.plot(dataframe2, color="blue", linewidth=1, label=f"{dp2.observatory}")
        for i in scipy_peaks2:
            plt.plot(mdates.date2num(datetime.fromtimestamp(_time_start + i / 4)), x2[i], "x", color="blue")

        for i in new3:
            if not new3.index(i):
                plt.axvline(mdates.date2num(datetime.fromtimestamp(_time_start + i / 4)), linestyle="--", color="grey",
                            label="Possible Peak")
            else:
                plt.axvline(mdates.date2num(datetime.fromtimestamp(_time_start + i / 4)), linestyle="--", color="grey")

        ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=2))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        plt.xlim([mdates.date2num(time_axis_plot1[0]), mdates.date2num(time_axis_plot1[-1])])
        plt.xticks(rotation=45)
        plt.legend(loc="upper left")
        plt.show()

    return events_


def getEvents(*args, mask_frq=None, r_window=None,
              flatten=None, bin_time=None, bin_freq=None, no_bg=None,
              flatten_window=None, bin_time_width=None, limit=None):
    date = None
    dp1 = None
    dp2 = None
    obs1 = None
    obs2 = None
    for i in args:
        if isinstance(i, data.DataPoint) and dp1 is None:
            dp1 = i
            obs1 = i.observatory
            continue
        if isinstance(i, data.DataPoint) and dp1 is not None:
            dp2 = i
            obs2 = i.observatory
            continue
        if isinstance(i, datetime) and date is None:
            date = i
            continue
        if isinstance(i, str) or isinstance(i, stations.Station):
            obs1 = i
            continue
        if (isinstance(i, str) or isinstance(i, stations.Station)) and obs1 is not None:
            obs2 = i
            continue
    if dp1 is not None and dp2 is not None:
        date = dp1.spectrum_data.start

    if date is None or obs2 is None:
        raise ValueError("Needs either datetime and 2 stations   or   2 datapoints as args")

    e_list = events.EventList([], date)
    dp1, dp2, cor = calcPoint(date, obs1=obs1, obs2=obs2, data_point_1=dp1, data_point_2=dp2,
                              mask_frq=mask_frq, r_window=r_window,
                              flatten=flatten, bin_time=bin_time, bin_freq=bin_freq, no_bg=no_bg,
                              flatten_window=flatten_window, bin_time_width=bin_time_width, limit=limit)

    event_peaks = peaksInData(dp1, dp2)
    for peak in cor.peaks:
        if peak.inList(event_peaks):
            e_list += peak
    return e_list


def filename(*date, step: int):
    date_ = const.getDateFromArgs(*date)
    return const.path_data + f"results/{date_.year}/{date_.month:02}/" + \
                             f"{date_.year}_{date_.month:02}_{date_.day:02}_step{step}"


def saveData(*date, step: int, event_list: events.EventList):
    """
    """
    date_ = const.getDateFromArgs(*date)
    file_name = filename(date_, step=step)
    folder = file_name[:file_name.rfind("/")+1]
    if not (os.path.exists(folder) and os.path.isdir(folder)):
        os.makedirs(folder)
    with open(filename(date_, step=step), "wb") as file:
        pickle.dump(event_list, file)


def loadData(*date, step: int):
    """
    """
    date_ = const.getDateFromArgs(*date)
    with open(filename(date_, step=step), "rb") as read_file:
        loaded_data = pickle.load(read_file)

    return loaded_data
