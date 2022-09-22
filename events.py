#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import copy
from datetime import datetime, timedelta

from typing import List, Union

import const

MAX_STATIONS = 3
TIME_TOLERANCE = 60
LIMIT = 0.70
DATA_POINTS_PER_SECOND = const.DATA_POINTS_PER_SECOND
BIN_FACTOR = const.BIN_FACTOR
BURST_TYPE_UNKNOWN = "???"

# TODO -> datetime, not str


class Time(datetime):
    def __str__(self):
        return f"{self.hour:02}:{self.minute:02}:{self.second:02}"

    def __repr__(self):
        return self.__str__()


def time(datetime_: datetime):
    return Time(datetime_.year, datetime_.month, datetime_.day, 
                datetime_.hour, datetime_.minute, datetime_.second)


class Event:
    """
    """

    def __init__(self, start_time: datetime, end_time=None, probability=1., burst_type=BURST_TYPE_UNKNOWN,
                 stations=None):
        if stations is None:
            stations = []
        self.time_start = Time(start_time.year, start_time.month, start_time.day, start_time.hour,
                               start_time.minute, start_time.second)
        self.time_end = Time(start_time.year, start_time.month, start_time.day, start_time.hour, start_time.minute,
                             start_time.second)
        if end_time is not None:
            self.time_end = Time(end_time.year, end_time.month, end_time.day, end_time.hour, end_time.minute,
                                 end_time.second)
        self.burst_type = burst_type
        self.probability = probability
        self.stations = stations

    def __str__(self):
        return str([self.burst_type, self.time_start, self.time_end, f"{self.probability:.4f}"])

    def __repr__(self):
        return self.__str__()

    def setTimeEnd(self, time: datetime):
        self.time_end = Time(time.year, time.month, time.day, time.hour, time.minute, time.second)

    def compare(self, other):
        return min(abs(self.time_end - other.time_start).total_seconds(),
                   abs(self.time_start - other.time_end).total_seconds(),
                   abs(self.time_start - other.time_start).total_seconds()) < \
                   timedelta(seconds=TIME_TOLERANCE).total_seconds() or \
                   (self.time_start < other.time_start and self.time_end > other.time_end) or \
                   (other.time_start < self.time_start and other.time_end > self.time_end)

    def __eq__(self, other):
        return self.compare(other)

    def __add__(self, other):
        return EventList([self, other])

    def __iadd__(self, other):
        return self.__add__(other)

    def inList(self, _list):
        for i in range(len(_list)):
            if self.compare(_list[i]):
                return True, i
        return False


class EventList:
    def __init__(self, events: Union[Event, List[Event]]):
        self.events = []
        if isinstance(events, Event):
            self.events = [events]
        elif isinstance(events, list):
            self.events = events

    def __getitem__(self, item):
        return self.events[item]

    def __len__(self):
        return len(self.events)

    def __bool__(self):
        return bool(self.__len__())

    def __add__(self, other):
        if isinstance(other, Event):
            return self.__radd__(other)

        temp = copy.deepcopy(self)
        for i in other.events:
            if not i.inList(temp.events):
                temp.events.append(i)
            else:
                if i.probability >= temp.events[i.inList(temp.events)[1]].probability:
                    temp.events[i.inList(temp.events)[1]].probability = i.probability
                    
                    for j in i.stations:
                        if j not in temp.events[i.inList(temp.events)[1]].stations and \
                                    len(temp.events[i.inList(temp.events)[1]].stations) >= MAX_STATIONS:
                            temp.events[i.inList(temp.events)[1]].stations.pop(0)
                        temp.events[i.inList(temp.events)[1]].stations.append(j)
                else:
                    for j in i.stations:
                        if j not in temp.events[i.inList(temp.events)[1]].stations and \
                                    len(temp.events[i.inList(temp.events)[1]].stations) >= MAX_STATIONS:
                            temp.events[i.inList(temp.events)[1]].stations.append(j)
                temp.events[i.inList(temp.events)[1]].stations = list(set(temp.events[i.inList(temp.events)[1]].stations))
        return temp

    def __radd__(self, other):
        temp = copy.deepcopy(self)
        if not isinstance(other, Event):
            raise TypeError

        if not other.inList(temp.events):
            temp.events.append(other)
        else:
            if other.probability >= temp.events[other.inList(temp.events)[1]].probability:
                temp.events[other.inList(temp.events)[1]].probability = other.probability
            
                for j in other.stations:
                    if j not in temp.events[other.inList(temp.events)[1]].stations and \
                                        len(temp.events[other.inList(temp.events)[1]].stations) >= MAX_STATIONS:
                        temp.events[other.inList(temp.events)[1]].stations.pop(0)
                    temp.events[other.inList(temp.events)[1]].stations.append(j)
            else:
                for j in other.stations:
                    if j not in temp.events[other.inList(temp.events)[1]].stations and \
                                len(temp.events[other.inList(temp.events)[1]].stations) >= MAX_STATIONS:
                        temp.events[other.inList(temp.events)[1]].stations.append(j)
        return temp

    def __sub__(self, other):
        temp = copy.deepcopy(self)
        if isinstance(other, Event):
            return self.__rsub__(other)
        for i in other:
            if i.inList(temp.events):
                temp.events.remove(i)
        return temp

    def __rsub__(self, other):
        temp = copy.deepcopy(self)
        if not isinstance(other, Event):
            raise TypeError
        if other.inList(temp.events):
            temp.events.remove(other)
        return temp

    def __iadd__(self, other):
        if isinstance(other, Event):
            return self.__radd__(other)
        return self.__add__(other)

    def __isub__(self, other):
        if isinstance(other, Event):
            return self.__rsub__(other)
        return self.__sub__(other)

    def __repr__(self):
        return str(self.events)

    def __str__(self):
        return self.__repr__()

    def sort(self):
        self.events = sorted(self.events, key=lambda event: event.time_start)
