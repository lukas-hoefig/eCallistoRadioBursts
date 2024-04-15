#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
 -  ROBUST  -
 - download.py -

manages download of e-callisto files from website
"""

import datetime
import radiospectra.sources.callisto as cal
import os
import copy
from typing import List, Union, Tuple
import io

import config
import stations

file_log = ".datalog"


def downloadFullDay(*date: Union[datetime.datetime, int],
                    station: Union[str, stations.Station, List[str], List[stations.Station]]):
    """
    downloads all available files of a day
    files will be located in
    <script>/eCallistoData/<year>/<month>/<day>/

    :param date: datetime
    :param station: name-codes|Stations
    """
    date_ = config.getDateFromArgs(*date)
    station = copy.deepcopy(station)
    if not isinstance(station, list):
        station = [station]
    for i, j in enumerate(station):
        if isinstance(j, stations.Station):
            station[i] = j.name
    station = list(set(station))
    year = date_.year
    month = date_.month
    day = date_.day
    download_path = config.pathDataDay(date_)
    time_start = datetime.datetime(year, month, day)
    time_end = datetime.datetime(year, month, day, 23, 59, 59)

    data_available, stations_old = dataAvailable(date_)
    if data_available:
        for i in stations_old:
            try:
                station.remove(i)
            except ValueError:
                try:
                    station.remove(i.rstrip('-'))
                except ValueError:
                    pass
    if not os.path.exists(download_path):
        os.makedirs(download_path)

    if station:
        url_list = cal.query(time_start, time_end, station)
        cal.download(url_list, download_path)
        if data_available:
            createLog(date_, station=station, _overwrite=False)
        else:
            createLog(date_, station=station)


def downloadLastHours(station: Union[str, stations.Station, List[Union[str, stations.Station]]]):
    if not isinstance(station, list):
        station = [station]
    for i, j in enumerate(station):
        if isinstance(j, stations.Station):
            station[i] = j.name

    now = datetime.datetime.now()
    start = now - datetime.timedelta(hours=4)
    if now.day == start.day:
        download_path = config.pathDataDay(start)
        if not os.path.exists(download_path):
            os.makedirs(download_path)
        url_list = cal.query(start, now, station)
        cal.download(url_list, download_path)
    else:
        dl_path_1 = config.pathDataDay(start)
        end_1 = datetime.datetime(start.year, start.month, start.day, 23, 59)
        start_2 = datetime.datetime(now.year, now.month, now.day)
        dl_path_2 = config.pathDataDay(now)
        if not os.path.exists(dl_path_1):
            os.makedirs(dl_path_1)
        url_list = cal.query(start, end_1, station)
        cal.download(url_list, dl_path_1)

        if not os.path.exists(dl_path_2):
            os.makedirs(dl_path_2)
        url_list = cal.query(start_2, now, station)
        cal.download(url_list, dl_path_2)


def createLog(*date: datetime.datetime, station: List[str], _overwrite=True):
    """
    writes/appends a log file with the names of observatories for which data is available for a specified day

    :param date: datetime
    :param station: list[str] name-codes of observatories
    :param _overwrite: True:new log file, False:append log file
    """
    if not station:
        return
    date_ = config.getDateFromArgs(*date)
    today = datetime.datetime.today()
    if date_.year == today.year and date_.month == today.month and date_.day == today.day:
        return

    path_log = config.pathDataDay(date_)
    if _overwrite:
        with open(path_log + file_log, "w+") as datalog:
            print("1", path_log + file_log)
            print(os.path.exists(path_log + file_log))
            writeLog(datalog, path_log, station)
    else:
        with open(path_log + file_log, "a+") as datalog:
            writeLog(datalog, path_log, station)
    print("3")
    print(os.path.exists(path_log + file_log))


def writeLog(datalog: io.IOBase, path_log: str, station: List[str]):
    files = os.listdir(path_log)
    for station_ in station:
        print(station_)
        if any(file.startswith(station_ + stations.seperator) for file in files):
            datalog.write(station_ + " ")
        else:
            print("2")
            datalog.write(station_ + "- ")


def dataAvailable(*date) -> Tuple[bool, Union[None, List[str]]]:
    """
    don't call this

    call stationsAvailable() instead

    :param date: datetime, integer: year, month, day
    :return: bool, list[str] observatories for which data is available
    """
    date_ = config.getDateFromArgs(*date)

    path_log = config.pathDataDay(date_)
    if not os.path.exists(path_log):
        return False, None
    try:
        datalog = open(path_log + file_log, "r")
        station = datalog.read().split(" ")
        datalog.close()
        station.pop(-1)
        return True, station

    except FileNotFoundError:
        return False, None


def stationsAvailable(*date) -> Tuple[bool, List[str]]:
    """
    checks whether data is available for a certain day in the local folder,
    and returns the observatory names for which data was downloaded

    :param date: datetime, integer: year, month, day
    :return: bool, list[str] observatories for which data is available
    """
    date_ = config.getDateFromArgs(*date)
    data_available, station = dataAvailable(date_)
    stations_available = []
    for i in station:
        if not i.endswith('-'):
            stations_available.append(i)

    return data_available, stations_available
