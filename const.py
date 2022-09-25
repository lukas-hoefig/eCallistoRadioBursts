#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import matplotlib.pyplot as plt
import datetime

path_script = os.getcwd().replace("\\", "/") + "/"
path_data = "eCallistoData/"
path_plots = "eCallistoPlots/"
file_ending = ".fit.gz"
e_callisto_url = 'http://soleil.i4ds.ch/solarradio/data/2002-20yy_Callisto/'
DATA_POINTS_PER_SECOND = 4
LENGTH_FILES_MINUTES = 15
BIN_FACTOR = 4
ROLL_WINDOW = 180
even_time_format = "%H:%M:%S"
plot_colors = ['blue', 'red', 'purple', 'green', 'yellow']

frq_limit_low = 50.
frq_limit_high = 900.
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


def pathDataDay(*args):
    """
    creates string for the data paths <script>/eCallistoData/<year>/<month>/<day>/

    :param args: datetime, integer: year, month, day
    :return:
    """
    if isinstance(args[0], datetime.datetime):
        year = args[0].year
        month = args[0].month
        day = args[0].day
    elif len(args) > 2:
        for i in args:
            if not isinstance(i, int):
                raise ValueError("Arguments should be datetime or Integer")
        year = args[0]
        month = args[1]
        day = args[2]
    else:
        raise ValueError("Arguments should be datetime or multiple Integer as year, month, day")
    return path_script + path_data + f"{year}/{month:02}/{day:02}/"


setupMatPlotLib()
