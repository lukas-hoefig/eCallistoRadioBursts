#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import os 
from typing import List

import const
import stations
import download
import data

# TODO
# get files from nextcloud
# read newest files (+1h)
# create dp
# run correlation 
# get peaks
# -> if any: do something
# -> if not: do something else

observatories = ["AUSTRIA-UNIGRAZ", "AUSTRIA-OE3FLB", "SWISS-Landschlacht"]


def getFilesFromExtern():
    # TODO replayce with whatever -> nextcloud | (ba)sh scripts
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


def isNew(file: str):
    file_date = getDate(file)
    today = datetime.datetime.today()
    difference = (today - file_date).total_seconds()
    return difference < datetime.timedelta(minutes=50).total_seconds()


def dropOld(obs: List[str]):
    return obs[-3:]
    # return [file for file in obs if isNew(file)]


def getFiles():
    """
    TODO switch dropold-only when a new file ?
    """
    focus_codes = [stations.getFocusCode(datetime.datetime.today(), station=obs) for obs in observatories]
    files_all = os.listdir(pathData())
    files_stations = [[file for file in files_all
                       if file.startswith(observatory) and file.endswith(focus_codes[i] + const.file_ending)]
                      for i, observatory in enumerate(observatories)]
    files_filtered = [dropOld(files) for files in files_stations]

    newest = [getDate(i[-1]) for i in files_filtered]
    newest_max = max(newest)
    files_new = [files for i, files in enumerate(files_filtered) if 
                 (newest[i] - newest_max).total_seconds() < datetime.timedelta(minutes=5).total_seconds()]

    return files_new


if __name__ == '__main__':
    getFilesFromExtern()
    files = getFiles()
    files = [i for i in files if i]
    print(files)
    if len(files) < 2:
        raise AttributeError("Not Enough Stations")
    if len(files) == 2:
        # run for 2 stations
        # datapoints
        # correlation
        # get peaks
        # if peaks newer than 15min -> print or something
        pass
    else:
        # run for 3 stations
        # sets
        pass
