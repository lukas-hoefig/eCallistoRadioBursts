from datetime import timedelta

import correlation
import observatories
import download
import data
import analysis
import reference

spec_range = [45, 81]
_year = 2022
_month = 1
_day = 31
_days = 1
time = "08:24:00"
date = analysis.Time(_year, _month, _day, int(time[:2]), int(time[3:5]))

observatory = [observatories.uni_graz,
               observatories.triest,
               observatories.swiss_landschlacht,
               observatories.oe3flb,
               observatories.alaska_haarp,
               observatories.alaska_cohoe,
               observatories.roswell,
               observatories.bir,
               observatories.indonesia,
               observatories.assa,
               observatories.swiss_muhen,
               observatories.swiss_hb9sct,
               observatories.egypt_alexandria,
               observatories.arecibo]

obs = observatories.uni_graz

dp1 = data.createFromTime(_year, _month, _day, time, obs, spec_range)
dp2 = data.createFromTime(_year, _month, _day, str(date+timedelta(minutes=15)), obs, spec_range)
#dp3 = data.createFromTime(_year, _month, _day, str(date+timedelta(minutes=15*2)), obs, spec_range)
#dp4 = data.createFromTime(_year, _month, _day, str(date+timedelta(minutes=15*3)), obs, spec_range)

dp = dp1+dp2 #+dp3+dp4
dp.subtract_background()
dp.plot()
