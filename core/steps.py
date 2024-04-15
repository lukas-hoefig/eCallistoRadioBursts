#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
 -  ROBUST  -
 - steps.py -

Contains step structure of the algorithm
top level
"""

import copy
import numpy as np
from typing import List, Union
import warnings
import datetime

import config
import download
import stations
import analysis
import events
import data


def dataSetDay(*date: Union[datetime.datetime, int], run: bool = False, eu_ut: bool = False) -> List[data.DataPoint]:
    """
    creates a list of the longest continuous timeframes for all stations for a specific day

    :param date: 
    :param run: True: also searches local files | False: searches external files on the server, downloads missing files
    :param eu_ut: restricts calculation time to 08:00-17:00 UT
    :return: List[data.DataPoint]
    """
    date_ = config.getDateFromArgs(*date)
    if run:
        print(f"\nGetting Stations for 1st Step: {date_.year} {date_.month:02} {date_.day:02}")
        observatories = stations.getStations(date_, offline=True)
    else:
        observatories = stations.getStations(date_, offline=False)
        download.downloadFullDay(date_, station=observatories)
    print(len(observatories), "observatories found")
    sets = []
    for j in observatories:
        if eu_ut:
            sets.extend(data.listDataPointDayEuropeUT(date_, station=j))
        else:
            sets.extend(data.listDataPointDay(date_, station=j))
    sets_summed = [sum(i) for i in sets]
    return sets_summed


def firstStep(*date: Union[datetime.datetime, int], data_sets: List[data.DataPoint], mask_frq: bool or None = False,
              nobg: bool or None = False, bin_f: bool or None = False, bin_t: bool or None = False,
              flatten: bool or None = False, bin_t_w: int = 4, flatten_w: int or None = 400, r_w: int = 180,
              limit: float or None = None) -> events.EventList:
    """
    Calculates via correlation method for all permutations of data points in data_sets

    :param date: calculation day
    :param data_sets: input data
    :param mask_frq: toggle dynamic frequency masking
    :param nobg: toggle background subtraction
    :param bin_f: toggle binning over frequency
    :param bin_t: toggle binning over time
    :param flatten: toggle median subtraction
    :param bin_t_w: #points to be merged into one point compared to default 4 points/second
    :param flatten_w: rolling window size for median subtraction
    :param r_w: rolling window for correlation method
    :param limit: detection threshold
    :return: events.Eventlist
    """
    print(f"\nstarting 1st Step:")
    date_ = config.getDateFromArgs(*date)
    if limit is None:
        limit = config.correlation_start
    else:
        limit = limit
    perm_abs = int(len(data_sets) * (len(data_sets) - 1) / 2)
    perm = 0
    print(perm_abs, "permutations to go")
    e_list = events.EventList([], date_)
    for i, data_point_1 in enumerate(data_sets):
        print(f"Start permutations of {data_point_1.observatory} ({perm+1:6} / {perm_abs:6})", end="\r")
        for j, data_point_2 in enumerate(data_sets[i + 1:]):
            perm += 1
            data1 = copy.deepcopy(data_point_1)
            data2 = copy.deepcopy(data_point_2)
            if data1 and data2:
                dp1, dp2, corr = analysis.calcPoint(date_, obs1=data1.observatory, obs2=data2.observatory,
                                                    data_point_1=data1, data_point_2=data2, limit=limit,
                                                    no_bg=nobg, bin_freq=bin_f, bin_time=bin_t,
                                                    flatten=flatten, bin_time_width=bin_t_w, mask_frq=mask_frq,
                                                    flatten_window=flatten_w, r_window=r_w)
                try:
                    if corr.peaks:
                        e_list += corr.peaks
                except AttributeError:
                    pass
            else:
                pass
    try:
        e_list.sort()
    except AttributeError:
        # empty list
        pass
    return e_list


def secondStep(data_set: events.EventList, *date: Union[datetime.datetime, int],
               mask_freq: bool or None = True, no_bg: bool or None = True, bin_f: bool or None = False,
               bin_t: bool or None = True, bin_t_w: int or None = None,
               flatten: bool or None = True, flatten_w: int or None = None,
               r_w: int = 30) -> events.EventList:
    """
    first verification step with correlation method,
    smaller timeframe (3 minutes around bursts)
    threshold for detection: config.correlation_limit_2

    :param data_set: input data
    :param date:
    :param mask_freq: toggle dynamic frequency masking
    :param no_bg: toggle background subtraction
    :param bin_f: toggle binning over frequency
    :param bin_t: toggle binning over time
    :param bin_t_w: #points to be merged into one point compared to default 4 points/second
    :param flatten: toggle median subtraction
    :param flatten_w: rolling window size for median subtraction
    :param r_w: rolling window for correlation method
    :return:
    """
    date_ = config.getDateFromArgs(*date)
    if data_set is None:
        events_day = analysis.loadData(date_, step=2)
    else:
        events_day = data_set
    e_list = events.EventList([], date_)
    limit = config.correlation_limit_2

    num_events = len(events_day)
    current = 0
    print(f"\nStarting 2nd Step\n{date_.year} {date_.month:02} {date_.day:02}, {num_events} events to go")
    for event in events_day:
        current += 1
        print(f"{current:4} / {num_events:4} | {event}")
        obs = stations.StationSet(event.stations)
        set_obs = obs.getSet()
        for i in set_obs:
            print(i)
            try:
                d1 = data.createFromEvent(event, station=i[0])
                d2 = data.createFromEvent(event, station=i[1])
                if d1.spectrum_data is None or d2.spectrum_data is None:
                    continue
                dp1, dp2, cor = analysis.calcPoint(event.time_start, obs1=i[0], obs2=i[1],
                                                   data_point_1=d1, data_point_2=d2,
                                                   mask_frq=mask_freq, r_window=r_w,
                                                   flatten=flatten, bin_time=bin_t, bin_freq=bin_f, no_bg=no_bg,
                                                   flatten_window=flatten_w, bin_time_width=bin_t_w, limit=limit)
                """
                # TODO maybe different values (1)
                # increase threshold, when correlation is too high for the timeframe 
                #   filters too strong with these values
                
                if np.nanmean(cor.data_curve) > config.correlation_noise_limit_high:
                    cor.peaks = events.EventList([], event.time_start)
                    limit = config.correlation_limit_high_noise
                elif np.nanmean(cor.data_curve) > config.correlation_noise_limit_low:
                    cor.peaks = events.EventList([], event.time_start)
                    limit = config.correlation_limit_low_noise
                """
                cor.calculatePeaks(limit=limit)

                if dp1 is None:
                    continue
                if events.includes(cor.peaks, event):
                    e_list += cor.peaks                         # TODO don't add (stretched out) event, add event from cor.peaks
                else:
                    pass
            except FileNotFoundError:
                warnings.warn(message="Some file not found", category=UserWarning)
            except (AttributeError, TypeError, OverflowError, ValueError):
                # TypeError: buffer is too small for requested array
                # getStationFromFile : frq_axis = fds[1].data["frequency"].flatten()
                # corrupt file
                # valueError: corrupt file, caused in
                #   File "./analysis.py", in calcPoint
                #   mean_2 = np.nanmean(data_2)  | resulting array read only
                continue

    return e_list


def thirdStep(data_set: events.EventList, *date: Union[int, datetime.datetime], peak_limit: float or None = None,
              mask_frq: bool or None = False, bin_time_w: int = 0, limit_skip: float or None = None, limit_skip2: float or None = None) \
        -> events.EventList:
    """
    second verification step with peak finder method, or initial very high correlation from first verification
    smaller timeframe (3 minutes around bursts)
    threshold for detection: config.correlation_limit_2

    :param data_set: input data
    :param date:
    :param peak_limit: limit for peak finder method
    :param mask_frq: toggle dynamic frequency masking
    :param bin_time_w: #points to be merged into one point compared to default 4 points/second | 0 for no binning
    :return:
    """
    if peak_limit is None:
        peak_limit = 3

    date_ = config.getDateFromArgs(*date)
    if data_set is None:
        events_day = analysis.loadData(date_, step=3)
    else:
        events_day = data_set
    e_list = events.EventList([], date_)

    if limit_skip is None:

        limit_1 = config.correlation_limit_1
    else:
        limit_1 = limit_skip

    if limit_skip2 is None:
        peak_limit_low = 0.5  #correlation_limit_high_noise
    else:
        peak_limit_low = limit_skip2
    limit_2 = config.correlation_limit_higher
    print(f"\nStarting 3rd Step\n{date_.year} {date_.month:02} {date_.day:02}")
    for i in events_day:
        print(f"{i}                                                      ", end="\r")
        if i.probability > config.correlation_limit_high_noise and len(i.stations) > 7:
            e_list += i
            continue
        if i.probability < limit_1:
            continue
        peak_list = events.EventList([], date_)
        peak_list_low_limit = events.EventList([], date_)
        obs = stations.stationRange(i.stations)
        for j in obs:
            try:
                d1 = data.createFromTime(
                    i.time_start, station=j[0], extent=False)
                d2 = data.createFromTime(
                    i.time_start, station=j[1], extent=False)
                if bin_time_w:
                    d1.binDataTime(bin_time_w)
                    d2.binDataTime(bin_time_w)
                if mask_frq:
                    mask1 = analysis.maskBadFrequencies(
                        d1, limit=analysis.mask_frq_limit)
                    mask2 = analysis.maskBadFrequencies(
                        d2, limit=analysis.mask_frq_limit)
                    d1.spectrum_data.data[mask1, :] = np.nanmean(
                        d1.spectrum_data.data)
                    d2.spectrum_data.data[mask2, :] = np.nanmean(
                        d2.spectrum_data.data)
                ev = analysis.peaksInData(d1, d2, peak_limit=peak_limit)
                if i.inList(ev):
                    peak_list += ev
                ev_low_limit = analysis.peaksInData(d1, d2, peak_limit=peak_limit_low)
                if i.inList(ev_low_limit):
                    peak_list_low_limit += ev_low_limit

            except (FileNotFoundError, AttributeError, OverflowError):
                # file does not exist | corrupt file
                continue
        
        if peak_list_low_limit and (i.probability > limit_2 and len(i.stations) > 2) or peak_list:
            e_list += i
    # analysis.saveData(date_, event_list=e_list, step=10)
    return e_list


"""
def possibleFilterStepAfterInitialSearch(data_set, *date, limit=2.25, limit_corr=None):
    raise DeprecationWarning("Dropped due to increasing complexity - results where promising")
    date_ = config.getDateFromArgs(*date)
    if data_set is None:
        events_day = analysis.loadData(date_, step=1)
    else:
        events_day = data_set
    if limit_corr is None:
        limit_corr = config.correlation_limit_low_noise

    e_list = events.EventList([], date_)

    print(f"\nStarting 2nd Step\n{date_.year} {date_.month:02} {date_.day:02}")
    for i in events_day:
        if i.probability > limit_corr or len(i.stations) > 4:
            e_list += i
            continue
        obs = stations.stationRange(i.stations)
        for j in obs:
            try:
                d1 = data.createFromEvent(i, station=j[0])
                d2 = data.createFromEvent(i, station=j[1])
                ev = analysis.peaksInData(d1, d2, peak_limit=limit)
                if events.includes(ev, i):
                    e_list += i
            except FileNotFoundError:
                warnings.warn(message="Some file not found", category=UserWarning)
            except AttributeError:
                pass
    # analysis.saveData(date_, event_list=e_list, step=step_save)
    return e_list
"""
