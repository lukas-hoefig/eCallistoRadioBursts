#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import matplotlib.pyplot as plt
import numpy as np
import datetime
import config
import analysis
import events
import reference


def getReference(*date, europeUT=True):
    ref_load = reference.listSWPC(*date)
    # ref_strong = [i for i in ref_load if i.burst_type.endswith("II/2") or i.burst_type.endswith("II/3")]
    if europeUT:
        ref = events.EventList([i for i in ref_load if config.EU_time_lower <=
                               i.time_start.hour < config.EU_time_upper], *date)
    else:
        ref = ref_load
    return ref


def strong(ref: events.EventList, *date):
    """
    returns list of events: TP, TN, FP
    """
    ref_strong = events.EventList([i for i in ref if i.burst_type.endswith(
        "II/2") or i.burst_type.endswith("II/3")], *date)
    return ref_strong


# csv
def readResult(file: str):
    with open(file, "r") as f:
        reader = csv.reader(f, delimiter="\t")
        data = np.array([i for i in reader])
    dataT = data.transpose()[1:-1]
    res = [sum(int(i) for i in j) for j in dataT]
    return res


if not __name__ == "__main__":

    date_start = datetime.datetime(2017, 5, 1)
    date_end = datetime.datetime(2023, 4, 1)
    date = date_start
    referen = 0
    referen_s = 0

    data_missing = 0

    while date < date_end:
        try:
            even = len(getReference(date))
            even_str = len(strong(getReference(date), date))
            referen += even
            referen_s += even_str

        except FileNotFoundError:
            data_missing += 1

        finally:
            date += datetime.timedelta(days=1)

    print("reference:", referen, "\nstrong: ", referen_s)
    print("missing ", data_missing)

    # test
    d = []
    ds = []
    for step_ in [3]:

        step = step_
        d.append(readResult(config.path_results +
                            f"all_summed_results2_{step}.txt"))

    for j, i in enumerate(d):
        print(i)


if not __name__ == "__main__":
    # test
    d = []
    ds = []
    for step_ in [1, 2]:
        step = step_
        d.append(readResult(config.path_results +
                            f"summed_results_{step}.txt"))

    for j, i in enumerate(d):
        print(i)


if not __name__ == "__main__":
    # step 3 -> ??
    d = []
    ds = []
    for mask_frq_ in [0, 1]:
        for bin_t_w_ in [4, 8, 12]:
            for peak_limit_ in [0.8, 1.0, 1.5, 2.0, 2.5, 3.0]:
                step = int(50000000 + bin_t_w_ * 1000 +
                           mask_frq_*1000000 + peak_limit_ * 10)
                # ds.append(r_w_)
                d.append(readResult(config.path_results +
                         f"summed_results_{step}.txt"))

    for j, i in enumerate(d):
        if not j % 6:
            print("\n")
        print(i)


if not __name__ == "__main__":
    # step 2 -> rolling window 20 | bin time width 8 | no flatten
    d = []
    ds = []
    for bin_t_w_ in [2, 4, 6, 8]:

        for r_w_ in [10, 15, 20, 25, 30, 35, 40, 45, 50]:
            step = 330000000 + bin_t_w_ * 1000 + r_w_
            ds.append(r_w_)
            d.append(readResult(config.path_results +
                     f"summed_results_{step}.txt"))
        dd = np.array(d).transpose()
        kwargs = [{"color": "r", "label": f"missed strong"},
                  {"color": "b", "label": f"all hits"},
                  {"color": "g", "label": f"false positives"}]

        fig, ax = plt.subplots(figsize=(16, 9))
        tax = plt.twinx(ax)
        tax2 = plt.twinx(ax)
        a = [ax, tax, tax2]
        for j, i in enumerate(dd):
            a[j].scatter(ds, i, **kwargs[j])
            plt.legend()
        plt.show()

    for j, i in enumerate(d):
        if not j % 9:
            print("\n")
        print(i)


if not __name__ == "__main__":
    # step 1 -> rolling window 160 | flatten window 300
    d = []
    ds = []
    for rw in [100, 130, 150, 160, 170, 180, 190, 200, 220, 400]:
        step = 9100000 + rw
        ds.append(rw)
        d.append(readResult(config.path_results +
                 f"summed_results2_{step}.txt"))

    ds.append(1)
    d.append(readResult(config.path_results + f"summed_results2_{1}.txt"))

    e = []
    ds2 = []
    for flat_w in [10, 50, 100, 150, 200, 300, 400, 600, 1000, 3000]:
        step = 9200000 + flat_w
        ds2.append(flat_w)
        e.append(readResult(config.path_results +
                 f"summed_results2_{step}.txt"))

    ds2.append(1)
    e.append(readResult(config.path_results + f"summed_results2_{1}.txt"))

    dd = np.array(d).transpose()
    ee = np.array(e).transpose()

    kwargs = [{"color": "r", "label": f"missed strong"},
              {"color": "b", "label": f"all hits"},
              {"color": "g", "label": f"false positives"}]

    """fig, ax = plt.subplots(figsize=(16, 9))
    tax = plt.twinx(ax)
    tax2 = plt.twinx(ax)
    a = [ax, tax, tax2]
    for j, i in enumerate(dd):
        a[j].scatter(ds, i, **kwargs[j])
    plt.show()

    fig, ax = plt.subplots(figsize=(16, 9))
    tax = plt.twinx(ax)
    tax2 = plt.twinx(ax)
    a = [ax, tax, tax2]
    for j, i in enumerate(ee):
        a[j].scatter(ds2, i, **kwargs[j])
    plt.show()"""

    print(ds)
    print(dd)
    print(ds2)
    print(ee)


if __name__ == "__main__":
    # step 1 -> rolling window 160 | flatten window 300
    d = []
    ds = []
    for rw in [100, 130, 150, 160, 180, 200, 220, 400]:
        step = 12200000 + rw
        ds.append(rw)
        d.append(readResult(config.path_results +
                 f"all_summed_results_{step}.txt"))

    e = []
    ds2 = []
    for flat_w in [10, 50, 100, 150, 200, 400, 1000, 3000]:
        step = 13200000 + flat_w
        ds2.append(flat_w)
        e.append(readResult(config.path_results +
                 f"all_summed_results_{step}.txt"))

    dd = np.array(d).transpose()
    ee = np.array(e).transpose()

    kwargs = [{"color": "r", "label": f"missed strong"},
              {"color": "b", "label": f"all hits"},
              {"color": "g", "label": f"false positives"}]

    """fig, ax = plt.subplots(figsize=(16, 9))
    tax = plt.twinx(ax)
    tax2 = plt.twinx(ax)
    a = [ax, tax, tax2]
    for j, i in enumerate(dd):
        a[j].scatter(ds, i, **kwargs[j])
    plt.show()

    fig, ax = plt.subplots(figsize=(16, 9))
    tax = plt.twinx(ax)
    tax2 = plt.twinx(ax)
    a = [ax, tax, tax2]
    for j, i in enumerate(ee):
        a[j].scatter(ds2, i, **kwargs[j])
    plt.show()"""

    print(ds)
    print(dd)
    print(ds2)
    print(ee)

