#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import sys

import steps


if __name__ == '__main__':
    """
    args: year month day #days 
    """
    input_arg = sys.argv
    args = [2022, 1, 1, 1]
    if input_arg and len(input_arg) > 2:
        for i, j in enumerate(input_arg[1:]):
            args[i] = int(j)
    
    date_start = datetime.datetime(args[0],args[1],args[2])

    for i in range(0, args[3]):
        date = date_start + datetime.timedelta(i)
        steps.run1stSearch(date, mask_frq=True)
        steps.run2ndSearch(date)
        steps.run3rdSearch(date)


# 31.01 18:11 why?
"""
if __name__ == '__main__':
    # bacBurstFailed()

    #nobg = False
    #bin_f = False
    #bin_t = False
    #flatten = False
    #bin_t_w = 1
    #flatten_w = 1
    ## nobg = True
    #for r_w in range(20, 260, 20):
    #    testBacBursts(nobg, bin_f, bin_t, flatten, bin_t_w, flatten_w, r_w)
    #
    #r_w = 160
    #flatten = True
    #for flatten_w in range(40, 400, 60):
    #    testBacBursts(nobg, bin_f, bin_t, flatten, bin_t_w, flatten_w, r_w)
    #
    #r_w = 160
    #flatten = False
    #bin_t = True
    #for bin_t_w in range(2, 16, 2):
    #    testBacBursts(nobg, bin_f, bin_t, flatten, bin_t_w, flatten_w, r_w)
    #
    #r_w = 180
    #flatten = True
    #flatten_w = 220
    #bin_f = True
    #for nobg in range(2):
    #    testBacBursts(nobg, bin_f, bin_t, flatten, bin_t_w, flatten_w, r_w)

    flatten = True
    flatten_w = 220
    bin_f = False
    nobg = True
    bin_t = False
    bin_t_w = 4
    for r_w in range(180, 260, 10):
        testBacBursts(nobg, bin_f, bin_t, flatten, bin_t_w, flatten_w, r_w)




   andere ecallisto auswertungen -> type 3
   warum/wie/welche werte setzen -> i.e. binsize -> ___statistics___ 
   
   ordner -> test files -> known bursts, empties, type 2/3 overlay (anfang november 21), gewitter
   background remove -> yes/no, why - does it get better? 
   
   1/11 10:52-10:52  11:06-11:07
   2/11 10:14-10:15                         | gewitter
   3/11 09:31-09:32  14:06-14:08	        | gewitter
   
   
"""


# TODO:
"""

comparison -> [ liste["Events-verpasst"], liste["Events-falsch"]]

datapoint (obs1) 
datapoint (obs2)
datapoint (....)

for each test:
    for each setOfObservatoryCombination
        comparisons (obs1-obs2)
        ... 
        -> merge result listen  # TODO
    print test results 

"""

# TODO:
"""
day, obs1 obs2 -> EventList
day, obs1 obs3 -> EventList
day, obs2 obs3 -> EventList
                      |
                    merge
                  compare to reference 
"""

"""
type ii list 
20200529	07:23
20201016	12:59 (greenland + SWISS-Landschlacht ) 
20201020	13:31 (greenland)

"""
"""
type iv
20110924 12:00 - 14:00
20201121	11:30-    multiple type III 
20201125	23:26     australia-assa
20201129	12:56     unigraz - looks like type 2
20201130	10:56-10:58	VI	BIR, SWISS-Landschlacht    weak, multiple type iii ?
20201229	20:57      roswell - mexart
20201230	02:35      australia india uidaipur, indonesia
20201230	09:12      austria unigraz 
"""
"""
type V < 45 MHz -> not usually measurable with chosen observatories - rare


"""
"""
type i
20201201	04:53-05:53	I	Australia-ASSA   nope


"""
