#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime as dt
import radiospectra.sources.callisto as cal
import os
import copy

from typing import List

import const
import observatories as obs

path_script = const.path_script
path_data = const.path_data
date_format = "%Y %m %d %H %M %S"
file_log = ".datalog"


def downloadFullDay(_year: int, _month: int, _day: int, _observatories: List[str]):
    """
    downloads all available files of a day for all instruments defined in eCallistoData.py
    files will be located in
    <script>/eCallistoData/<year>/<month>/<day>/

    :param _observatories: [str] or [list[str]] name-codes of observatories
    :param _year:
    :param _month:
    :param _day:
    """
    _observatories = copy.copy(_observatories)
    if type(_observatories) == str:
        _observatories = [_observatories]

    download_path = const.pathDataDay(_year, _month, _day)
    hour_start = minute_start = second_start = "00"
    hour_end = "23"
    minute_end = second_end = "59"
    time_start = dt.strptime(str(_year) + " " + str(_month) + " " + str(_day) + " "
                             + hour_start + " " + minute_start + " " + second_start, date_format)
    time_end = dt.strptime(str(_year) + " " + str(_month) + " " + str(_day) + " "
                           + hour_end + " " + minute_end + " " + second_end, date_format)

    data_available, observatories_old = dataAvailable(_year, _month, _day)
    if data_available:
        for observatory in observatories_old:
            try:
                _observatories.remove(observatory)
            except ValueError:
                try:
                    _observatories.remove(observatory.rstrip('-'))
                except ValueError:
                    pass
    if not os.path.exists(download_path):
        os.makedirs(download_path)

    if _observatories:
        url_list = cal.query(time_start, time_end, _observatories)
        cal.download(url_list, download_path)
        if data_available:
            createLog(_year, _month, _day, _observatories, _overwrite=False)
        else:
            createLog(_year, _month, _day, _observatories)


def createLog(_year: int, _month: int, _day: int, _observatories: List[str], _overwrite=True):
    """
    writes/appends a log file with the names of observatories for which data is available for a specified day

    TODO: don't create file if day == today

    :param _year:
    :param _month:
    :param _day:
    :param _observatories: list[str] name-codes of observatories
    :param _overwrite: True:new log file, False:append log file
    """
    if not len(_observatories):
        return

    path_log = const.pathDataDay(_year, _month, _day)
    if _overwrite:
        datalog = open(path_log + file_log, 'w')
    else:
        datalog = open(path_log + file_log, "a")
    files = os.listdir(path_log)
    for observatory in _observatories:
        if any(file.startswith(observatory) for file in files):
            datalog.write(observatory + " ")
        else:
            datalog.write(observatory + "- ")
    datalog.close()


def dataAvailable(_year: int, _month: int, _day: int):
    """
    checks whether data is available for a certain day in the local folder,
    and returns the observatory names for which data was downloaded

    :param _year:
    :param _month:
    :param _day:
    :return: bool, list[str] observatories for which data is available
    """
    path_log = const.pathDataDay(_year, _month, _day)
    if not os.path.exists(path_log):
        return False, None
    try:
        datalog = open(path_log + file_log, "r")
        observatories = datalog.read().split(" ")
        datalog.close()
        observatories.pop(-1)
        return True, observatories

    except FileNotFoundError:
        return False, None


def observatoriesAvailable(_year, _month, _day):
    data_available, observatories = dataAvailable(_year, _month, _day)
    observatories_available = []
    for i in observatories:
        if not i.endswith('-'):
            observatories_available.append(obs.observatory_dict[i])

    return data_available, observatories_available
