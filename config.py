#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Paths, names, constants needed in several scripts

:authors: 	Lukas Höfig
:contact: 	lukas.hoefig@edu.uni-graz.at
:date:       27.09.2022
"""


import warnings
import os
import matplotlib.pyplot as plt
import datetime

warnings.simplefilter("ignore", UserWarning)


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


def getDateFromArgs(*date):
    """
    returns a datetime object from any combination of input parameters

    :param date: datetime, str, ints
    :return: datetime object
    """
    if isinstance(date, datetime.datetime):
        date_ = date
    elif isinstance(date[0], datetime.datetime):
        date_ = date[0]
    elif len(date) > 2:
        param = [2000, 1, 1, 0, 0, 0]
        for i, j in enumerate(date):
            param[i] = int(j)
        year = param[0]
        month = param[1]
        day = param[2]
        hour = param[3]
        minute = param[4]
        second = param[5]
        date_ = datetime.datetime(year, month, day, hour, minute, second)
    else:
        raise ValueError("Arguments should be datetime, Integer or convertible to Integer")
    return date_


def pathDataDay(*date):
    """
    creates string for the data paths <script>/eCallistoData/<year>/<month>/<day>/

    :param date: datetime, integer: year, month, day
    :return:
    """
    date_ = getDateFromArgs(*date)
    return path_data + pathDay(date_)


def pathDay(*date):
    date_ = getDateFromArgs(*date)
    return f"{date_.year}/{date_.month:02}/{date_.day:02}/"


def getPathScript():
    path_file = os.path.abspath(__file__).replace("\\", "/")
    pos = path_file.rfind("/")
    path = path_file[:pos + 1]
    return path


path_script = getPathScript()
path_data = path_script + "eCallistoData/"                # "C:/Users/14hoefig/data/eCallisto/"                   #  "eCallistoData/"
path_realtime = path_data + "realtime/"
path_results = path_script + "results/"
path_plots = "eCallistoPlots/"
file_type = ".fit"
file_type_zip = ".fit.gz"
file_ending = file_type_zip
e_callisto_url = 'http://soleil.i4ds.ch/solarradio/data/2002-20yy_Callisto/'
DATA_POINTS_PER_SECOND = 4
LENGTH_FILES_MINUTES = 15
BIN_FACTOR = 4
ROLL_WINDOW = 180
event_time_format = "%H:%M:%S"
event_time_format_short = "%H:%M"
event_time_format_date = "%Y%m%d"
plot_colors = ['blue', 'red', 'purple', 'green', 'yellow']

frq_limit_low_upper = 50.
frq_limit_high_upper = 220.
frq_limit_low_lower = 1.
frq_limit_high_lower = 70.

setupMatPlotLib()
