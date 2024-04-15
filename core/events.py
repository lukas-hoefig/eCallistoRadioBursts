#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
 -  ROBUST  -
 - events.py -

contains low level structure and function regarding events
"""

import copy
from datetime import datetime, timedelta
import bisect
from typing import List, Union

import config

MAX_STATIONS = 8
TIME_TOLERANCE = 60    # 30
LIMIT = 0.60
DATA_POINTS_PER_SECOND = config.DATA_POINTS_PER_SECOND
BIN_FACTOR = config.BIN_FACTOR
BURST_TYPE_UNKNOWN = "???"


def header():
    return f"# Product: e-CALLISTO automated search by ROBUST\n" \
           f"# Please send comments and suggestions regarding ROBUST to lukas.hoefig(at)edu.uni-graz.at\n" \
           f"#     or for general questions, comments or suggestions: christian.monstein(at)irsol.usi.ch\n" \
           f"# Missing data: ##:##-##:##\n" \
           f"#\n" \
           f"#Date		Time		Type	Stations\n" \
           f"#-------------------------------------------------------------------------------"


# TODO remove deprecated class Time()


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

    def __str__(self, full=False):
        if not full:
            station_names = [i.name for i in self.stations]
            return f"{self.time_start.strftime(config.event_time_format_date)}\t" \
                   f"{self.time_start.strftime(config.event_time_format_short)}-{self.time_end.strftime(config.event_time_format_short)}\t" \
                   f"{self.burst_type}\t{', '.join(station_names)}"
        else:
            return str([self.burst_type, self.time_start, self.time_end, f"{self.probability:.4f}"])

    def __repr__(self):
        return self.__str__()

    def setTimeEnd(self, time: datetime):
        self.time_end = Time(time.year, time.month, time.day, time.hour, time.minute, time.second)

    def __eq__(self, other):
        delta_start = abs((self.time_start - other.time_start).total_seconds())
        delta_end = abs((self.time_end - other.time_end).total_seconds())
        delta_e1s2 = abs((self.time_end - other.time_start).total_seconds())
        delta_e2s1 = abs((self.time_start - other.time_end).total_seconds())

        return min(delta_start, delta_end, delta_e1s2, delta_e2s1) < timedelta(seconds=TIME_TOLERANCE).total_seconds() \
            or (self.time_start < other.time_start and self.time_end > other.time_end) \
            or (other.time_start < self.time_start and other.time_end > self.time_end)

    def __lt__(self, other):
        return self.time_start < other.time_start and self != other

    def __add__(self, other):
        return EventList([self, other], self.time_start)

    def __iadd__(self, other):
        return self.__add__(other)

    def merge(self, other):
        if self != other:
            raise AttributeError
        self.probability = max(self.probability, other.probability)
        self.stations.extend(other.stations)
        self.stations = sorted(set(self.stations))
        self.time_start = min(self.time_start, self.time_start)         # TODO either change this is lower tolerance
        self.time_end = max(self.time_end, other.time_end)

    def inList(self, _list):                                            # TODO add tolerance
        i = bisect.bisect_left(_list, self)
        return i != len(_list) and _list[i] == self

    def positionInList(self, _list):
        i = bisect.bisect_left(_list, self)
        if i != len(_list) and _list[i] == self:
            return i
        return -1


class EventList:
    def __init__(self, events: Union[Event, List[Event]], *date):
        self.events = []
        self.date = config.getDateFromArgs(*date)
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

        if isinstance(other, EventList):
            temp = copy.deepcopy(self)
            for i in other.events:
                temp = temp.__radd__(i)
            return temp

    def __radd__(self, other):
        temp = copy.deepcopy(self)
        if other is None:
            return temp

        if not isinstance(other, Event):
            print(type(other))
            raise TypeError("Wrong Type, should be Event")

        if not other.inList(self):
            bisect.insort(self.events, other)
        else:
            self.events[other.positionInList(temp)].merge(other)
        return self

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

    def insert(self, index, other):
        if isinstance(other, Event):
            self.events.insert(index, other)
        else:
            raise TypeError

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        if self:
            str_ = [i.__str__() for i in self.events]
            return "\n".join(str_)
        else:
            return f"{self.date.strftime(config.event_time_format_date)}\t##:##-##:##"

    def sort(self):
        self.events = sorted(self.events, key=lambda event: event.time_start)


def includes(event_list: EventList, event: Event) -> bool:
    for i in event_list:
        if i.inList(EventList(event, event.time_start)):
            return True
    return False
