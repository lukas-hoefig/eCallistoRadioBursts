"""import matplotlib.pyplot as plt
from datetime import datetime
from datetime import timedelta
import const
import data
import observatories
import download
import analysis
import correlation

from datetime import datetime
"""
import datetime

import radiospectra.sources.callisto as cal
import os

import observatories
import data
import reference
import const
import analysis

year = 2022
month = 1
day = 10
time = "14:34:00"
date = datetime.datetime(year, month, day, int(time[:2]), int(time[3:5]))
obs = [observatories.uni_graz, observatories.triest, observatories.swiss_landschlacht, observatories.oe3flb,
       observatories.alaska_haarp, observatories.alaska_cohoe, observatories.roswell, observatories.bir,
       observatories.indonesia, observatories.assa, observatories.swiss_muhen, observatories.swiss_hb9sct,
       observatories.egypt_alexandria, observatories.arecibo, observatories.greenland, observatories.humain]
obs = [observatories.glasgow, observatories.humain]
for i in obs:
    try:
        dp = data.createFromTime(year, month, day, time, i, [45, 81])
        dp.plot()
    except:
        pass


ref1 = reference.referenceMonstein(year, month, day)

print("monstein")
for i in ref1:
    print(i, i.stations)

ref2 = reference.referenceSWPC(year, month, day)

print("swpc")
print(ref2)
"""
o_unigraz = observatories.uni_graz
spec_range = [45, 81]


def plotPoint(year, month, day, time):
    p1 = data.createFromTime(year,month,day,time, o_unigraz, spec_range)
    p1.plot()
    p2 = data.createFromTime(year,month,day,time, observatories.swiss_landschlacht, spec_range)
    p2.plot()


def plotPoint2(year, month, day, time):
    p1 = data.createFromTime(year,month,day,time, o_unigraz, spec_range)
    p1.plot()
    p2 = data.createFromTime(year,month,day,time, observatories.austria, spec_range)
    p2.plot()
    p3 = data.createFromTime(year, month, day, time, observatories.triest, spec_range)
    p3.plot()

def time2(time):
    date_format_str = '%H:%M:%S'
    given_time = datetime.strptime(time, date_format_str)
    final_time = given_time - timedelta(minutes=15) 
    final_time_str = final_time.strftime('%H:%M:%S')
    return final_time_str

year = 2022
month = 1
day = 7
time = "12:11:00"
time_2 = time2(time)

plotPoint2(year, month, day, time)

# dp1 = data.createDay(year, month, day, observatories.uni_graz, spec_range)
# dp2 = data.createDay(year, month, day, observatories.austria, spec_range)
# dp3 = data.createDay(year, month, day, observatories.triest, spec_range)
# 
# 
# dp1_clean1, dp2_clean1 = data.fitTimeFrameDataSample(dp1, dp2)
# dp1_clean2, dp2_clean2 = data.fitTimeFrameDataSample(dp1, dp3)
# dp1_clean3, dp2_clean3 = data.fitTimeFrameDataSample(dp2, dp3)
# 
# cor1 = correlation.Correlation(dp1_clean1, dp2_clean1)
# 
d11 = data.createFromTime(year, month, day, time, observatories.triest, spec_range)
d12 = data.createFromTime(year, month, day, time_2, observatories.triest, spec_range)

d21 = data.createFromTime(year, month, day, time, observatories.uni_graz, spec_range)
d22 = data.createFromTime(year, month, day, time_2, observatories.uni_graz, spec_range)

d1 = d11 + d12
d2 = d21 + d22

c = correlation.Correlation(d1, d2)
c.calculatePeaks()
c.printResult()
fig, ax = plt.subplots(figsize=(16,9))
c.plotCurve(ax)
plt.show()
"""