#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import sys
import os 

sys.path.append(os.path.join(os.path.dirname("."), "core"))

import steps
import analysis
import config
import calcTimeP


step_1 = 1
step_2 = 2
step_3 = 3



if __name__ == '__main__':
    """
    ARGS:
    year month day 
    """
    input_arg = sys.argv

    date_start = datetime.datetime(int(input_arg[1]), int(input_arg[2]), int(input_arg[3]))
    date = date_start
    while date <= calcTimeP.date_end:
        print(date)
        # TODO: move this to steps -> skip calc if file already exists, with debug/overwrite parameter to calc anyways
        if not os.path.exists(analysis.filename(date, step=step_1)):
            data_raw = steps.dataSetDay(date, run=True, eu_ut=True)
            data_step_1 = steps.firstStep(date, data_sets=data_raw,
                                          limit=config.correlation_start, r_w=200, nobg=True, mask_frq=False,
                                          flatten=True, flatten_w=500,
                                          bin_t=False, bin_t_w=4)
            analysis.saveData(date, step=step_1, event_list=data_step_1)
        date = date + datetime.timedelta(days=calcTimeP.cores)

        # data_step_2 = steps.secondStep(None, date)
        # analysis.saveData(date, event_list=data_step_2, step=2)
    date = date_start
    while date <= calcTimeP.date_end:
        print(date)        
        if not os.path.exists(analysis.filename(date, step=step_2)): 
            data_1 = analysis.loadData(date, step=step_1)       
            data_step_3 = steps.secondStep(data_1, date,
                                           mask_freq=True, bin_t=True, bin_t_w=6,
                                           flatten=False, r_w=25)
            analysis.saveData(date, event_list=data_step_3, step=step_2)
        date += datetime.timedelta(days=calcTimeP.cores)
        
    date = date_start
    while date <= calcTimeP.date_end:
        print(date)            
        if not os.path.exists(analysis.filename(date, step=step_3)):
            data_2 = analysis.loadData(date, step=step_2)
            data_step_3 = steps.thirdStep(data_2, date, 
                                          peak_limit=7.0, mask_frq=True, 
                                          bin_time_w=12, limit_skip=0.7, 
                                          limit_skip2=1.2)
            analysis.saveData(date, event_list=data_step_3, step=step_3)
        
        date += datetime.timedelta(days=calcTimeP.cores)
