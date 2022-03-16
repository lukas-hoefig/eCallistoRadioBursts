#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import data
import observatories
import const


LIMIT = 0.70
DATA_POINTS_PER_SECOND = eCallistoConst.DATA_POINTS_PER_SECOND
BIN_FACTOR = eCallistoConst.BIN_FACTOR


class Correlation:
    def __init__(data_point_1: eCallistoData.DataPoint, data_point_2: eCallistoData.DataPoint,
                 _no_background: bool, _bin_freq: bool, _bin_time: bool, _flatten: bool, 
                 _bin_time_width: int, _flatten_window: int, _r_window, _plot=False):
        pass

