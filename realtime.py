#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
functions and algorithm for the realtime implementation

:authors: 	Lukas Höfig
:contact: 	lukas.hoefig@edu.uni-graz.at
:date:       02.10.2022
"""

import copy
import datetime
import os
import sys  # sys.argv   [0]name script [1-n] arguments
from typing import List, Union
from ftplib import FTP
import shutil
import pickle

import analysis
import config
import correlation
import events
import stations
import download
import nextcloud
import data
import steps

token_download = "token1"
token_handle = "token2"
token_auth = "token3"

ftp_server = "147.86.8.73"
ftp_acc = 'solarradio'
ftp_psswd = 'solar$251'
ftp_directory = 'XCHG'

# observatories = ["AUSTRIA-UNIGRAZ", "AUSTRIA-OE3FLB", "SWISS-Landschlacht"]


def deleteOldFiles(*date):
    if date:
        date_ = config.getDateFromArgs(*date)
    else:
        date_ = datetime.datetime.today() - datetime.timedelta(days=2)
    try:
        path = config.pathDataDay(date_)
        shutil.rmtree(path)
    except FileNotFoundError:
        pass


def stationsToday():
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


def downloadFtpNewFiles(path: str):
    with FTP(ftp_server) as ftp:
        ftp.login(ftp_acc, ftp_psswd)
        ftp.cwd(ftp_directory)
        files = ftp.nlst()
        print(f"Downloading files from server: {len(files)}")
        for i in enumerate(files):
            print(f"{i[0] + 1:4} ({ftp.size(i[1]) / 1024:9.3f} kB): {i[1]}           ", end="\r")
            with open(path + i[1], 'wb') as fp:
                # CMD = 'RETR ' + config.pathDataDay(datetime.datetime.today()) + i
                CMD = 'RETR ' + i[1]
                ftp.retrbinary(CMD, fp.write)
        ftp.quit()
    print("All files downloaded successfully                                         ")


def getFilesFromExtern(observatories=None):
    if observatories is None:
        observatories = ["AUSTRIA-UNIGRAZ", "AUSTRIA-OE3FLB", "SWISS-Landschlacht", "BIR", "HUMAIN", "ALASKA-HAARP",
                         "ALASKA-COHOE", "GLASGOW", "Australia-ASSA", "ROSWELL-NM", "ALMATY", "Arecibo-Observatory",
                         "INDONESIA", "TRIEST"]
    path_dl = config.pathDataDay(datetime.datetime.today())
    # downloadFtpNewFiles(path_dl)    <--- finally
    # nextcloud.downloadFromCloud(token_download, path=path_dl)
    # download.downloadFullDay(datetime.datetime.today(), station=observatories)
    download.downloadLastHours(observatories)
    # nextcloud.unzip(path_dl)


def getDate(file: str):
    reader = file.rsplit('/')[-1]
    reader = reader.rsplit('_')

    year = int(reader[-3][:4])
    month = int(reader[-3][4:6])
    day = int(reader[-3][6:])
    hour = int(reader[-2][:2])
    minute = int(reader[-2][2:4])
    second = int(reader[-2][4:])

    return datetime.datetime(year, month, day, hour, minute, second)


def dropOld(list_str: List[List[str]], num=2):
    new = [i[-num:] for i in list_str]
    newest_all = [getDate(i[-1]) for i in new]
    newest = max(newest_all)
    files = [i[1] for i in enumerate(new) if
             abs((newest_all[i[0]] - newest).total_seconds()) < datetime.timedelta(minutes=3).total_seconds()]
    return files


def getFiles(observatories: List[Union[str, stations.Station]]):
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


def filename(date=None):
    if date is None:
        date = datetime.datetime.today()
    else:
        date = config.getDateFromArgs(date)
    return config.path_realtime + config.pathDay(date) + f"{date.year}_{date.month}_{date.day}"


def saveRealtimeTxt(event_list: events.EventList, date=None):
    file_name = filename(date=date) + ".txt"
    with open(file_name, "w+") as file:
        file.write("\n".join([events.header(), str(event_list)]))


def saveRealTime(event_list: events.EventList, date=None):
    file_name = filename(date=date)
    folder = file_name[:file_name.rfind("/") + 1]
    if not (os.path.exists(folder) and os.path.isdir(folder)):
        os.makedirs(folder)
    if os.path.exists(filename()):
        os.remove(filename())
    with open(filename(), "wb+") as file:
        pickle.dump(event_list, file)


def loadRealTime(date=None) -> events.EventList:
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

        return events.EventList([], date)


if __name__ == "__main__":
    today = datetime.datetime.today()
    all_obs = stations.getStations(today)
    getFilesFromExtern(observatories=all_obs)
    # deleteOldFiles()
    obs = stationsToday()
    f = getFiles(obs)
    e_list_old = loadRealTime(date=today)

    sets = [sum([data.DataPoint(j) for j in i]) for i in f]
    e_list_new = steps.firstStep(today, data_sets=sets)

    if not e_list_new:
        saveRealTime(e_list_old)
        saveRealtimeTxt(e_list_old)
        quit()

    e_list_new2 = steps.secondStep(e_list_new, today)

    if not e_list_new2:
        saveRealTime(e_list_old)
        saveRealtimeTxt(e_list_old)
        quit()

    e_list_new3 = steps.thirdStep(e_list_new2, today)

    if not e_list_new3:
        saveRealTime(e_list_old)
        saveRealtimeTxt(e_list_old)
        quit()

    e_list_new4 = steps.fourthStep(e_list_new3, today)

    if not e_list_new4:
        saveRealTime(e_list_old)
        saveRealtimeTxt(e_list_old)
        quit()

    e_list = e_list_old + e_list_new4
    saveRealTime(e_list)
    saveRealtimeTxt(e_list)
