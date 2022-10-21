#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import copy
import numpy as np

import warnings

import download
import stations
import analysis
import events
import data
import correlation
import config


def run1stSearch(*date, mask_frq=False, nobg=True, bin_f=False, bin_t=False,
                 flatten=True, bin_t_w=4, flatten_w=400, r_w=180):
    date_ = config.getDateFromArgs(*date)
    limit = 0.6

    print(f"starting 1st Step: {date_.year} {date_.month:02} {date_.day:02}")
    observatories = stations.getStations(date_)
    print(len(observatories), "observatories found")
    download.downloadFullDay(date_, station=observatories)
    sets = []
    for j in observatories:
        sets.extend(data.listDataPointDay(date_, station=j))
    perm_abs = int(len(sets) * (len(sets) - 1) / 2)
    perm = perm_abs + 1
    print(perm_abs, "permutations to go")
    e_list = events.EventList([], date_)
    for set1 in range(len(sets)):
        for set2 in range(set1 + 1, len(sets)):
            perm -= 1
            data1_raw = copy.deepcopy(sets[set1])
            data2_raw = copy.deepcopy(sets[set2])
            data1 = sum(data1_raw)
            data2 = sum(data2_raw)
            if data1 and data2:
                print(f"{perm:6} / {perm_abs:6} | {data1.observatory} {data2.observatory}                   ", end="\r")
                if mask_frq:
                    mask1 = analysis.maskBadFrequencies(data1)
                    mask2 = analysis.maskBadFrequencies(data2)
                    data1.spectrum_data.data[mask1] = np.nanmean(data1.spectrum_data.data)
                    data2.spectrum_data.data[mask2] = np.nanmean(data2.spectrum_data.data)
                corr = correlation.Correlation(data1, data2, date_.day, no_background=nobg, bin_freq=bin_f,
                                               bin_time=bin_t, flatten=flatten, bin_time_width=bin_t_w,
                                               flatten_window=flatten_w, r_window=r_w)
                corr.calculatePeaks(limit=limit)
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
    analysis.saveData(date_, event_list=e_list, step=1)
    return e_list


def run2ndSearch(*date, mask_freq=True, no_bg=True, bin_f=False, bin_t=True, flatten=True, bin_t_w=None, flatten_w=None,
                 r_w=30):
    date_ = config.getDateFromArgs(*date)
    events_day = analysis.loadData(date_, step=1)
    e_list = events.EventList([], date_)
    limit = 0.8

    num_events = len(events_day)
    current = 0
    print(f"Starting 2nd Step\n{date_.year} {date_.month:02} {date_.day:02}, {num_events} events to go")
    for event in events_day:
        current += 1
        print(f"{current:4} / {num_events:4} | {event}", end="\r")
        obs = stations.StationSet(event.stations)
        set_obs = obs.getSet()
        for i in set_obs:
            print(i)
            try:
                dp1_peak = data.createFromTime(event.time_start, station=i[0], extent=False)
                dp2_peak = data.createFromTime(event.time_start, station=i[1], extent=False)
                if dp1_peak.spectrum_data is None or dp2_peak.spectrum_data is None:
                    continue
                # m1 = analysis.maskBadFrequencies(dp1_peak)
                # m2 = analysis.maskBadFrequencies(dp2_peak)
                # dp1_peak.spectrum_data.data[m1,:] = 0
                # dp2_peak.spectrum_data.data[m2,:] = 0
                dp1_peak.createSummedCurve()
                dp2_peak.createSummedCurve()
                dp1_peak.flattenSummedCurve()
                dp2_peak.flattenSummedCurve()
                dp1_peak.subtractBackground()
                dp2_peak.subtractBackground()
                event_peaks = analysis.peaksInData(dp1_peak, dp2_peak)
                if event.inList(event_peaks):
                    dp1, dp2, cor = analysis.calcPoint(event.time_start, obs1=i[0], obs2=i[1], mask_frq=mask_freq,
                                                       r_window=r_w,
                                                       flatten=flatten, bin_time=bin_t, bin_freq=bin_f, no_bg=no_bg,
                                                       flatten_window=bin_t_w, bin_time_width=flatten_w, limit=limit)
                    if dp1 is None:
                        continue
                    for peak in cor.peaks:
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
    print(f"Starting 3rd Step\n{date_.year} {date_.month:02} {date_.day:02}")
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
