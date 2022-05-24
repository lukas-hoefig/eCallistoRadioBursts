#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime

import const
import analysis

path_data = const.path_data
reference_header_length = 12


def referenceFileName(year, month, day, next_folder=False):
    return path_data + "/reference/{}_events/{}{}{}events.txt".format(str(year + next_folder), str(year),
                                                                      str(month).zfill(2), str(day).zfill(2))


def reference(year, month, day):
    try:
        file = referenceFileName(year, month, day)
        f = open(file)
    except FileNotFoundError:
        file = referenceFileName(year, month, day, next_folder=True)
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

    lines = list(filter(lambda i: i[6] == 'RSP', lines))

    references = []
    for line in lines:
        start_hour = int(line[1][:2])
        start_minute = int(line[1][2:])
        end_hour = int(line[3][:2])
        end_minute = int(line[3][2:])
        b_type = line[8].rsplit('/')[0]
        event = analysis.Event(datetime(year, month, day, start_hour, start_minute),
                               end_time=datetime(year, month, day, end_hour, end_minute), burst_type=b_type)
        references.append(event)
    return references
