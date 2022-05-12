# from calendar import month
import matplotlib.pyplot as plt
from datetime import datetime
from datetime import timedelta
import const
import data
import observatories
import download
import analysis
import correlation

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

year = 2017
month = 9
day = 6
time = "12:19:00"
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


