#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np


class Observatory:
    """
    TODO: comparable spectral range

    TODO: get id
    """

    def __init__(self, name: str, spectral_range: dict):
        """
        :param name: ID of the Observatory
        :param spectral_range: dict{"ID", [spectral, range]}
        """
        self.name = name
        self.spectral_range = spectral_range

    def getSpectralRange(self, identification: str):
        """
        get spectral range of files
        throws KeyError

        :param identification: string i.e. "01", "02", "57", ...
        :return: list [low, high]
        """
        return self.spectral_range[identification]


stat_uni_graz = "AUSTRIA-UNIGRAZ"
spec_range_uni_graz = {"01": [45, 81]}
uni_graz = Observatory(stat_uni_graz, spec_range_uni_graz)

stat_swiss_landschlacht = "SWISS-Landschlacht"
spec_range_swiss_landschlacht = {"01": [45, 81], "02": [np.NaN, np.NaN]}  # true range = [15.0, 86.625]
swiss_landschlacht = Observatory(stat_swiss_landschlacht, spec_range_swiss_landschlacht)

stat_michelbach = "AUSTRIA-MICHELBACH"
spec_range_michelbach = {"60": [175, 380]}
michelbach = Observatory(stat_michelbach, spec_range_michelbach)

stat_oe3flb = "AUSTRIA-OE3FLB"
# spec_range_oe3flb = {"57": [20.0, 91.625]}
spec_range_oe3flb = {"57": [45, 81]}
oe3flb = Observatory(stat_oe3flb, spec_range_oe3flb)

stat_austria = "AUSTRIA"
# spec_range_austria = {"57": [20, 91.625]}
spec_range_austria = {"57": [45, 81]}
austria = Observatory(stat_austria, spec_range_austria)

stat_swiss_hb9sct = "HB9SCT"  # swiss-hb9sct   ?????????
spec_range_swiss_hb9sct = {"02": [45, 81]}
swiss_hb9sct = Observatory(stat_swiss_hb9sct, spec_range_swiss_hb9sct)

stat_swiss_heiterswil = "SWISS-HEITERSWIL"
spec_range_swiss_heiterswil = {"59": [45, 81]}
swiss_heiterswil = Observatory(stat_swiss_heiterswil, spec_range_swiss_heiterswil)

# stat_swiss_muhen = "SWISS_MUHEN"
# spec_range_swiss_muhen = {"02": [np.nan,np.nan ]}
# swiss_muhen = Observatory(stat_swiss_muhen, spec_range_swiss_muhen)

stat_triest = "TRIEST"
spec_range_triest = {"57": [45, 81]}
triest = Observatory(stat_triest, spec_range_triest)

# ----------------------------------------------------
"""
TODO -> class this 

"""
observatories = {stat_uni_graz: uni_graz, stat_triest: triest, stat_oe3flb: oe3flb,
                 stat_swiss_heiterswil: swiss_heiterswil, stat_swiss_hb9sct: swiss_hb9sct, stat_austria: austria,
                 stat_swiss_landschlacht: swiss_landschlacht}
observatory_list = [stat_uni_graz, stat_triest, stat_oe3flb, stat_swiss_heiterswil, stat_swiss_hb9sct, stat_austria,
                    stat_swiss_landschlacht]
