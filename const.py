#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

path_script = os.getcwd().replace("\\", "/") + "/"
path_data = "eCallistoData/"
path_plots = "eCallistoPlots/"
DATA_POINTS_PER_SECOND = 4
BIN_FACTOR = 4
ROLL_WINDOW = 180

plot_colors = ['blue', 'red', 'purple', 'green', 'yellow']


def pathDataDay(year: int, month: int, day: int):
    """
    creates string for the data paths <script>/eCallistoData/<year>/<month>/<day>/

    :param year:
    :param month:
    :param day:
    :return:
    """
    return path_script + path_data + '{}/{}/{}/'.format(str(year), str(month).zfill(2), str(day).zfill(2))
