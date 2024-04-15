#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
 -  ROBUST  -
 - analysis.py -

Contains most top level functions to directly calculate SRBs, create Plots, save/load data in ROBUST file format
"""

from datetime import datetime, timedelta
from scipy.signal import find_peaks
import matplotlib.pylab as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import copy
import os
import pickle
from typing import Union, Tuple

import config
import data
import correlation
import events
import stations

plot_size_x = 19
plot_size_y = 12
mask_frq_limit = 1.1

# TODO make plot() its own function - code duplication


# TODO def applyMaskBadFrequency(): return masked data
def maskBadFrequencies(datapoint: Union[data.DataPoint, np.ndarray], limit: float = mask_frq_limit) -> np.array([bool]):
    """
    dynamic frequency filter to filter frequencies with irregular noise
    only works for small time-frames - low values of limit max filter signal, high values may ignore everything

    :param datapoint: Input data
    :param limit: *stddev() | values for frequencies above/below that limit get discarded,
                  values also get discarded if >10*mean(stddev(frq_i))
    :return: np.array[bool] mask array what frequencies to keep
    """
    if isinstance(datapoint, data.DataPoint):
        dpt = copy.deepcopy(datapoint)
        dpt.subtractBackground()
        data_ = dpt.spectrum_data.data
    elif isinstance(datapoint, np.ndarray):
        data_ = datapoint
    else:
        raise ValueError
    if isinstance(data_, np.ma.masked_array):
        data_ = data_.data

    summed = np.array([np.nansum(f) for f in data_])
    summed_lim = limit * np.nanstd(summed)
    summed_mean = np.nanmean(summed)

    mean_ = []
    for i in data_:
        mean_.append(np.nanstd(i))
    mean = np.nanmedian(mean_)

    mask = np.array([(abs(j - summed_mean) > summed_lim)
                    or (mean_[i] > mean * 10) for i, j in enumerate(summed)])
    return mask


def maskBadFrequenciesPlot(datapoint: data.DataPoint, limit: float = mask_frq_limit, save_img: bool = False) \
        -> np.array([bool]):
    """
    same as maskBadFrequencies(), but also plots the spectrogram. it also saves the image into the current folder with
    an appropriate name.

    :param datapoint: Input data
    :param limit: *stddev() | values for frequencies above/below that limit get discarded,
                  values also get discarded if >10*mean(stddev(frq_i))
    :param save_img:
    :return: np.array[bool] mask array what frequencies to keep
    """
    data_ = datapoint.spectrum_data.data
    frq = datapoint.spectrum_data.freq_axis
    summed = np.array([np.nansum(f) for f in data_])
    summed_max = np.nanmax(summed)
    summed_min = np.nanmin(summed)

    mask = maskBadFrequencies(datapoint, limit=limit)
    summed_masked = copy.copy(summed)
    summed_masked[mask] = np.nanmean(summed)

    fig, ax = plt.subplots(figsize=(plot_size_x, plot_size_y))

    plt.imshow(data_, extent=[summed_min, summed_max, frq[0], frq[-1]],
               aspect='auto', origin='lower')
    ax.set_ylim(frq[0], frq[-1])
    ax.set_xlim([np.nanmin(summed), np.nanmax(summed)])

    plt.xlabel("Intensity [arbitrary units]")
    plt.ylabel("Frequency [MHz]")

    ax.plot(summed, frq, color='red', label="Dropped Frequency Regime")
    ax.plot(summed_masked, frq, color='orange', label="Summed Intensity")

    ax.legend(loc="best")
    plt.tight_layout()
    if save_img:
        plt.savefig(f"frq_masking_{datapoint.observatory}_{datapoint.date.year}_{datapoint.date.month:02}_"
                    f"{datapoint.date.day:02}_{datapoint.date.hour:02}_{datapoint.date.minute:02}.png",
                    transparent=True)
    plt.show()

    ####

    data_masked = copy.copy(data_)
    data_masked[mask, :] = np.nanmedian(data_)
    fig, ax = plt.subplots(figsize=(plot_size_x, plot_size_y))

    plt.imshow(data_masked, extent=[summed_min, summed_max, frq[0], frq[-1]],
               aspect='auto', origin='lower')
    ax.set_ylim(frq[0], frq[-1])
    ax.set_xlim([np.nanmin(summed), np.nanmax(summed)])

    plt.xlabel("Intensity [arbitrary units]")
    plt.ylabel("Frequency [MHz]")

    ax.plot(summed, frq, color='red', label="Dropped Frequency Regime")
    ax.plot(summed_masked, frq, color='orange', label="Summed Intensity")

    ax.legend(loc="best")
    plt.tight_layout()
    if save_img:
        plt.savefig(f"frq_masking_{datapoint.observatory}_{datapoint.date.year}_{datapoint.date.month:02}_"
                    f"{datapoint.date.day:02}_{datapoint.date.hour:02}_{datapoint.date.minute:02}_masked.png",
                    transparent=True)

    return mask


def calcPoint(*date: Union[int, datetime], obs1: Union[stations.Station, str], obs2: Union[stations.Station, str],
              data_point_1: data.DataPoint = None, data_point_2: data.DataPoint = None,
              mask_frq: bool or None = None, limit_frq: bool = mask_frq_limit, extent: bool = True,
              limit: float or None = None, flatten: float or None = None, bin_time: float = None,
              bin_freq: bool = None, no_bg: bool = None, r_window: int = None, flatten_window: int = None,
              bin_time_width: int = None, method_bin_t: str = None, method_bin_f: str = None) \
        -> Tuple[data.DataPoint, data.DataPoint, correlation.Correlation] or None:
    """
    Calculates via correlation method whether there are possible bursts in two spectra.

    Spectra are either:

    option1: given directly via data_point_1|data_point_2

    option2: date and 2 stations are specified

    :param data_point_1: option1: datapoint 1 to be compared
    :param data_point_2: option1: datapoint 1 to be compared
    :param date: option2: Datetime or (3+) Ints to create DateTime (year, month, day)
    :param obs1: option2: Station to create datapoint, if datapoint is not set
    :param obs2: option2: Station to create datapoint, if datapoint is not set
    :param mask_frq: toggle dynamic frequency filter
    :param limit_frq: float - set limit for maskBadFrequencies
    :param extent: for option2: allows createFromTime() to load previous/subsequent file if date is close to file edge
    :param limit: min correlation required to recognise burst
    :param flatten: toggle median subtraction
    :param flatten_window: if 'flatten': rolling window size
    :param bin_time: toggle time binning
    :param bin_time_width: #points to be merged into new point
    :param bin_freq: toggle frequency binning
    :param no_bg: toggle background subtraction
    :param r_window: rolling window correlation method
    :param method_bin_t: str - toggle between mean and median
    :param method_bin_f: str - toggle between mean and median
    :return: datapoint 1, datapoint 2, correlation | None if either DataPoint can't be loaded
    """
    if limit is None:
        limit = correlation.CORRELATION_MIN
    if flatten is None:
        flatten = True
    if flatten_window is None:
        flatten_window = correlation.default_flatten_window
    if bin_time is None:
        bin_time = True
    if bin_freq is None:
        bin_freq = False
    if mask_frq is None:
        mask_frq = False
    if no_bg is None:
        no_bg = True
    if bin_time_width is None:
        bin_time_width = correlation.default_time_window
    if r_window is None:
        r_window = int(correlation.default_r_window / bin_time_width)
    if method_bin_t is None:
        method_bin_t = 'median'
    if method_bin_f is None:
        method_bin_f = 'median'

    if data_point_1 is None and data_point_2 is None:
        date_ = config.getDateFromArgs(*date)
        data_point_1 = data.createFromTime(date_, station=obs1, extent=extent)
        data_point_2 = data.createFromTime(date_, station=obs2, extent=extent)
    else:
        date_ = data_point_1.spectrum_data.start

    if data_point_1.spectrum_data is None or data_point_2.spectrum_data is None:
        return

    if mask_frq:
        data_1 = copy.deepcopy(data_point_1.spectrum_data.data)
        data_2 = copy.deepcopy(data_point_2.spectrum_data.data)
        mask1 = maskBadFrequencies(data_point_1, limit=limit_frq)
        mask2 = maskBadFrequencies(data_point_2, limit=limit_frq)
        mean_1 = np.nanmean(data_1)
        mean_2 = np.nanmean(data_2)
        data_point_1.spectrum_data.data[mask1, :] = mean_1
        data_point_2.spectrum_data.data[mask2, :] = mean_2
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
    data_point_1.flattenSummedCurve(
        rolling_window=correlation.default_flatten_window)
    data_point_2.flattenSummedCurve(
        rolling_window=correlation.default_flatten_window)
    if no_bg:
        data_point_1.subtractBackground()
        data_point_2.subtractBackground()
    return data_point_1, data_point_2, cor


def plotDatapoint(datapoint: data.DataPoint, curve: bool = False, save_img: bool = False, folder: str = "", short_name=False) -> None:
    """
    Creates a (pretty) Plot of a datapoint.

    :param datapoint: input data
    :param curve: bool: whether summed intensity curve gets overlain
    :param save_img: bool: whether picture gets saved
    :param folder: specify a folder for resulting file
    """
    t = np.arange(datapoint.spectrum_data.start.strftime("%Y-%m-%dT%H:%M:%S.%z"),
                  datapoint.spectrum_data.end.strftime("%Y-%m-%dT%H:%M:%S.%z"), dtype='datetime64[s]').astype(datetime)
    mt = mdates.date2num((t[0], t[-1]))

    fig, ax = plt.subplots(figsize=(plot_size_x, plot_size_y))
    fig.suptitle(
        f"{datapoint.day}.{datapoint.month}.{datapoint.year} Radio Flux Data {datapoint.observatory.name}")
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

    if curve:
        _time = datapoint.spectrum_data.time_axis
        _time_start = datapoint.spectrum_data.start.timestamp()
        ax3 = plt.twinx(ax)
        # ax3.spines["right"].set_position(("axes", 1.2))
        # ax3.yaxis.get_offset_text().set_position((1.2,1))
        # ax3.set_ylabel("data")
        ax3.set_axis_off()
        time_axis_plot2 = []
        for i in _time:
            time_axis_plot2.append(datetime.fromtimestamp(
                _time_start + i).strftime("%Y %m %d %H:%M:%S"))
        time_axis_plot2 = pd.to_datetime(time_axis_plot2)
        dataframe2 = pd.DataFrame()
        dataframe2['data'] = datapoint.summed_curve
        dataframe2 = dataframe2.set_index(time_axis_plot2)
        plot_dat = ax3.plot(dataframe2, color="white", linewidth=1,
                            label=f"Summed Intensity Curve {datapoint.observatory.name}")
        plt.legend(loc='best')
    plt.tight_layout()
    if save_img:
        name = f"{['','curve'][curve]}"+datapoint.fileName(short_name)
        if folder:
            name = os.path.join(folder, name)
        plt.savefig(name, transparent=True)
    plt.show()


def plotEverything(dp1: data.DataPoint, dp2: data.DataPoint, cor: correlation.Correlation,
                   limit=correlation.CORRELATION_MIN, save_img=False) -> None:
    """
    Creates (pretty) plot of a datapoint and resulting correlation with another datapoint

    (best to be used with output data of calcPoint)

    :param dp1: input data (gets plotted)
    :param dp2: reference data (only summed intensity plotted)
    :param cor: correlation of d1 and d2
    :param limit: float: set marks if correlation exceeds limit
    :param save_img: whether image gets saved as file
    """
    if cor.day == dp1.day:
        year = dp1.year
        month = dp1.month
        day = cor.day
    else:
        date = datetime(dp1.year, dp1.month, dp1.day) + timedelta(days=1)
        year = date.year
        month = date.month
        day = date.day

    # if len(cor.data_curve) < len(dp1.spectrum_data.time_axis[::4]):
    #    _time = dp1.spectrum_data.time_axis[::4][:len(cor.data_curve)]
    # else:
    #    _time = dp1.spectrum_data.time_axis[::4]

    _time = cor.time_axis
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
    plot_limit = ax2.axhline(limit, color="yellow",
                             linestyle='--', label='Correlation Limit')
    time_axis_plot = []
    for i in _time:
        time_axis_plot.append(datetime.fromtimestamp(
            _time_start + i).strftime("%Y %m %d %H:%M:%S"))
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
        time_axis_plot2.append(datetime.fromtimestamp(
            _time_start + i).strftime("%Y %m %d %H:%M:%S"))
    time_axis_plot2 = pd.to_datetime(time_axis_plot2)
    dataframe2 = pd.DataFrame()
    dataframe2['data'] = dp1.summed_curve
    dataframe2 = dataframe2.set_index(time_axis_plot2)
    plot_dat = ax3.plot(dataframe2, color="white", linewidth=1,
                        label=f"Summed Intensity Curve {dp1.observatory.name}")

    ax4 = plt.twinx(ax)
    ax4.set_axis_off()
    time_axis_plot3 = []
    for i in _time3:
        time_axis_plot3.append(datetime.fromtimestamp(
            _time_start + i).strftime("%Y %m %d %H:%M:%S"))
    time_axis_plot3 = pd.to_datetime(time_axis_plot3)
    dataframe3 = pd.DataFrame()
    dataframe3['data'] = dp2.summed_curve
    dataframe3 = dataframe3.set_index(time_axis_plot3)
    plot_dat2 = ax4.plot(dataframe3, color="cyan", linewidth=1,
                         label=f"Summed Intensity Curve {dp2.observatory.name}")

    plots = plot_cor + plot_dat + plot_dat2
    plots.append(plot_limit)

    _peaks_start = []
    _peaks_end = []
    for j, i in enumerate(cor.peaks):
        start = mdates.date2num(
            i.time_start-timedelta(seconds=unscientific_shift))
        end = mdates.date2num(i.time_end-timedelta(seconds=unscientific_shift))
        _peaks_start.append(start)
        _peaks_end.append(end)

        plot_b_start = plt.axvline(
            start, color="darkgrey", linestyle='--', label='Burst start')
        plot_b_end = plt.axvline(
            end, color="black", linestyle='--', label='Burst end')

        if not j:
            plots.extend([plot_b_start, plot_b_end])

    labs = [i.get_label() for i in plots]
    # -> TODO position as parameter
    plt.legend(plots, labs, loc="lower right")
    plt.tight_layout()
    if save_img:
        plt.savefig(cor.fileName(), transparent=True)
    plt.show()


def peaksInData(dp1: data.DataPoint, dp2: data.DataPoint,
                plot: bool = False, save_img: bool = False, peak_limit: float or None = None) \
        -> events.EventList:
    """
    Find peaks in dp1 and dp2 at the same datetime. limit is dynamically generated by stddev(curves) * peak_limit

    :param dp1: input data 1
    :param dp2: input data 2
    :param plot: bool: create image of calculation
    :param save_img: bool: save image as file
    :param peak_limit: float: limit for scipy.find_peaks()
    :return: events.EventList(possible bursts)

    """
    if peak_limit is None:
        peak_limit = 2.15

    # TODO different time range of files
    if dp1.observatory == dp2.observatory:
        return events.EventList([], dp1.spectrum_data.start)

    if dp1.binned_time and not dp2.binned_time:
        dp2.binDataTime(width=dp1.binned_time_width)
    elif dp2.binned_time and not dp1.binned_time:
        dp1.binDataTime(width=dp2.binned_time_width)

    dp1.subtractBackground()
    dp2.subtractBackground()
    dp1.createSummedCurve()
    dp2.createSummedCurve()
    dp1.flattenSummedCurve()
    dp2.flattenSummedCurve()
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
            peak = datetime.fromtimestamp(
                _time_start + i / dp1.points_per_second)
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
            time_axis_plot1.append(datetime.fromtimestamp(
                _time_start + i).strftime("%Y %m %d %H:%M:%S"))
        time_axis_plot1 = pd.to_datetime(time_axis_plot1)
        dataframe1 = pd.DataFrame()
        dataframe1['data'] = dp1.summed_curve
        dataframe1 = dataframe1.set_index(time_axis_plot1)
        plt.plot(dataframe1, color="red", linewidth=2,
                 label=f"{dp1.observatory}")
        for i in scipy_peaks1:
            plt.plot(mdates.date2num(datetime.fromtimestamp(
                _time_start + i / dp1.points_per_second)), x1[i], "x", color="red")

        time_axis_plot2 = []
        for i in _time2_:
            time_axis_plot2.append(datetime.fromtimestamp(
                _time_start + i).strftime("%Y %m %d %H:%M:%S"))
        time_axis_plot2 = pd.to_datetime(time_axis_plot2)
        dataframe2 = pd.DataFrame()
        dataframe2['data'] = dp2.summed_curve
        dataframe2 = dataframe2.set_index(time_axis_plot2)
        plt.plot(dataframe2, color="blue", linewidth=1,
                 label=f"{dp2.observatory}")
        for i in scipy_peaks2:
            plt.plot(mdates.date2num(datetime.fromtimestamp(
                _time_start + i / dp1.points_per_second)), x2[i], "x", color="blue")

        for i in new3:
            if not new3.index(i):
                plt.axvline(mdates.date2num(datetime.fromtimestamp(_time_start + i / dp1.points_per_second)),
                            linestyle="--", color="grey",
                            label="Possible Peak")
            else:
                plt.axvline(mdates.date2num(datetime.fromtimestamp(
                    _time_start + i / dp1.points_per_second)), linestyle="--", color="grey")

        ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=2))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        plt.xlim([mdates.date2num(time_axis_plot1[0]),
                 mdates.date2num(time_axis_plot1[-1])])
        plt.xticks(rotation=45)
        plt.legend(loc="upper left")
        plt.tight_layout()
        if save_img:
            file_name = \
                f"peaksData_{dp1.date.strftime(config.event_time_format_date)}_{dp1.observatory}_{dp2.observatory}.png"
            plt.savefig(file_name, transparent=True)
        plt.show()
    return events_


def getEvents(*args: Union[data.DataPoint, int, str, stations.Station], mask_frq: bool or None = None,
              r_window: int or None = None, flatten: bool or None = None, bin_time: bool or None = None,
              bin_freq: bool or None = None, no_bg: bool or None = None, flatten_window: int or None = None,
              bin_time_width: int or None = None, limit: float or None = None) \
        -> events.EventList:
    """
    Calculates Bursts with Correlation limit and peak finder method. Returns Burst only if both methods find the burst

    :param args: 2 DataPoints   _or_   date (datetime, or 3+ ints) and 2 stations
    :param mask_frq:
    :param r_window:
    :param flatten:
    :param bin_time:
    :param bin_freq:
    :param no_bg:
    :param flatten_window:
    :param bin_time_width:
    :param limit: for correlation method
    :return: events.EventList
    """
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
        raise ValueError(
            "Needs either datetime and 2 stations   or   2 datapoints as args")

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


def filename(*date: Union[datetime, int], step: int) -> str:
    """
    Path and name of a result file based on date of calculation and step (id)

    :param date: calculation date
    :param step: id of the file
    :return: str
    """
    date_ = config.getDateFromArgs(*date)
    return os.path.join(config.path_results, f"{date_.year}/{date_.month:02}/", 
                        f"{date_.year}_{date_.month:02}_{date_.day:02}_step{step}")


def saveData(*date: Union[datetime, int], step: int, event_list: events.EventList) -> None:
    """
    saves an EventList to a binary file in the result folder

    :param date: calculation date
    :param step: id of the file
    :param event_list: input data
    """
    date_ = config.getDateFromArgs(*date)
    file_name = filename(date_, step=step)
    folder = file_name[:file_name.rfind("/")+1]
    if not (os.path.exists(folder) and os.path.isdir(folder)):
        os.makedirs(folder)
    with open(filename(date_, step=step), "wb+") as file:
        pickle.dump(event_list, file)


def loadData(*date, step: int) -> events.EventList:
    """
    loads a result file (created with saveData()) to an EventList

    :param date: calculation date
    :param step: id of the file
    :return: event_list: data
    """
    date_ = config.getDateFromArgs(*date)
    with open(filename(date_, step=step), "rb") as read_file:
        loaded_data = pickle.load(read_file)

    return loaded_data
