import matplotlib.pyplot as plt

import correlation
import observatories
import data


obs = [observatories.uni_graz,              # 0
       observatories.triest,                # 1
       observatories.swiss_landschlacht,    # 2
       observatories.oe3flb,                # 3
       observatories.alaska_haarp,          # 4
       observatories.alaska_cohoe,          # 5
       observatories.roswell,               # 6
       observatories.bir,                   # 7
       observatories.indonesia,             # 8
       observatories.assa,                  # 9
       observatories.swiss_muhen,           # 10
       observatories.swiss_hb9sct,          # 11
       observatories.egypt_alexandria,      # 12
       observatories.arecibo,               # 13
       observatories.humain,
       observatories.glasgow]

obs1 = obs[15]
obs2 = obs[14]

year = 2022
month = 1
day = 7
time = "03:32:00"

dp1 = data.createFromTime(year, month, day, time, obs1, [45, 81])
dp2 = data.createFromTime(year, month, day, time, obs2, [45, 81])

cor1 = correlation.Correlation(dp1, dp2, day=day, flatten=True, bin_time=False, bin_freq=False, no_background=False,
                               r_window=180)
cor1.calculatePeaks(limit=0.6)
print(cor1.fileName())
print(cor1.peaks)

cor = correlation.Correlation(dp1, dp2, day=day, flatten=True, bin_time=True, bin_freq=True, no_background=True,
                              r_window=30)
cor.calculatePeaks()
print(cor.fileName())
print(cor.peaks)

fig, ax = plt.subplots(figsize=(16, 9))
cor.plotCurve(ax)
cor1.plotCurve(ax)
plt.show()

fig2, ax2 = plt.subplots(figsize=(16, 9))
ax2_ = plt.twinx(ax2)
dp1.flattenSummedCurve()
dp2.flattenSummedCurve()
dp1.plotSummedCurve(ax2)
dp2.plotSummedCurve(ax2_)
plt.show()

fig3, ax3 = plt.subplots(figsize=(16, 9))
ax3_ = plt.twinx(ax3)
cor.plotCurve(ax3)

dp1.flattenSummedCurve()
dp2.flattenSummedCurve()
dp1.plotSummedCurve(ax3_)
dp2.plotSummedCurve(ax3_)


plt.show()

