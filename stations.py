#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
 -  ROBUST  -
 - stations.py -

contains the management of the stations/observatories
low level
"""


from typing import List, Union
from astropy.io import fits
import urllib
from bs4 import BeautifulSoup
import os
import warnings
import datetime

import config

e_callisto_url = config.e_callisto_url
seperator = "_"


class Station:
    def __init__(self, name: str, focus_code=None, longitude=None, latitude=None, spectral_range=None):
        """
        :param name: ID of the Observatory
        :param spectral_range: dict{"ID", [spectral, range]}
        """
        self.name = name
        self.focus_code = focus_code
        self.longitude = longitude
        self.latitude = latitude
        self.spectral_range = spectral_range

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __lt__(self, other):
        if isinstance(other, str):
            return self.name < other
        if not isinstance(other, Station):
            raise AttributeError
        if self.name == other.name:
            return self.focus_code < other.focus_code
        return self.name < other.name

    def obsTime(self):
        """
        sun zenith by latitude
        """
        return (12 - (self.longitude + 360) / 360 * 24) % 24


class StationSet:
    """
    TODO remove this and only keep stationRange()
    """
    def __init__(self, stations: List[Station]):
        self.stations = stations

    def getSet(self):
        sets = []
        for station1 in range(len(self.stations)):
            for station2 in range(station1 + 1, len(self.stations)):
                sets.append([self.stations[station1], self.stations[station2]])
        return sets


def stationRange(station_list: List[Station]) -> List[List[Station]]:
    """
    creates a set of station pairs from a list of stations
    :param station_list:
    """
    set_ = StationSet(station_list)
    return set_.getSet()


def getFocusCode(*date: Union[int, datetime.datetime], station: str) -> str:
    """
    gets the first valid focus code for a station on a specific day
    :param date:
    :param station:
    :return:
    """
    date_ = config.getDateFromArgs(*date)

    files = os.listdir(config.pathDataDay(date_))
    files_station = [i for i in files if i.startswith(station + seperator)]
    for i in files_station:
        file = fits.open(config.pathDataDay(date_) + i)
        frq_axis = file[1].data['frequency'].flatten()
        frq = sorted([frq_axis[0], frq_axis[-1]])
        if config.frq_limit_low_upper > frq[0] > config.frq_limit_low_lower and \
                config.frq_limit_high_upper > frq[1] > config.frq_limit_high_lower:
            return i.rsplit(seperator)[-1].rstrip(config.file_ending)
    raise ValueError("No valid focus code for that day")


def listFilesDay(source: str, offline=False):
    """
    :param source: full url incl the day, or path to offline data
    :param offline: switch between offline and online search of files to go through
    """
    if not offline:
        page = urllib.request.urlopen(source).read()
        soup = BeautifulSoup(page, 'html.parser')
        return [node.get('href') for node in soup.find_all('a') if node.get('href').endswith(config.file_type_zip)]
    else:
        files = os.listdir(source)
        return [file for file in files if file.endswith(config.file_type_zip)]


def listFD(source: str, station: List[str], offline=False):
    """
    :param source: full url incl the day
    :param station: [name, focus-code]
    :param offline: switch between offline and online search of files to go through
    """
    if not offline:
        page = urllib.request.urlopen(source).read()
        soup = BeautifulSoup(page, 'html.parser')

        return [source + '/' + node.get('href') for node in soup.find_all('a')
                if node.get('href').startswith(station[0]) and node.get('href').endswith(station[1] + config.file_type_zip)]
    else:
        files = os.listdir(source)
        return [source + '/' + file for file in files
                if file.startswith(station[0]) and file.endswith(station[1] + config.file_type_zip)]


def getNameFcFromFile(file: str) -> (str, str):
    """
    get name and focus code from a filename
    :param file:
    """
    file_name = file.rsplit("/")[-1]
    parts = file_name.rsplit(seperator)
    if len(parts) < 4:
        return None, None
    elif len(parts) == 4:
        return parts[0], parts[3][:2]
    else:
        len_ = len(parts)
        return seperator.join([parts[i] for i in range(len_ - 3)]), parts[-1][:2]


def getStations(*date: Union[int, datetime.datetime], offline: bool = False) -> List[Station]:
    """
    returns a list of stations for a specific date from online data or local files
    :param date:
    :param offline: searches local files
    """
    date_ = config.getDateFromArgs(*date)
    if offline:
        source = config.pathDataDay(date_)
    else:
        date_str = "{:%Y/%m/%d}".format(date_)
        source = e_callisto_url + date_str
    files = listFilesDay(source, offline=offline)
    stations = []
    stations_return = []
    for i in files:
        name_read, fc_read = getNameFcFromFile(i)
        if name_read is not None:
            stations.append([name_read, fc_read])
    stations_clean = []
    for i in stations:
        if i not in stations_clean:
            stations_clean.append(i)
    for i in stations_clean:
        name = i[0]
        focus_code = i[1]
        for a, b in enumerate(listFD(source, i, offline=offline)):
            try:
                with fits.open(b) as fds:
                    try:
                        lat = fds[0].header['OBS_LAT']
                        lac = fds[0].header['OBS_LAC']
                        if lac == 'S':
                            lat_ = -lat
                        else:
                            lat_ = lat
                        lon = fds[0].header['OBS_LON']
                        loc = fds[0].header['OBS_LOC']
                        if loc == 'W':
                            lon_ = -lon
                        else:
                            lon_ = lon
                        frq_axis = fds[1].data['frequency'].flatten()
                        frq = sorted([frq_axis[0], frq_axis[-1]])
                        if config.frq_limit_low_upper > frq[0] > config.frq_limit_low_lower and \
                                config.frq_limit_high_upper > frq[1] > config.frq_limit_high_lower:
                            station = Station(name, focus_code, lon_, lat_, frq)
                            stations_return.append(station)
                    except (IndexError, KeyError, TypeError, AttributeError):
                        warnings.warn(message=f"Could not read fits file of {b}",
                                      category=UserWarning)
                    break
            except OSError:
                continue
    return stations_return


def getStationFromFile(file: str) -> Station:
    """
    creates Station object from filename
    :param file:
    """
    name, focus_code = getNameFcFromFile(file)
    if name is None:
        raise AttributeError("cannot read file", file)
    try:
        with fits.open(file) as fds:
            lat = fds[0].header['OBS_LAT']
            lac = fds[0].header['OBS_LAC']
            if lac == 'S':
                lat = -lat
            lon = fds[0].header['OBS_LON']
            loc = fds[0].header['OBS_LOC']
            if loc == 'W':
                lon = -lon
    except IndexError:
        warnings.warn(message=f"failed to open {file}", category=UserWarning)
        return Station(name, focus_code=focus_code)
    except KeyError:
        warnings.warn(message=f" {file}", category=UserWarning)
        return Station(name, focus_code=focus_code)
    except OSError:
        warnings.warn(message=f"corrupt file {file}", category=UserWarning)
        return Station(name, focus_code=focus_code)
    finally:
        try:
            with fits.open(file) as fds:
                frq_axis = fds[1].data["frequency"].flatten()
                frq = sorted([frq_axis[0], frq_axis[-1]])
                if config.frq_limit_low_upper > frq[0] > config.frq_limit_low_lower and \
                        config.frq_limit_high_upper > frq[1] > config.frq_limit_high_lower:
                    return Station(name, focus_code, lon, lat, frq)
                raise AttributeError("Station in file has wrong frequency range.")
        except IndexError:
            warnings.warn(message=f"failed to open {file}", category=UserWarning)
            return Station(name, focus_code=focus_code)
        except KeyError:
            return Station(name, focus_code=focus_code)
        except OSError:
            warnings.warn(message=f"corrupt file {file}", category=UserWarning)
            return Station(name, focus_code=focus_code)
        