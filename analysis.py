#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from scipy.signal import find_peaks
import matplotlib.pylab as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import copy
import pickle
from typing import Union

import const
import data
import correlation
import events
import observatories

plot_size_x = 19
plot_size_y = 12
mask_frq_limit = 1.5

# TODO make plot() its own function - code duplication
# TODO correlation always from -.4 to 1 !!!!!


def maskBadFrequencies(dp1, limit=mask_frq_limit):
    dpt = copy.deepcopy(dp1)
    dpt.subtract_background()
    data_ = dpt.spectrum_data.data

    summed = np.array([np.nansum(data_[f]) for f in range(len(data_))])
    summed_lim = limit * np.nanstd(summed)
    summed_mean = np.nanmean(summed)
    mask = [abs(i - summed_mean) > summed_lim for i in summed]
    return mask


def maskBadFrequenciesPlot(dp1, limit=mask_frq_limit):
    data_ = dp1.spectrum_data.data
    frq = dp1.spectrum_data.freq_axis
    summed = np.array([np.nansum(f) for f in data_])
    summed_max = np.nanmax(summed)
    summed_min = np.nanmin(summed)

    mask = maskBadFrequencies(dp1, limit=limit)
    summed_masked = copy.copy(summed)
    summed_masked[mask] = np.nanmean(summed)

    fig, ax = plt.subplots(figsize=(plot_size_x, plot_size_y))
    plt.imshow(dp1.spectrum_data.data, extent=[summed_min, summed_max, frq[0], frq[-1]],
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


def calcPoint(year: int, month: int, day: int, time: Union[str, datetime],
              obs1: observatories.Observatory, obs2: observatories.Observatory, spec_range=const.spectral_range,
              mask_frq=False, limit_frq=mask_frq_limit):
    """
    TODO -> corrupt data -> skip 
    """
    if isinstance(time, datetime):
        time_ = time.strftime("%H:%M:%S")
        date = time
    else:
        time_ = time
        date = datetime(year, month, day, int(time_[:2]), int(time_[3:5]), int(time_[6:]))

    # TODO function this -> createfromEvent -> cut front and back to 15min with peak in middle
    blind_spot = (correlation.default_r_window / correlation.default_time_window) * 2
    if (int(time_[3:5]) * 60. + int(time_[6:]))  % (const.LENGTH_FILES_MINUTES * 60) < 4 * blind_spot:
        date2 = date - timedelta(minutes=const.LENGTH_FILES_MINUTES)
        time2 = date2.strftime("%H:%M:%S")
        dp11 = data.createFromTime(year, month, day, time2, obs1, spec_range)
        dp12 = data.createFromTime(year, month, day, time_, obs1, spec_range)
        dp21 = data.createFromTime(year, month, day, time2, obs2, spec_range)
        dp22 = data.createFromTime(year, month, day, time_, obs2, spec_range)
        dp1 = dp11 + dp12               # TODO this breaks if file corrupted
        dp2 = dp21 + dp22
    else:
        dp1 = data.createFromTime(year, month, day, time_, obs1, spec_range)
        dp2 = data.createFromTime(year, month, day, time_, obs2, spec_range)

    if mask_frq:
        mask1 = maskBadFrequencies(dp1, limit=limit_frq)
        mask2 = maskBadFrequencies(dp2, limit=limit_frq)
        dp1.spectrum_data.data[mask1, :] = np.nanmean(dp1.spectrum_data.data)

        dp2.spectrum_data.data[mask2, :] = np.nanmean(dp2.spectrum_data.data)
    else:
        pass
    dp1_cor = copy.deepcopy(dp1)
    dp2_cor = copy.deepcopy(dp2)
    # TODO parameter all corr variables
    cor = correlation.Correlation(dp1_cor, dp2_cor, day=day,
                                  _flatten=True, _bin_time=True, _bin_freq=False, _no_background=True,
                                  _r_window=int(correlation.default_r_window/correlation.default_time_window),
                                  _flatten_window=correlation.default_flatten_window,
                                  _bin_time_width=correlation.default_time_window)
    cor.calculatePeaks()
    print(cor.fileName())
    print(cor.peaks)

    dp1.createSummedCurve([dp1.spectrum_data.freq_axis[-1], dp1.spectrum_data.freq_axis[-1]])
    dp2.createSummedCurve([dp2.spectrum_data.freq_axis[-1], dp2.spectrum_data.freq_axis[-1]])
    dp1.flattenSummedCurve(rolling_window=correlation.default_flatten_window)
    dp2.flattenSummedCurve(rolling_window=correlation.default_flatten_window)
    return dp1, dp2, cor


def plotDatapoint(dp1):
    t = np.arange(dp1.spectrum_data.start.strftime("%Y-%m-%dT%H:%M:%S.%z"),
                  dp1.spectrum_data.end.strftime("%Y-%m-%dT%H:%M:%S.%z"), dtype='datetime64[s]').astype(datetime)
    mt = mdates.date2num((t[0], t[-1]))

    fig, ax = plt.subplots(figsize=(plot_size_x, plot_size_y))
    fig.suptitle(f"{dp1.day}.{dp1.month}.{dp1.year} Radio Flux Data {dp1.observatory.name}")
    ax.set_xlabel("Time")
    ax.set_ylabel("Frequency [MHz]")
    plt.imshow(dp1.spectrum_data.data, extent=[mt[0], mt[1], 0, int(900 / plot_size_x * plot_size_y)],
               aspect='auto', origin='lower')
    cbar = plt.colorbar(location='right', anchor=(.15, 0.0))
    cbar.set_label("Intensity")
    ax.set_yticks([int(900 / plot_size_x * plot_size_y / 9) * i for i in range(0, 10)],
                  np.around(dp1.spectrum_data.freq_axis[::int(len(dp1.spectrum_data.freq_axis) / 9)], 1))
    ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.xticks(rotation=45)

    plt.tight_layout()
    plt.show()


def plotEverything(dp1, dp2, cor):
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
    ax2.set_ylim(-0.4,1)

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
    dataframe2['data'] = dp1.summedCurve
    dataframe2 = dataframe2.set_index(time_axis_plot2)
    plot_dat = ax3.plot(dataframe2, color="blue", linewidth=1, label=f"Summed Intensity Curve {dp1.observatory.name}")

    ax4 = plt.twinx(ax)
    ax4.set_axis_off()
    time_axis_plot3 = []
    for i in _time3:
        time_axis_plot3.append(datetime.fromtimestamp(_time_start + i).strftime("%Y %m %d %H:%M:%S"))
    time_axis_plot3 = pd.to_datetime(time_axis_plot3)
    dataframe3 = pd.DataFrame()
    dataframe3['data'] = dp2.summedCurve
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


def peaksInData(dp1, dp2, plot=False, peak_limit=2):
    """

    """
    x1 = np.array(dp1.summedCurve)
    lim1 = peak_limit * np.nanstd(x1)
    scipy_peaks1 = find_peaks(x1, height=lim1)[0]

    x2 = np.array(dp2.summedCurve)
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
    events_ = events.EventList(peaks)

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
        dataframe1['data'] = dp1.summedCurve
        dataframe1 = dataframe1.set_index(time_axis_plot1)
        plt.plot(dataframe1, color="red", linewidth=2, label=f"{dp1.observatory}")
        for i in scipy_peaks1:
            plt.plot(mdates.date2num(datetime.fromtimestamp(_time_start + i / 4)), x1[i], "x", color="red")

        time_axis_plot2 = []
        for i in _time2_:
            time_axis_plot2.append(datetime.fromtimestamp(_time_start + i).strftime("%Y %m %d %H:%M:%S"))
        time_axis_plot2 = pd.to_datetime(time_axis_plot2)
        dataframe2 = pd.DataFrame()
        dataframe2['data'] = dp2.summedCurve
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

    print(events_)
    return events_


def filename(year, month):
    return const.path_data + f"results/{year}/" + f"{year}_{str(month).zfill(2)}_unsearched_obs++"


def saveData(event_list: events.EventList, year, month):
    """
    """
    with open(filename(year, month), "wb") as file:
        pickle.dump(event_list, file)


def loadData(year, month):
    """
    """
    with open(filename(year, month), "rb") as read_file:
        loaded_data = pickle.load(read_file)

    return loaded_data
