#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
 -  ROBUST  -
 - downloader.py -

automatically downloads all available files from start date to end date
on common connection issues: waits and tries again
"""

import download
import datetime
import stations
import time
import socket
from concurrent.futures import TimeoutError


start = datetime.datetime(2023,3, 8)
end = datetime.datetime(2018,3, 10)
end_reached = False
current = start

while not end_reached:
    print(f"Download {current.year} {current.month:02} {current.day:02}")
    observatories = stations.getStations(current)
    print(f"{len(observatories)}")
    passed = False
    while not passed:
        try:
            download.downloadFullDay(current, station=observatories)
            current = current + datetime.timedelta(days=1)
            passed = True
            print("Done:", current)
        except TimeoutError:
            time.sleep(5)
        except ConnectionRefusedError:
            time.sleep(61)
        except socket.timeout:
            time.sleep(61)
    if current >= end:
        print("all done", current)
        end_reached = True
        break
