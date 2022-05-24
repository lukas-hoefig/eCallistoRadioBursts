#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import copy
from datetime import datetime, timedelta

from typing import List, Union

import data
import observatories
import const

TIME_TOLERANCE = 60
LIMIT = 0.70
DATA_POINTS_PER_SECOND = const.DATA_POINTS_PER_SECOND
BIN_FACTOR = const.BIN_FACTOR
BURST_TYPE_UNKNOWN = "???"

#    for file in files_observatory:
#        data_day.append(data.DataPoint(file))  # try except |error -> TRIEST_20210906_234530_57.fit   TODO
#    return data_day


class Time(datetime):
    def __str__(self):
        return "{}:{}:{}".format(str(self.hour).zfill(2), str(self.minute).zfill(2), str(self.second).zfill(2))

    def __repr__(self):
        return self.__str__()


class Event:
    """
    TODO observatories
    """

    def __init__(self, start_time: datetime, end_time=None, probability=1., burst_type=BURST_TYPE_UNKNOWN):
        self.time_start = Time(start_time.year, start_time.month, start_time.day, start_time.hour,
                               start_time.minute, start_time.second)
        self.time_end = Time(start_time.year, start_time.month, start_time.day, start_time.hour, start_time.minute,
                             start_time.second)
        if end_time is not None:
            self.time_end = Time(end_time.year, end_time.month, end_time.day, end_time.hour, end_time.minute,
                                 end_time.second)
        self.burst_type = burst_type
        self.probability = probability

    def __str__(self):
        return str([self.burst_type, self.time_start, self.time_end, f"{self.probability:.4f}"])

    def __repr__(self):
        return self.__str__()

    def compare(self, other):
        return min(abs(self.time_end - other.time_start).total_seconds(),
                   abs(self.time_start - other.time_end).total_seconds()) < \
                   timedelta(seconds=TIME_TOLERANCE).total_seconds()

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

    def __add__(self, other):  # TODO add observatories of all involved
        if isinstance(other, Event):
            return self.__radd__(other)

        temp = copy.deepcopy(self)
        for i in other.events:
            if not i.inList(temp.events):
                temp.events.append(i)
            else:
                temp.events[i.inList(temp.events)[1]].probability = \
                    max(temp.events[i.inList(temp.events)[1]].probability, i.probability)
        return temp

    def __radd__(self, other):
        temp = copy.deepcopy(self)
        if not isinstance(other, Event):
            raise TypeError

        if not other.inList(temp.events):
            temp.events.append(other)
        else:
            temp.events[other.inList(temp.events)[1]].probability = \
                max(temp.events[other.inList(temp.events)[1]].probability, other.probability)
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
