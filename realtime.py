#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
functions and algorithm for the realtime implementation

:authors: 	Lukas Höfig
:contact: 	lukas.hoefig@edu.uni-graz.at
:date:       02.10.2022
"""

import datetime
import os
import sys    # sys.argv   [0]name script [1-n] arguments
from typing import List

import analysis
import const
import correlation
import stations
import download
import nextcloud
import data

token_download = "token1"
token_handle   = "token2"
token_auth = "token3"

observatories = ["AUSTRIA-UNIGRAZ", "AUSTRIA-OE3FLB", "SWISS-Landschlacht"]


def getFilesFromExtern():
    path_dl = const.path_data + const.pathDataDay(datetime.datetime.today())
    # nextcloud.downloadFromCloud(token_download, path=path_dl)
    download.downloadFullDay(datetime.datetime.today(), station=observatories)


def pathData():
    today = datetime.datetime.today()
    return const.path_script + const.path_data + f"{today.year}/{today.month:02}/{today.day:02}/"


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
    """
    TODO switch dropold-only when a new file ?
    """
    focus_codes = [stations.getFocusCode(datetime.datetime.today(), station=obs) for obs in observatories]
    files_all = os.listdir(pathData())
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

    if len(data_points) == 2:
        dp1, dp2, cor = analysis.calcPoint(datetime.datetime.today(), dp1=data_points[0], dp2=data_points[1],
                                           obs1=data_points[0].observatory, obs2=data_points[1].observatory)
        analysis.plotEverything(dp1, dp2, cor)

    # TODO 3 stations available
    