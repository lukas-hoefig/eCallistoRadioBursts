#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
import urllib

import const
import events
import stations

path_data = const.path_data
reference_header_length = 12


def fileNameSWPC(year, month, day, next_folder=False):
    return f"{path_data}reference/{year + next_folder}_events/{year}{str(month).zfill(2)}{str(day).zfill(2)}events.txt"


def listSWPC(year, month, day):
    try:
        file = fileNameSWPC(year, month, day)
        f = open(file)
    except FileNotFoundError:
        file = fileNameSWPC(year, month, day, next_folder=True)
        f = open(file)
    lines_read = f.readlines()
    lines = []
    f.close()
    lines_read = lines_read[reference_header_length:]

    for line in lines_read:
        if line == '\n':
            lines_read.remove(line)

    for line in range(len(lines_read)):
        lines.append(lines_read[line].rsplit(' '))
        lines[line] = list(filter(None, lines[line]))
        try:
            lines[line].remove('+')
        except ValueError:
            pass

    lines = list(filter(lambda i: i[6] == 'RSP' and not i[8].startswith('CTM'), lines))

    references = []
    for line in lines:
        start_hour = int(line[1][:2])
        start_minute = int(line[1][2:])
        end_hour = int(line[3][:2])
        end_minute = int(line[3][2:])
        b_type = line[8]
        event = events.Event(datetime(year, month, day, start_hour, start_minute),
                             end_time=datetime(year, month, day, end_hour, end_minute), burst_type=b_type)
        references.append(event)
    return events.EventList(references)


def urlMonstein(year: int, month: int):
    year = str(year)
    month = str(month).zfill(2)
    return f"http://soleil.i4ds.ch/solarradio/data/BurstLists/2010-yyyy_Monstein/{year}/e-CALLISTO_{year}_{month}.txt"


def fileNameMonstein(year, month):
    return f"{path_data}reference/{str(year)}_monstein/{str(year)}{str(month).zfill(2)}events.txt"


def listMonstein(year: int, month: int, day: int):
    """
    TODO: download txt , check if file exist, only then check url
    """
    url = urlMonstein(year, month)
    file = urllib.request.urlopen(url)
    event_list = events.EventList([])
    for line in file:
        decoded_line = line.decode("utf-8").rstrip("\n")
        if decoded_line.startswith(str(year)):
            dat = decoded_line.rsplit("\t")
            if not dat[1].startswith("#"):
                _year = int(dat[0][:4])
                _month = int(dat[0][4:6])
                _day = int(dat[0][6:8])
                if _day != day:
                    continue
                _times = dat[1].rsplit("-")
                _time_start = datetime(year=_year, month=_month, day=_day, hour=int(_times[0][:2]), minute=int(_times[0][3:5]))
                _time_end = datetime(year=_year, month=_month, day=_day, hour=int(_times[1][:2]), minute=int(_times[1][3:5]))
                _type = dat[2]
                if _type == "CTM":
                    continue
                _stations = dat[3].rsplit(", ")
                _observatories = []
                for i in _stations:
                    try:
                        _observatories.append(observatories.observatory_dict[i])        # TODO
                    except KeyError:
                        pass
                event = events.Event(_time_start, end_time=_time_end, stations=_observatories, burst_type=_type)
                event_list += event
    return event_list


def listMonstein2orMore(year: int, month: int, day: int):
    url = urlMonstein(year, month)
    file = urllib.request.urlopen(url)
    event_list = events.EventList([])
    for line in file:
        decoded_line = line.decode("utf-8").rstrip("\n")
        if decoded_line.startswith(str(year)):
            dat = decoded_line.rsplit("\t")
            if not dat[1].startswith("#"):
                _year = int(dat[0][:4])
                _month = int(dat[0][4:6])
                _day = int(dat[0][6:8])
                if _day != day:
                    continue
                _times = dat[1].rsplit("-")
                _time_start = datetime(year=_year, month=_month, day=_day, hour=int(_times[0][:2]), minute=int(_times[0][3:5]))
                _time_end = datetime(year=_year, month=_month, day=_day, hour=int(_times[1][:2]), minute=int(_times[1][3:5]))
                _type = dat[2]
                _stations = dat[3].rsplit(", ")
                _observatories = []
                for i in _stations:
                    try:
                        _observatories.append(observatories.observatory_dict[i])        # TODO
                    except KeyError:
                        pass
                if len(_observatories) < 2:
                    continue
                event = events.Event(_time_start, end_time=_time_end, stations=_observatories, burst_type=_type)
                event_list += event
    return event_list
