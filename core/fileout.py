#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import os
import shutil
import json 

import config
import analysis
import events 
import data 

file_metadata = os.path.join(config.path_realtime_metadata, config.file_metadata)

def txtFileName(date: datetime.datetime):
    if date is None:
        date = datetime.datetime.now()
    return f"Robust_Graz_{date.year}{date.month:02}{date.day:02}.txt"


def loadJson() -> dict:
    date = datetime.datetime.today()
    filename_txt = txtFileName(date)
    if not os.path.exists(file_metadata):
        with open(file_metadata, "w+") as f:
            f.write(f'{{"txt_filename": "{filename_txt}"}}')

    with open(file_metadata, 'r') as file:
        json_data = json.load(file)    
    return json_data


def updateJsonValue(key, new_value):
    json_data = loadJson()   

    # if key in json_data: # check if value is empty
    json_data[key] = new_value

    with open(file_metadata, 'w') as file:
        json.dump(json_data, file, indent=4)


def foldername(burst: events.Event):
    return os.path.join(config.path_realtime, "current", burst.time_start.strftime(config.foldernames_realtime))


def saveJson(eventlist: events.EventList) -> None:
    json_data = loadJson()
    event_list_dict = []

    for event in eventlist:
        name_folder = event.time_start.strftime(config.foldernames_realtime)    
        name_file = event.time_start.strftime(config.filenames_realtime)
        stations_dict = sorted([{"name":stat.name, "file":f"{name_file}_{stat.name}.png"} for stat in event.stations], key=lambda x: x["name"]) 
        event_list_dict.append({"name": name_folder,
                                "type": event.burst_type,
                                "time": f"{event.time_start.strftime('%H:%M')} - {event.time_end.strftime('%H:%M')}",
                                "stations": stations_dict})

    json_data["last_update"] = datetime.datetime.now().strftime(config.event_time_website)
    json_data["bursts"] = event_list_dict

    with open(file_metadata, 'w') as file:
        json.dump(json_data, file, indent=4)


def saveplots(eventlist: events.EventList) -> None:
    for event in eventlist:
        folder = foldername(event)
        os.makedirs(folder, exist_ok=True)
        for stat in event.stations:
            dp = data.createFromEvent(event, stat)
            analysis.plotDatapoint(dp, save_img=True, folder=folder, short_name=True)


def moveDayToArchive():
    day = datetime.datetime.today() - datetime.timedelta(days=1)
    folder = os.path.join(config.path_realtime, "current")
    shutil.make_archive(os.path.join(config.path_realtime, f"{day.year}/{day.month}/{day.day}", f"ROBUST_archive_{day.strftime('%Y%m%d')}"), 'zip', folder)
    os.remove(folder)
    os.makedirs(folder, exist_ok=True)
