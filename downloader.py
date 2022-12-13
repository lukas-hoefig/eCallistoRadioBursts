import download
import datetime
import stations
import time
from concurrent.futures import TimeoutError


start = datetime.datetime(2021, 4, 30)
end = datetime.datetime(2022, 5, 1)
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
        except TimeOutError:
            time.sleep(5)
        except ConnectionRefusedError:
            time.sleep(61)
    if current >= end:
        print("all done", current)
        end_reached = True
        break
