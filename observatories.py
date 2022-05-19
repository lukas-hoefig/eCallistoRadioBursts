#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
from typing import List

observatory_dict = {}
observatory_list = []


class Observatory:
    """
    TODO: comparable spectral range

    TODO: get id
    """

    def __init__(self, name: str, spectral_range: dict, longitude=0.0):
        """
        :param name: ID of the Observatory
        :param spectral_range: dict{"ID", [spectral, range]}
        """
        self.name = name
        self.spectral_range = spectral_range
        observatory_list.append(self.name)
        observatory_dict[self.name] = self
        self.longitude = longitude

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__str__()

    def getSpectralRange(self, identification: str):
        """
        get spectral range of files
        throws KeyError

        :param identification: string i.e. "01", "02", "57", ...
        :return: list [low, high]
        """
        return self.spectral_range[identification]

    def obsTime(self):
        """
        sun zenith by latitude
        """
        return (12 - (self.longitude + 360) / 360 * 24) % 24


class ObservatorySet:
    def __init__(self, observatories: List[Observatory]):
        self.observatories = observatories

    def getSet(self):
        sets = []
        for obs1 in range(len(self.observatories)):
            for obs2 in range(obs1+1, len(self.observatories)):
                sets.append([self.observatories[obs1], self.observatories[obs2]])
        return sets


def specID(_observatory, _spectral_range):
    return next(key for key, s_range in _observatory.spectral_range.items() if s_range == _spectral_range)


def getObservatory(name: str) -> Observatory:
    return observatory_dict[name]


stat_uni_graz = "AUSTRIA-UNIGRAZ"
spec_range_uni_graz = {"01": [45, 81]}
uni_graz = Observatory(stat_uni_graz, spec_range_uni_graz, longitude=15.5)

stat_swiss_landschlacht = "SWISS-Landschlacht"
spec_range_swiss_landschlacht = {"01": [45, 81], "02": [np.NaN, np.NaN]}  # true range = [15.0, 86.625]
swiss_landschlacht = Observatory(stat_swiss_landschlacht, spec_range_swiss_landschlacht, longitude=9.239999771)

stat_michelbach = "AUSTRIA-MICHELBACH"
spec_range_michelbach = {"60": [175, 380]}
michelbach = Observatory(stat_michelbach, spec_range_michelbach, longitude=15.39999962)

stat_oe3flb = "AUSTRIA-OE3FLB"
# spec_range_oe3flb = {"57": [20.0, 91.625]}
spec_range_oe3flb = {"57": [45, 81]}
oe3flb = Observatory(stat_oe3flb, spec_range_oe3flb, longitude=15.39999962)

stat_austria = "AUSTRIA"
# spec_range_austria = {"57": [20, 91.625]}
spec_range_austria = {"57": [45, 81]}
austria = Observatory(stat_austria, spec_range_austria, longitude=15.39999962)

stat_swiss_hb9sct = "HB9SCT"  # swiss-hb9sct   ?????????
spec_range_swiss_hb9sct = {"02": [45, 81]}
swiss_hb9sct = Observatory(stat_swiss_hb9sct, spec_range_swiss_hb9sct, longitude=8.75590992)

stat_swiss_heiterswil = "SWISS-HEITERSWIL"
spec_range_swiss_heiterswil = {"59": [45, 81]}
swiss_heiterswil = Observatory(stat_swiss_heiterswil, spec_range_swiss_heiterswil, longitude=9.130000114)

stat_swiss_heiterswil_old = "Heiterswil-CH"
spec_range_swiss_heiterswil_old = {"59": [45, 81]}
swiss_heiterswil_old = Observatory(stat_swiss_heiterswil_old, spec_range_swiss_heiterswil_old, longitude=9.130000114)

# stat_swiss_muhen = "SWISS_MUHEN"
# spec_range_swiss_muhen = {"02": [np.nan,np.nan ]}
# swiss_muhen = Observatory(stat_swiss_muhen, spec_range_swiss_muhen, longitude=8.059169769)

stat_triest = "TRIEST"
spec_range_triest = {"57": [45, 81]}
triest = Observatory(stat_triest, spec_range_triest, longitude=13.875)

stat_bir = "BIR"
spec_range_bir = {"01": [45, 81]}
bir = Observatory(stat_bir, spec_range_bir, longitude=-7.92)

stat_alaska_haarp = "ALASKA-HAARP"
spec_range_alaska_haarp = {"62": [45, 81], "63": [45, 81]}   # [10,81]
alaska_haarp = Observatory(stat_alaska_haarp, spec_range_alaska_haarp, longitude=-145.1699982)

stat_alaska_cohoe = "ALASKA-COHOE"
spec_range_alaska_cohoe = {"62": [45, 81], "63": [45, 81]}   # [45,95]
alaska_cohoe = Observatory(stat_alaska_cohoe, spec_range_alaska_cohoe, longitude=-151.3200073)

stat_roswell = "ROSWELL-NM"
spec_range_roswell = {"57": [200, 400], "58": [45, 81], "59": [200, 500]}   # [20,80]
roswell = Observatory(stat_roswell, spec_range_roswell, longitude=-104.51528)


# TODO:
"""
groups of observatories that should work together

AUSTRIA-UNIGRAZ , TRIEST , SWISS-Landschlacht

Australia-ASSA, INDONESIA, MONGOLIA-UB, INDIA-UDAIPUR, ALMATY
Australia-LMRO, JAPAN-IBARAKI, KASI (south corea), 

Arecibo-Observatory, MEXART, roswell-nm

alaska-cohoe, alaska-haarp
"""