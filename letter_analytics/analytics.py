import numpy as np
from collections import defaultdict
import datetime as dt

"""
Common use functions for serveral views
"""

def str_to_timestamp(dstr):
    """
    Function to convert string of format 'Y-m-d' into timestamp (ordinal number of
    days since 01.01.0001)
    """
    dstr = dstr[:10]
    try:
        d = dt.datetime.strptime(dstr, "%Y-%m-%d")
    except:
        dstr = dstr.split('-')
        try:
            d = dt.datetime(int(dstr[0]), int(dstr[1]), int(dstr[2]))
        except ValueError:
            d = dt.datetime(int(dstr[0]), int(dstr[1]), 28)
    a = d.toordinal()
    return a


def timestamp_to_date(t):
    """
    Convert timestamp (ordinal number of days since date 1.1.1) to datetime obj.
    """
    return dt.date.fromordinal(t)


def iet(times, full=False):
    """
    Inter-event time (IET) statistics
    times: series of timestamps
    full: Boolean. If True, returns the full IET distribution
    Returns -
    mu: mean IET
    std: standard dev. of IET
    ts: IET values.
    """
    stats = {}
    ts = [t1 - t0 for t0, t1 in zip(times[:-1], times[1:])]
    mu = np.mean(ts)
    std = np.std(ts)

    stats['mu'] = mu
    stats['std'] = std
    stats['b'] = (std - mu) / (std + mu) if len(ts) > 2 else np.nan
    stats['ts'] = ts[-1] - ts[0]
    if full:
        stats['iet'] = ts
    return stats

def bursty_cascades(times, dt=30):
    """
    Obtain bursty cascade statstics given a sequence of timestamps

    times: sequence of timestamp events
    dt: delta-t parameter to define an activity burst

    """
    if len(times) > 1:
        e = 1
        e_dist = [] # List containing the distribution of events within a train
        t_dist = [times[0]] # List containing the times of occurence of a train
        for t0, t1 in zip(times[:-1], times[1:]):
            if t1 - t0 < dt:
                e += 1
            else:
                e_dist.append(e)
                e = 1
                t_dist.append(t1)
        e_dist.append(e)
    else:
        t_dist = times
        e_dist = [1]


def ego_reciprocity(in_set, out_set):
    """
    Returns statistics regarding the reciprocity of an ego network
    in_set: dict of neighbors that sent a letter to a node (weights are num. letters)
    out_set: dict of neghbors that received letter from node (weights are num. letters)

    Returns:
    stats: dict where
        - out_w: average node out-weight
        - att_b: attractiveness balance (how a node is sought vs how it seeks the net)
        - s

    """
    stats = {}

    stats['out_w'] = np.mean(list(out_set.values()))
    stats['att_b'] = len(in_set) / len(out_set) if len(out_set) > 0 else len(in_set)
    stats['bal'] = len(set(in_set).intersection(set(out_set))) / \
            len(set(in_set).union(out_set)) if out_set or in_set else np.nan

    return stats


def get_stat(stats, key):
    # Obtain out_w or that data from ego_reciprocity as a list
    return [v[key] for v in stats.values()]



