#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import radiospectra.sources.callisto as cal
import os
import copy

from typing import List, Union, Tuple

import const
import stations

path_script = const.path_script
path_data = const.path_data
file_log = ".datalog"

# _date -> *date, _stations - > stations
def downloadFullDay(*date: Union[datetime.datetime, int],
                    station: Union[str, stations.Station, List[str], List[stations.Station]]):
    """
    downloads all available files of a day
    files will be located in
    <script>/eCallistoData/<year>/<month>/<day>/

    :param _date: datetime
    :param _stations: name-codes|Stations
    """

    if isinstance(date[0], datetime.datetime):
        date = date[0]
    elif len(date) > 2:
        for i in date:
            if not isinstance(i, int):
                raise ValueError("Arguments should be datetime or Integer")
        year = date[0]
        month = date[1]
        day = date[2]
        date = datetime.datetime(year, month, day)
    else:
        raise ValueError("Arguments should be datetime or multiple Integer as year, month, day")
    
    station = copy.deepcopy(station)
    if not isinstance(station, list):
        station = [station]
    for i in range(len(station)):
        if isinstance(station[i], stations.Station):
            station[i] = station[i].name
    year = date.year
    month = date.month
    day = date.day
    download_path = const.pathDataDay(year, month, day)
    time_start = datetime.datetime(year, month, day)
    time_end = datetime.datetime(year, month, day, 23, 59, 59)

    data_available, stations_old = dataAvailable(year, month, day)
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
            createLog(date, station, _overwrite=False)
        else:
            createLog(date, station)


def createLog(_date: datetime.datetime, _stations: List[str], _overwrite=True):
    """
    writes/appends a log file with the names of observatories for which data is available for a specified day

    :param _date: datetime
    :param _stations: list[str] name-codes of observatories
    :param _overwrite: True:new log file, False:append log file
    """
    if not _stations:
        return
    if _date == datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0):
        return

    path_log = const.pathDataDay(_date)
    if _overwrite:
        datalog = open(path_log + file_log, 'w')
    else:
        datalog = open(path_log + file_log, "a")
    files = os.listdir(path_log)
    for station in _stations:
        if any(file.startswith(station) for file in files):
            datalog.write(station + " ")
        else:
            datalog.write(station + "- ")
    datalog.close()


def dataAvailable(*args) -> Tuple[bool, List[str]]:
    """
    don't call this
    call stationsAvailable() instead

    :param args: datetime, integer: year, month, day
    :return: bool, list[str] observatories for which data is available
    """
    if isinstance(args[0], datetime.datetime):
        year = args[0].year
        month = args[0].month
        day = args[0].day
    elif len(args) > 2:
        for i in args:
            if not isinstance(i, int):
                raise ValueError("Arguments should be datetime or Integer")
        year = args[0]
        month = args[1]
        day = args[2]
    else:
        raise ValueError("Arguments should be datetime or multiple Integer as year, month, day")

    path_log = const.pathDataDay(year, month, day)
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


def stationsAvailable(*args) -> Tuple[bool, List[str]]:
    """
    checks whether data is available for a certain day in the local folder,
    and returns the observatory names for which data was downloaded

    :param args: datetime, integer: year, month, day
    :return: bool, list[str] observatories for which data is available
    """
    if isinstance(args[0], datetime.datetime):
        year = args[0].year
        month = args[0].month
        day = args[0].day
    elif len(args) > 2:
        for i in args:
            if not isinstance(i, int):
                raise ValueError("Arguments should be datetime or Integer")
        year = args[0]
        month = args[1]
        day = args[2]
    else:
        raise ValueError("Arguments should be datetime or multiple Integer as year, month, day")

    date = datetime.datetime(year, month, day)
    data_available, station = dataAvailable(date)
    stations_available = []
    for i in station:
        if not i.endswith('-'):
            stations_available.append(i)

    return data_available, stations_available
