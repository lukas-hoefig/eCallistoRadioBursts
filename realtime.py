#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
 -  ROBUST  -
 - realtime.py -

functions and algorithm for the realtime implementation
"""

import copy
import datetime
import os
import sys  # sys.argv   [0]name script [1-n] arguments
from typing import List, Union
from ftplib import FTP
import shutil
import pickle
from urllib.error import HTTPError, URLError
from socket import gaierror

sys.path.append(os.path.join(os.path.dirname(__file__), "core"))

import analysis
import config
import correlation
import events
import stations
import download
import nextcloud
import data
import steps
import fileout

token_download = "token1"
token_handle = "token2"
token_auth = "token3"


def deleteOldFiles(*date) -> None:
    """
    removes ecallisto files from two days ago to save memory
    :param date: empty or date to remove files
    """
    if date:
        date_ = config.getDateFromArgs(*date)
    else:
        date_ = datetime.datetime.today() - datetime.timedelta(days=2)
    try:
        path = config.pathDataDay(date_)
        shutil.rmtree(path)
    except FileNotFoundError:
        pass


def stationsToday() -> List[stations.Station]:
    """
    looks for available stations for the current day from external files
    """
    all_files = os.listdir(config.pathDataDay(datetime.datetime.today()))
    observatories = []
    for file in all_files:
        try:
            if not any([i.name == file.rsplit("_")[0] for i in observatories]):
                obs = stations.getStationFromFile(config.pathDataDay(datetime.datetime.today()) + file)
                observatories.append(obs)
        except AttributeError:
            pass
    observatories = list(set(observatories))
    return observatories


def getFilesFromExtern(observatories=None) -> None:
    """
    downloads files for a set of stations, if none are given, it downloads  set of handpicked ones
    :param observatories:
    """
    if observatories is None:
        observatories = ["AUSTRIA-UNIGRAZ", "AUSTRIA-OE3FLB", "SWISS-Landschlacht", "BIR", "HUMAIN", "ALASKA-HAARP",
                         "ALASKA-COHOE", "GLASGOW", "Australia-ASSA", "ROSWELL-NM", "ALMATY", "Arecibo-Observatory",
                         "INDONESIA", "TRIEST"]
    # path_dl = config.pathDataDay(datetime.datetime.today())
    # downloadFtpNewFiles(path_dl)    <--- finally
    # nextcloud.downloadFromCloud(token_download, path=path_dl)
    # download.downloadFullDay(datetime.datetime.today(), station=observatories)
    download.downloadLastHours(observatories)
    # nextcloud.unzip(path_dl)


def getDate(file: str):
    """
    creates a datetime object from name of an e-Callisto file
    :param file: filename
    """
    reader = file.rsplit('/')[-1]
    reader = reader.rsplit('_')

    year = int(reader[-3][:4])
    month = int(reader[-3][4:6])
    day = int(reader[-3][6:])
    hour = int(reader[-2][:2])
    minute = int(reader[-2][2:4])
    second = int(reader[-2][4:])

    return datetime.datetime(year, month, day, hour, minute, second)


def dropOld(list_str: List[List[str]], num=2) -> List[List[str]]:
    """
    removes all old files from a list
    :param list_str: [[datetime:newest file_station_i, filenames_station_i],]
    :param num: number of allowed files / station
    """
    new = [i[-num:] for i in list_str]
    newest_all = [getDate(i[-1]) for i in new]
    newest = max(newest_all)
    fileout.updateJsonValue("newest_file", newest.strftime(config.event_time_website))
    files = [i[1] for i in enumerate(new) if
             abs((newest_all[i[0]] - newest).total_seconds()) < datetime.timedelta(minutes=3).total_seconds()]
    return files


def getFiles(observatories: List[Union[str, stations.Station]]):
    """
    collects all files relevant for this calculation, gets all observatories, gets all files for those, removes old ones
    :param observatories:
    """
    for i in enumerate(observatories):
        if isinstance(i[1], str):
            observatories[i[0]] = stations.Station(i[1], stations.getFocusCode(datetime.datetime.today(), station=i[1]))

    # focus_codes = [stations.getFocusCode(datetime.datetime.today(), station=obs) for obs in observatories]
    files_all = sorted(os.listdir(config.pathDataDay(datetime.datetime.today())))
    files_stations = [[file for file in files_all
                       if file.startswith(observatory.name + stations.seperator) and
                       file.endswith(observatory.focus_code + config.file_ending)] for observatory in observatories]
    files_filtered = dropOld(files_stations)

    return files_filtered


def filename(date=None, website=False) -> str:
    """
    file name for save file incl. path
    :param date:
    """
    if date is None:
        date = datetime.datetime.today()
    else:
        date = config.getDateFromArgs(date)
    if website:
        path = os.path.join(config.path_realtime, "current")
    else:
        path = os.path.join(config.path_realtime, config.pathDay(date))

    return os.path.join(path, f"ROBUST_Graz_{date.year}_{date.month:02}_{date.day:02}")


def saveRealtimeTxt(event_list: events.EventList, date=None) -> None:
    """
    saves current event list as txt output file
    :param event_list:
    :param date:
    """
    file_name = filename(date=date, website=False) + ".txt"
    with open(file_name, "w+") as file:
        file.write("\n".join([events.header(), str(event_list)]))

    file_name_website = os.path.join(config.path_realtime, "current", fileout.txtFileName(date))
    shutil.copy(file_name, file_name_website)
    nextcloud.uploadToCloud(file_name)


def saveRealTime(event_list: events.EventList, date=None) -> None:
    """
    saves current event list as binary file for further calculations
    :param event_list:
    :param date:
    """
    file_name = filename(date=date)
    folder = file_name[:file_name.rfind("/") + 1]
    if not (os.path.exists(folder) and os.path.isdir(folder)):
        os.makedirs(folder)
    if os.path.exists(filename()):
        os.remove(filename())
    with open(filename(), "wb+") as file:
        pickle.dump(event_list, file)


def loadRealTime(date=None) -> events.EventList:
    """
    loads realtime binary event list into memory
    :param date: integer yyyy, mm, dd   or datetime, None for production
    """
    if date is None:
        date = datetime.datetime.today()
    else:
        date = config.getDateFromArgs(date)
    file = filename()
    folder = file[:file.rfind("/") + 1]
    if os.path.exists(filename()):
        with open(file, "rb") as read_file:
            loaded_data = pickle.load(read_file)
        return loaded_data
    else:
        if not (os.path.exists(folder) and os.path.isdir(folder)):
            os.makedirs(folder)
            fileout.moveDayToArchive()
            fileout.updateJsonValue("txt_filename", fileout.txtFileName(date))

        return events.EventList([], date)


#--------------------------------------------
#thing after this gets currently used,
def folderNextcloud(*date):
    if data is None:
        _date = datetime.datetime.today()
    else:
        _date = date
    _date = config.getDateFromArgs(*date)
    return f"/{_date.year}-{_date.month}/"


def saveToNextCloud(event_list, date=None):
    saveTxtToNextCloud(date=date)
    saveImgToNextcloud(event_list)


def saveTxtToNextCloud(date=None):
    # file_name = os.path.join(folderNextcloud(date), filename(date=date) + ".txt")
    file_name = f"Graz_ROBUST_{filename(date=date)}.txt"
    nextcloud.uploadToCloud(file_name)


def saveImgToNextcloud(event_list: events.EventList):
    for event in event_list:
        folder_event = f"{event.time_start.year:02}{event.time_start.month:02}{event.time_start.day:02}-{event.time_start.hour:02}{event.time_start.minute:02}"
        for station in event.stations:
            dp = data.createFromEvent(event, station=station)
            analysis.plotDatapoint(dp, save_img=True, folder=os.path.join(config.path_realtime, folder_event))

        nextcloud.uploadToCloud(folder_event)


def save(event_list, date=None):
    saveRealTime(event_list)
    saveRealtimeTxt(event_list)
    fileout.saveJson(event_list)
    fileout.saveplots(event_list)
    #saveToNextCloud(event_list, date=date)


if __name__ == "__main__":
    today = datetime.datetime.today()
    all_obs = None
    try:
        all_obs = stations.getStations(today)
    except (ConnectionResetError, HTTPError, TimeoutError, URLError, gaierror, ConnectionRefusedError):
        pass
    finally:
        getFilesFromExtern(observatories=all_obs)
    # deleteOldFiles()
    obs = stationsToday()
    f = getFiles(obs)
    e_list_old = loadRealTime(date=today)

    sets = [sum([data.DataPoint(j) for j in i]) for i in f]
    e_list_new = steps.firstStep(today, data_sets=sets)

    if not e_list_new:
        save(e_list_old)
        #saveRealTime(e_list_old)
        #saveRealtimeTxt(e_list_old)
        quit()

    e_list_new2 = steps.secondStep(e_list_new, today)

    if not e_list_new2:
        save(e_list_old)
        #saveRealTime(e_list_old)
        #saveRealtimeTxt(e_list_old)
        quit()

    e_list_new3 = steps.secondStep(e_list_new2, today)

    if not e_list_new3:
        save(e_list_old)
        #saveRealTime(e_list_old)
        #saveRealtimeTxt(e_list_old)
        quit()

    e_list_new4 = steps.thirdStep(e_list_new3, today)

    if not e_list_new4:
        save(e_list_old)
        #saveRealTime(e_list_old)
        #saveRealtimeTxt(e_list_old)
        quit()

    e_list = e_list_old + e_list_new4
    save(e_list)
    #saveRealTime(e_list)
    #saveRealtimeTxt(e_list)
