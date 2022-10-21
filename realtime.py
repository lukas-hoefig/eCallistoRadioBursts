#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
functions and algorithm for the realtime implementation

:authors: 	Lukas Höfig
:contact: 	lukas.hoefig@edu.uni-graz.at
:date:       02.10.2022
"""


import copy
import datetime
import os
import sys    # sys.argv   [0]name script [1-n] arguments
from typing import List, Union
from ftplib import FTP
import shutil
import pickle

import analysis
import config
import correlation
import events
import stations
import download
import nextcloud
import data

token_download = "token1"
token_handle   = "token2"
token_auth = "token3"

ftp_server = "147.86.8.73"
ftp_acc = 'solarradio'
ftp_psswd = 'solar$251'
ftp_directory = 'XCHG'

# observatories = ["AUSTRIA-UNIGRAZ", "AUSTRIA-OE3FLB", "SWISS-Landschlacht"]


def deleteOldFiles(*date):
    if date:
        date_ = config.getDateFromArgs(*date)
    else:
        date_ = datetime.datetime.today() - datetime.timedelta(days=2)
    try:
        path = config.pathDataDay(date_)
        shutil.rmtree(path)
    except FileNotFoundError: 
        pass


def stationsToday():
    all_files = os.listdir(config.pathDataDay(datetime.datetime.today()))
    observatories = []
    for file in all_files:
        try:
            if not any([i.name == file.rsplit("_")[0] for i in observatories]):
                obs = stations.getStationFromFile(config.pathDataDay(datetime.datetime.today()) + file)
                observatories.append(obs)
        except AttributeError:
            pass
    observatories = list(set(observatories))
    return observatories


def downloadFtpNewFiles(path: str):
    with FTP(ftp_server) as ftp:
        ftp.login(ftp_acc, ftp_psswd)
        ftp.cwd(ftp_directory)
        files = ftp.nlst()
        print(f"Downloading files from server: {len(files)}")
        for i in enumerate(files):
            print(f"{i[0] + 1:4} ({ftp.size(i[1])/1024:9.3f} kB): {i[1]}           ", end="\r")
            with open(path + i[1], 'wb') as fp:
                # CMD = 'RETR ' + config.pathDataDay(datetime.datetime.today()) + i
                CMD = 'RETR ' + i[1]
                ftp.retrbinary(CMD, fp.write)
        ftp.quit()
    print("All files downloaded successfully                                         ")
    

def getFilesFromExtern(observatories=None):
    if observatories is None:
        observatories = ["AUSTRIA-UNIGRAZ", "AUSTRIA-OE3FLB", "SWISS-Landschlacht", "BIR", "HUMAIN", "ALASKA-HAARP",
                         "ALASKA-COHOE", "GLASGOW", "Australia-ASSA", "ROSWELL-NM", "ALMATY", "Arecibo-Observatory",
                         "INDONESIA", "TRIEST"]
    path_dl = config.pathDataDay(datetime.datetime.today())
    # downloadFtpNewFiles(path_dl)    <--- finally
    # nextcloud.downloadFromCloud(token_download, path=path_dl)
    # download.downloadFullDay(datetime.datetime.today(), station=observatories)
    download.downloadLastHours(observatories)
    # nextcloud.unzip(path_dl)


def getDate(file: str):
    reader = file.rsplit('/')[-1]
    reader = reader.rsplit('_')

    year = int(reader[1][:4])
    month = int(reader[1][4:6])
    day = int(reader[1][6:])
    hour = int(reader[2][:2])
    minute = int(reader[2][2:4])
    second = int(reader[2][4:])

    return datetime.datetime(year, month, day, hour, minute, second)


def dropOld(list_str: List[List[str]], num=2):
    new = [i[-num:] for i in list_str]
    newest_all = [getDate(i[-1]) for i in new]
    newest = max(newest_all)
    files = [i[1] for i in enumerate(new) if
             abs((newest_all[i[0]]-newest).total_seconds()) < datetime.timedelta(minutes=3).total_seconds()]
    return files


def getFiles(observatories: List[Union[str, stations.Station]]):
    for i in enumerate(observatories):
        if isinstance(i[1], str):
            observatories[i[0]] = stations.Station(i[1], stations.getFocusCode(datetime.datetime.today(), station=i[1]))

    # focus_codes = [stations.getFocusCode(datetime.datetime.today(), station=obs) for obs in observatories]
    files_all = sorted(os.listdir(config.pathDataDay(datetime.datetime.today())))
    files_stations = [[file for file in files_all
                       if file.startswith(observatory.name) and
                          file.endswith(observatory.focus_code + config.file_ending)] for observatory in observatories]
    files_filtered = dropOld(files_stations)

    return files_filtered


def filename():
    today = datetime.datetime.today()
    return config.path_realtime + config.pathDay(today) + f"{today.year}_{today.month}_{today.day}"


def saveRealtimeTxt(event_list: events.EventList):
    file_name = filename() + ".txt"
    with open(file_name, "w+") as file:
        file.write("\n".join([events.header(), str(event_list)]))


def saveRealTime(event_list: events.EventList):
    file_name = filename()
    folder = file_name[:file_name.rfind("/")+1]
    if not (os.path.exists(folder) and os.path.isdir(folder)):
        os.makedirs(folder)
    if os.path.exists(filename()):
        os.remove(filename())
    with open(filename(), "wb") as file:
        pickle.dump(event_list, file)


def loadRealTime() -> events.EventList:
    file = filename()
    folder = file[:file.rfind("/") + 1]
    if os.path.exists(filename()):
        with open(file, "rb") as read_file:
            loaded_data = pickle.load(read_file)
        return loaded_data
    else:
        if not (os.path.exists(folder) and os.path.isdir(folder)):
            os.makedirs(folder)

        return events.EventList([], today)


if __name__ == "__main__":
    today = datetime.datetime.today()
    getFilesFromExtern()
    # deleteOldFiles()
    obs = stationsToday()
    f = getFiles(obs)
    e_list_old = loadRealTime()
    e_list_new = events.EventList([], datetime.datetime.today())
    sets = [sum([data.DataPoint(j) for j in i]) for i in f]
    for i, data_point_1 in enumerate(sets):
        for j, data_point_2 in enumerate(sets[i+1:]):
            data_1 = copy.deepcopy(data_point_1)
            data_2 = copy.deepcopy(data_point_2)
            if not data_1 or not data_2:
                continue
            # if mask_frq:
            #    mask1 = analysis.maskBadFrequencies(data_1)
            #    mask2 = analysis.maskBadFrequencies(data_2)
            # data1.spectrum_data.data[mask1] = np.nanmean(data1.spectrum_data.data)
            # data2.spectrum_data.data[mask2] = np.nanmean(data2.spectrum_data.data)
            corr = correlation.Correlation(data_1, data_2, today.day, no_background=True, bin_freq=False,
                                           bin_time=False, flatten=True, bin_time_width=4,
                                           flatten_window=None, r_window=180)
            corr.calculatePeaks(limit=.6)
            try:
                if corr.peaks:
                    e_list_new += corr.peaks
            except AttributeError:
                pass
        else:
            pass
    try:
        e_list_new.sort()
    except AttributeError:
        # empty list
        pass

    if not e_list_new:
        saveRealTime(e_list_old)
        saveRealtimeTxt(e_list_old)
        quit()

    e_list_new2 = events.EventList([], datetime.datetime.today())
    for event in e_list_new2:
        obs = stations.StationSet(event.stations)
        set_obs = obs.getSet()
        for i in set_obs:
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
                    dp1, dp2, cor = analysis.calcPoint(event.time_start, obs1=i[0], obs2=i[1], mask_frq=True,
                                                       r_window=30,
                                                       flatten=True, bin_time=True, bin_freq=False, no_bg=True,
                                                       flatten_window=4, bin_time_width=None, limit=0.8)
                    if dp1 is None:
                        continue
                    for peak in cor.peaks:
                        if peak.inList(event_peaks):
                            e_list_new2 += peak
                        else:
                            pass
            except FileNotFoundError:
                continue
            except AttributeError:
                continue

    if not e_list_new2:
        saveRealTime(e_list_old)
        saveRealtimeTxt(e_list_old)
        quit()

    e_list_new3 = events.EventList([], datetime.datetime.today())
    limit_1 = 0.90
    limit_2 = 0.95

    for i in e_list_new2:
        if i.probability < limit_1:
            continue
        peak_list = events.EventList([], datetime.datetime.today())
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
            e_list_new3 += i

    if not e_list_new3:
        saveRealTime(e_list_old)
        saveRealtimeTxt(e_list_old)
        quit()

    e_list = e_list_old + e_list_new3
    saveRealTime(e_list)
    saveRealtimeTxt(e_list)


"""
if __name__ == '__main__':
    getFilesFromExtern()
    files = getFiles()
    files = [i for i in files if i]
    if len(files) < 2:
        raise AttributeError("Not Enough Stations")
    data_points = [sum(data.DataPoint(i) for i in j) for j in files]
    event_list = events.EventList([], datetime.datetime.today())
    if len(data_points) == 2:
        dp1, dp2, cor = analysis.calcPoint(datetime.datetime.today(), data_point_1=data_points[0],
                                           data_point_2=data_points[1],
                                           obs1=data_points[0].observatory, obs2=data_points[1].observatory,
                                           mask_frq=True, limit=0.8, flatten=True, bin_time=True, bin_freq=False,
                                           no_bg=True, r_window=30)
        event_list += cor.peaks
    else:
        dp00 = copy.deepcopy(data_points[0])
        dp01 = copy.deepcopy(data_points[1])
        dp1, dp2, cor1 = analysis.calcPoint(datetime.datetime.now(), data_point_1=dp00, data_point_2=dp01,
                                            obs1=data_points[0].observatory, obs2=data_points[1].observatory,
                                            mask_frq=True, limit=0.8, flatten=True, bin_time=True, bin_freq=False,
                                            no_bg=True, r_window=30)
        try:
            event_list += cor1.peaks
        except AttributeError:
            pass
        dp10 = copy.deepcopy(data_points[0])
        dp11 = copy.deepcopy(data_points[2])
        dp1, dp2, cor2 = analysis.calcPoint(datetime.datetime.now(), data_point_1=dp10, data_point_2=dp11,
                                            obs1=data_points[0].observatory, obs2=data_points[1].observatory,
                                            mask_frq=True, limit=0.8, flatten=True, bin_time=True, bin_freq=False,
                                            no_bg=True, r_window=30)
        try:
            event_list += cor2.peaks
        except AttributeError:
            pass

        dp20 = copy.deepcopy(data_points[1])
        dp21 = copy.deepcopy(data_points[2])
        dp1, dp2, cor3 = analysis.calcPoint(datetime.datetime.now(), data_point_1=dp20, data_point_2=dp21,
                                            obs1=data_points[0].observatory, obs2=data_points[1].observatory,
                                            mask_frq=True, limit=0.8, flatten=True, bin_time=True, bin_freq=False,
                                            no_bg=True, r_window=30)
        try:
            event_list += cor3.peaks
        except AttributeError:
            pass
        
    print(events.header() + event_list)
"""
