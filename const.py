#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import matplotlib.pyplot as plt

path_script = os.getcwd().replace("\\", "/") + "/"
path_data = "eCallistoData/"
path_plots = "eCallistoPlots/"
DATA_POINTS_PER_SECOND = 4
LENGTH_FILES_MINUTES = 15
BIN_FACTOR = 4
ROLL_WINDOW = 180
even_time_format = "%H:%M:%S"
plot_colors = ['blue', 'red', 'purple', 'green', 'yellow']
spectral_range = [45, 81]


def setupMatPlotLib():
    # Properties to control fontsizes in plots
    small_size = 14
    medium_size = 18
    bigger_size = 16

    plt.rc('font', size=small_size)  # controls default text sizes
    plt.rc('axes', titlesize=bigger_size)  # fontsize of the axes title
    plt.rc('axes', labelsize=medium_size)  # fontsize of the x and y labels
    plt.rc('xtick', labelsize=small_size)  # fontsize of the tick labels
    plt.rc('ytick', labelsize=medium_size)  # fontsize of the tick labels
    plt.rc('legend', fontsize=small_size)  # legend fontsize
    plt.rc('figure', titlesize=bigger_size)  # fontsize of the figure title


def getColor():
    getColor.counter = (getColor.counter + 1) % len(plot_colors)
    return plot_colors[getColor.counter]


getColor.counter = 0


def pathDataDay(year: int, month: int, day: int):
    """
    creates string for the data paths <script>/eCallistoData/<year>/<month>/<day>/

    :param year:
    :param month:
    :param day:
    :return:
    """
    return path_script + path_data + '{}/{}/{}/'.format(str(year), str(month).zfill(2), str(day).zfill(2))


setupMatPlotLib()
