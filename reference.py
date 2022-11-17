#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
import urllib

import config
import events
import stations

path_data = config.path_data
reference_header_length = 12


def fileNameSWPC(*date, next_folder=False):
    date_ = config.getDateFromArgs(*date)
    return f"{path_data}reference/{date_.year + next_folder}_events/" \
           f"{date_.year}{date_.month:02}{date_.day:02}events.txt"


def listSWPC(*date):
    date_ = config.getDateFromArgs(*date)
    try:
        file = fileNameSWPC(date_)
        f = open(file)
    except FileNotFoundError:
        file = fileNameSWPC(date_, next_folder=True)
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
    try:
        lines = list(filter(lambda i: i[6] == 'RSP' and not i[8].startswith('CTM'), lines))
    except IndexError:
        return events.EventList([], date_)
    references = []
    for line in lines:
        start_hour = int(line[1][:2])
        start_minute = int(line[1][2:])
        end_hour = int(line[3][:2])
        end_minute = int(line[3][2:])
        b_type = line[8]
        event = events.Event(datetime(date_.year, date_.month, date_.day, start_hour, start_minute),
                             end_time=datetime(date_.year, date_.month, date_.day, end_hour, end_minute),
                             burst_type=b_type)
        references.append(event)
    return events.EventList(references, date_)


def urlMonstein(*date):
    date_ = config.getDateFromArgs(*date)
    return f"http://soleil.i4ds.ch/solarradio/data/BurstLists/2010-yyyy_Monstein/" \
           f"{date_.year}/e-CALLISTO_{date_.year}_{date_.month:02}.txt"


def fileNameMonstein(*date):
    date_ = config.getDateFromArgs(*date)
    return f"{path_data}reference/{date_.year}_monstein/{date_.year}{date_.month:02}events.txt"


def listMonstein(*date):
    """
    TODO: download txt , check if file exist, only then check url

    TODO: skip entries with typos -> raise warning, print line
    """
    date_ = config.getDateFromArgs(*date)
    url = urlMonstein(*date)
    file = urllib.request.urlopen(url)
    event_list = events.EventList([], date_)
    for line in file:
        decoded_line = line.decode("utf-8").rstrip("\n")
        if decoded_line.startswith(str(date_.year)):
            dat = decoded_line.rsplit("\t")
            if not dat[1].startswith("#"):
                _year = int(dat[0][:4])
                _month = int(dat[0][4:6])
                _day = int(dat[0][6:8])
                if _day != date_.day:
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
                        _observatories.append(stations.Station(i))        # TODO - where from
                    except KeyError:
                        pass
                event = events.Event(_time_start, end_time=_time_end, stations=_observatories, burst_type=_type)
                event_list += event
    return event_list


def listMonstein2orMore(*date):
    date_ = config.getDateFromArgs(*date)
    url = urlMonstein(*date)
    file = urllib.request.urlopen(url)
    event_list = events.EventList([], date_)
    for line in file:
        decoded_line = line.decode("utf-8").rstrip("\n")
        if decoded_line.startswith(str(date_.year)):
            dat = decoded_line.rsplit("\t")
            if not dat[1].startswith("#"):
                _year = int(dat[0][:4])
                _month = int(dat[0][4:6])
                _day = int(dat[0][6:8])
                if _day != date_.day:
                    continue
                _times = dat[1].rsplit("-")
                _time_start = datetime(year=_year, month=_month, day=_day, hour=int(_times[0][:2]), minute=int(_times[0][3:5]))
                _time_end = datetime(year=_year, month=_month, day=_day, hour=int(_times[1][:2]), minute=int(_times[1][3:5]))
                _type = dat[2]
                _stations = dat[3].rsplit(", ")
                _observatories = []
                for i in _stations:
                    try:
                        _observatories.append(stations.Station(i))         # TODO
                    except KeyError:
                        pass
                if len(_observatories) < 2:
                    continue
                event = events.Event(_time_start, end_time=_time_end, stations=_observatories, burst_type=_type)
                event_list += event
    return event_list
