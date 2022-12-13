#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import copy
import numpy as np
from typing import List
import warnings

import download
import stations
import analysis
import events
import data
import config


def dataSetDay(*date, run=False):
    date_ = config.getDateFromArgs(*date)
    if run:
        print(f"\nGetting Stations for 1st Step: {date_.year} {date_.month:02} {date_.day:02}")
    observatories = stations.getStations(date_)
    if run:
        print(len(observatories), "observatories found")
    download.downloadFullDay(date_, station=observatories)
    sets = []
    for j in observatories:
        sets.extend(data.listDataPointDay(date_, station=j))
    sets_summed = [sum(i) for i in sets]
    return sets_summed


def firstStep(*date, data_sets: List[data.DataPoint], mask_frq=False, nobg=True, bin_f=False, bin_t=False,
              flatten=True, bin_t_w=4, flatten_w=400, r_w=180, limit=None):
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
        for j, data_point_2 in enumerate(data_sets[i + 1:]):
            perm += 1
            data1 = copy.deepcopy(data_point_1)
            data2 = copy.deepcopy(data_point_2)
            if data1 and data2:
                print(f"{perm:6} / {perm_abs:6} | {data1.observatory} {data2.observatory}                   ", end="\r")

                dp1, dp2, corr = analysis.calcPoint(date, obs1=data1.observatory, obs2=data2.observatory,
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
    # analysis.saveData(date_, event_list=e_list, step=step_save)
    return e_list


def run2ndSearch(*date, mask_freq=True, no_bg=True, bin_f=False, bin_t=True, flatten=True, bin_t_w=None, flatten_w=None,
                 r_w=30):
    date_ = config.getDateFromArgs(*date)
    events_day = analysis.loadData(date_, step=1)
    e_list = events.EventList([], date_)
    limit = 0.8

    num_events = len(events_day)
    current = 0
    print(f"\nStarting 2nd Step\n{date_.year} {date_.month:02} {date_.day:02}, {num_events} events to go")
    for event in events_day:
        current += 1
        print(f"{current:4} / {num_events:4} | {event}")
        obs = stations.StationSet(event.stations)
        set_obs = obs.getSet()
        valid = False
        for i in set_obs:
            print(i)
            try:
                if valid:
                    break
                dp1_peak = data.createFromEvent(event, station=i[0])
                dp2_peak = data.createFromEvent(event, station=i[1])
                if dp1_peak.spectrum_data is None or dp2_peak.spectrum_data is None:
                    continue
                m1 = analysis.maskBadFrequencies(dp1_peak)
                m2 = analysis.maskBadFrequencies(dp2_peak)
                dp1_peak.spectrum_data.data[m1, :] = 0
                dp2_peak.spectrum_data.data[m2, :] = 0
                event_peaks = analysis.peaksInData(dp1_peak, dp2_peak)
                if event.inList(event_peaks):
                    dp1, dp2, cor = analysis.calcPoint(event.time_start, obs1=i[0], obs2=i[1], mask_frq=mask_freq,
                                                       r_window=r_w,
                                                       flatten=flatten, bin_time=bin_t, bin_freq=bin_f, no_bg=no_bg,
                                                       flatten_window=bin_t_w, bin_time_width=flatten_w, limit=limit)
                    if np.nanmean(cor.data_curve) > config.correlation_noise_limit_high:
                        cor.peaks = []
                        limit = config.correlation_limit_high_noise
                    elif np.nanmean(cor.data_curve) > config.correlation_noise_limit_low:
                        cor.peaks = []
                        limit = config.correlation_limit_low_noise
                    cor.calculatePeaks(limit=limit)

                    if dp1 is None:
                        continue
                    for peak in cor.peaks:
                        # if peak.inList(events.EventList(event),event.time_start):         # TODO -> add event to list and skip other station combinations
                        #     valid = True
                        if peak.inList(event_peaks):
                            e_list += peak
                        else:
                            pass
            except FileNotFoundError:
                warnings.warn(message="Some file not found", category=UserWarning)
            except AttributeError:
                continue

    analysis.saveData(date_, event_list=e_list, step=2)
    return e_list


def run3rdSearch(*date):
    date_ = config.getDateFromArgs(*date)
    events_day = analysis.loadData(date_, step=2)
    e_list = events.EventList([], date_)
    limit_1 = 0.90
    limit_2 = 0.95
    print(f"\nStarting 3rd Step\n{date_.year} {date_.month:02} {date_.day:02}")
    for i in events_day:
        if i.probability < limit_1:
            continue
        peak_list = events.EventList([], date_)
        obs = stations.StationSet(i.stations)
        set_obs = obs.getSet()
        for j in set_obs:
            d1 = data.createFromTime(i.time_start, station=j[0], extent=False)
            d2 = data.createFromTime(i.time_start, station=j[1], extent=False)
            d1.createSummedCurve()
            d2.createSummedCurve()
            d1.flattenSummedCurve()
            d2.flattenSummedCurve()
            d1.subtractBackground()
            d2.subtractBackground()
            ev = analysis.peaksInData(d1, d2, peak_limit=3)
            peak_list += ev
        if not peak_list and i.probability < limit_2:
            pass
        else:
            e_list += i
    analysis.saveData(date_, event_list=e_list, step=3)
    return e_list


def secondStep(data_set, *date):
    date_ = config.getDateFromArgs(*date)
    if data_set is None:
        events_day = analysis.loadData(date_, step=1)
    else:
        events_day = data_set
    e_list = events.EventList([], date_)

    print(f"\nStarting 2nd Step\n{date_.year} {date_.month:02} {date_.day:02}")
    for i in events_day:
        if i.probability > config.correlation_limit_low_noise or len(i.stations) > 4:
            e_list += i
            continue
        obs = stations.stationRange(i.stations)
        for j in obs:
            try:
                d1 = data.createFromEvent(i, station=j[0])
                d2 = data.createFromEvent(i, station=j[1])
                ev = analysis.peaksInData(d1, d2, peak_limit=2.25)
                if events.includes(ev, i):
                    e_list += i
            except FileNotFoundError:
                warnings.warn(message="Some file not found", category=UserWarning)
            except AttributeError:
                pass
    # analysis.saveData(date_, event_list=e_list, step=step_save)
    return e_list


def thirdStep(data_set, *date, mask_freq=True, no_bg=True, bin_f=False, bin_t=True, flatten=True, bin_t_w=None,
              flatten_w=None,
              r_w=30):
    date_ = config.getDateFromArgs(*date)
    if data_set is None:
        events_day = analysis.loadData(date_, step=2)
    else:
        events_day = data_set
    e_list = events.EventList([], date_)
    limit = config.correlation_limit_2

    num_events = len(events_day)
    current = 0
    print(f"\nStarting 3rd Step\n{date_.year} {date_.month:02} {date_.day:02}, {num_events} events to go")
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
                if np.nanmean(cor.data_curve) > config.correlation_noise_limit_high:
                    cor.peaks = events.EventList([], event.time_start)
                    limit = config.correlation_limit_high_noise
                elif np.nanmean(cor.data_curve) > config.correlation_noise_limit_low:
                    cor.peaks = events.EventList([], event.time_start)
                    limit = config.correlation_limit_low_noise
                cor.calculatePeaks(limit=limit)

                if dp1 is None:
                    continue
                if events.includes(cor.peaks, event):
                    e_list += event
                else:
                    pass
            except FileNotFoundError:
                warnings.warn(message="Some file not found", category=UserWarning)
            except AttributeError:
                continue

    # analysis.saveData(date_, event_list=e_list, step=3)
    return e_list


def fourthStep(data_set, *date):
    date_ = config.getDateFromArgs(*date)
    if data_set is None:
        events_day = analysis.loadData(date_, step=3)
    else:
        events_day = data_set
    e_list = events.EventList([], date_)
    limit_1 = config.correlation_limit_lower
    limit_2 = config.correlation_limit_higher
    print(f"\nStarting 3rd Step\n{date_.year} {date_.month:02} {date_.day:02}")
    for i in events_day:
        print(f"{i}                                                      ", end="\r")
        if i.probability < limit_1:
            continue
        peak_list = events.EventList([], date_)
        obs = stations.stationRange(i.stations)
        for j in obs:
            d1 = data.createFromTime(i.time_start, station=j[0], extent=False)
            d2 = data.createFromTime(i.time_start, station=j[1], extent=False)
            ev = analysis.peaksInData(d1, d2, peak_limit=3)
            peak_list += ev
        if not peak_list and i.probability < limit_2:
            pass
        else:
            e_list += i
    # analysis.saveData(date_, event_list=e_list, step=10)
    return e_list
