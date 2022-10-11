#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import radiospectra.sources.callisto as cal
import os
import copy

from typing import List, Union, Tuple

import const
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
    date_ = const.getDateFromArgs(*date)
    station = copy.deepcopy(station)
    if not isinstance(station, list):
        station = [station]
    for i in range(len(station)):
        if isinstance(station[i], stations.Station):
            station[i] = station[i].name

    year = date_.year
    month = date_.month
    day = date_.day
    download_path = const.pathDataDay(date_)
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


def createLog(*date: datetime.datetime, station: List[str], _overwrite=True):
    """
    writes/appends a log file with the names of observatories for which data is available for a specified day

    :param date: datetime
    :param station: list[str] name-codes of observatories
    :param _overwrite: True:new log file, False:append log file
    """
    if not station:
        return
    date_ = const.getDateFromArgs(*date)
    today = datetime.datetime.today()
    if date_.year == today.hour and date_.month == today.month and date_.day == today.day:
        return

    path_log = const.pathDataDay(date_)
    if _overwrite:
        datalog = open(path_log + file_log, 'w')
    else:
        datalog = open(path_log + file_log, "a")
    files = os.listdir(path_log)
    for station in station:
        if any(file.startswith(station) for file in files):
            datalog.write(station + " ")
        else:
            datalog.write(station + "- ")
    datalog.close()


def dataAvailable(*date) -> Tuple[bool, Union[None, List[str]]]:
    """
    don't call this

    call stationsAvailable() instead

    :param date: datetime, integer: year, month, day
    :return: bool, list[str] observatories for which data is available
    """
    date_ = const.getDateFromArgs(*date)

    path_log = const.pathDataDay(date_)
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
    date_ = const.getDateFromArgs(*date)
    data_available, station = dataAvailable(date_)
    stations_available = []
    for i in station:
        if not i.endswith('-'):
            stations_available.append(i)

    return data_available, stations_available
