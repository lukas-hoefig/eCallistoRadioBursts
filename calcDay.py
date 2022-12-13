#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import sys

import steps
import analysis


if __name__ == '__main__':
    """
    args: year month day #days 
    """
    input_arg = sys.argv
    args = [2022, 1, 1, 1]
    if input_arg and len(input_arg) > 2:
        for i, j in enumerate(input_arg[1:]):
            args[i] = int(j)

    date_start = datetime.datetime(args[0], args[1], args[2])

    for i in range(0, args[3]):
        date = date_start + datetime.timedelta(days=i)

        data_raw = steps.dataSetDay(date)
        data_step_1 = steps.firstStep(date, data_sets=data_raw, mask_frq=True)
        analysis.saveData(date, event_list=data_step_1, step=1)

        data_step_2 = steps.secondStep(None, date)
        analysis.saveData(date, event_list=data_step_2, step=2)

        data_step_3 = steps.thirdStep(None, date)
        analysis.saveData(date, event_list=data_step_3, step=3)

        data_step_4 = steps.fourthStep(None, date)
        analysis.saveData(date, event_list=data_step_4, step=4)
