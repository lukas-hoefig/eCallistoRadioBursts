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
from typing import List

import analysis
import const
import correlation
import events
import stations
import download
import nextcloud
import data

token_download = "token1"
token_handle   = "token2"
token_auth = "token3"

observatories = ["AUSTRIA-UNIGRAZ", "AUSTRIA-OE3FLB", "SWISS-Landschlacht"]


def deleteOldFiles():
    pass


def getFilesFromExtern():
    path_dl = const.path_data + const.pathDataDay(datetime.datetime.today())
    # nextcloud.downloadFromCloud(token_download, path=path_dl)
    download.downloadFullDay(datetime.datetime.today(), station=observatories)
    nextcloud.unzip(path_dl)


def pathData():
    today = datetime.datetime.today()
    return const.pathDataDay(today)


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


def dropOld(list_str: List[List[str]]):
    new = [i[-3:] for i in list_str]
    newest_all = [getDate(i[-1]) for i in new]
    newest = max(newest_all)
    files = [i[1] for i in enumerate(new) if
             abs((newest_all[i[0]]-newest).total_seconds()) < datetime.timedelta(minutes=3).total_seconds()]
    return files


def getFiles():
    focus_codes = [stations.getFocusCode(datetime.datetime.today(), station=obs) for obs in observatories]
    files_all = sorted(os.listdir(pathData()))
    files_stations = [[file for file in files_all
                       if file.startswith(observatory) and file.endswith(focus_codes[i] + const.file_ending)]
                      for i, observatory in enumerate(observatories)]
    files_filtered = dropOld(files_stations)

    return files_filtered


if __name__ == '__main__':
    getFilesFromExtern()
    files = getFiles()
    files = [i for i in files if i]
    if len(files) < 2:
        raise AttributeError("Not Enough Stations")
    data_points = [sum(data.DataPoint(i) for i in j) for j in files]
    event_list = events.EventList([])
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
    if event_list:
        station_names_list = [i.observatory.name for i in data_points]
        if len(data_points) == 2:
            station_names = f"{station_names_list[0]} and {station_names_list[1]}"
        else:
            station_names = f"{station_names_list[0]}, {station_names_list[1]} and {station_names_list[2]}"
        print(f"Events found at {station_names}.")
        print(event_list)
    else:
        print("No Event found.")

