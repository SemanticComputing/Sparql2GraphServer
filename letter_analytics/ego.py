import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import entropy
from collections import OrderedDict, defaultdict, Counter
from .analytics import str_to_timestamp, timestamp_to_date, ego_reciprocity


class EgoAnalytics(object):
    """
    Main view for ego networks. Obtains timelines, and interacts with social signature.
    Either query or ego networks must provided
    Inputs -
    node - str for node name
    egos - dict containing 'out_ego' and 'in_ego' dicts, where the keys are nodes and the values are lists with timestamps ()
    query - sparql query resuts that includes incoming and outgoing letters to 'node', including timestamps
    """
    def __init__(self, node, egos={}, query=''):
        self.node = node
        if not egos:
            assert query, "Either out_ego and in_ego, must be provided, or query results"
            egos = self._query_to_egos(query)
        self.out_ego = egos['out_ego']
        self.in_ego = egos['in_ego']

    def _query_to_egos(self, query):
        """
        Convert query of outgoing letters onto dictionary of timestamps, separating incoming and outgoing calls.
        Input-
        query: json that of the form
            {'results': {'bindings': list of dicts}}
            where each dict includes 'target' (a target node)
            'time_0'
        Output-
        egos: dict of dicts with incoming and outgoing letters
        """

        out_times = defaultdict(list)
        in_times = defaultdict(list)
        for out_node in query['results']['bindings']:
            if self.node in out_node['id']['value']:
                target = out_node['target']['value']
                time = str_to_timestamp(out_node['time_0']['value'])
                out_times[target] += [time]
            else:
                idn = out_node['id']['value']
                time = str_to_timestamp(out_node['time_0']['value'])
                in_times[idn] += [time]
        egos = {'out_ego': out_times,
                'in_ego': in_times}
        return egos


    def timeline(self, ego):
        ts = sorted([date for node in ego.values() for date in node])
        return ts


    def plot_timelines(self):
        out_ts = self.timeline(self.out_ego)
        in_ts = self.timeline(self.in_ego)
        fig, ax = plt.subplots(figsize=(10, 4))

        self._basic_timeline_plot(out_ts, ax, 'b', 'Sent')
        self._basic_timeline_plot(in_ts, ax, 'r', 'Received')
        ax.legend(loc=0)
        return fig, ax


    def _basic_timeline_plot(self, ts, ax, col, label):
        y_ts = [timestamp_to_date(t).year for t in ts]
        y_c = Counter(y_ts)
        years = sorted(list(y_c.keys()))
        vals = [y_c[y] for y in years]
        ax.plot(years, vals, c=col, label=label)


    def social_signature(self, bin_type='year', bin_n=5, max_rank=20):
        ss = SocialSignature(self.node, self.out_ego, bin_type, bin_n, max_rank)
        self.ss = ss


    def dynamic_attractiveness(self, bin_type='year', bin_n=5):
        #TODO: correct this so that dynamic ego doenst need 'egos', but we can pass only one
        egos = {'out_ego': self.out_ego, 'in_ego': self.in_ego}
        da = DynamicAttv(self.node, egos, bin_type, bin_n)
        self.da = da


class DynamicEgo(object):
    """
    Basic class for dynamic ego data. Basis for SocialSingature and DynamicAttrv
    """
    def __init__(self, node, egos, bin_type='linear', bin_n=3, kind='out'):
        self.node = node
        self.bin_type = bin_type
        self.bin_n = bin_n
        self.egos = {}
        self._get_times(egos, kind)

        if bin_type is not None:
            self._get_bin_edges(bin_type, bin_n)


    def _get_times(self, egos, kind):
        if kind == 'out':
            self.times = egos #egos['out_ego']
        elif kind == 'in':
            self.times = egos #egos['in_ego']
        elif kind == 'all':
            times = {k: egos['in_ego'].get(k, []) + egos['out_ego'].get(k, []) for \
                    k in set(egos['in_ego']) | set(egos['out_ego'])}
            self.times = times
            self.egos = egos
        else:
            self.egos = {}

    def _get_bin_edges(self, bin_type, bin_n):
        """
        Create bins, where social sigunatures will be calculated
        """
        s_times = sorted([t for time in self.times.values() for t in time])
        if bin_type == 'linear':
            self.edges = np.linspace(s_times[0] - 1, s_times[-1], bin_n + 1)
        elif bin_type == 'distribution':
            quantiles = np.linspace(0, 100, bin_n + 1)
            self.edges = np.percentile(s_times, quantiles)
            self.edges[0] =- 1 # Edge correction
        elif bin_type == 'year':
            bin_size = 365.25 *  bin_n
            self.edges = np.arange(int(s_times[0]-1), int(s_times[-1]) + bin_size, bin_size)
        else:
            raise TypeError("'bin_type' must be either 'linear', 'distribution' or 'year'")

    def jaccard_similarity(self, sa, sb):
        if (len(sa) == 0) or (len(sb) == 0):
            return np.nan
        sa = set(list(sa.keys())[:self.max_rank])
        sb = set(list(sb.keys())[:self.max_rank])
        try:
            sab = len(sa.intersection(sb)) / len(sa.union(sb))
        except ZeroDivisionError:
            sab = 0
        return sab


    def get_year_edges(self):
        """
        Return bin edges in years
        """
        y_edges = []
        for edge in self.edges:
            year = timestamp_to_date(int(edge)).year
            y_edges.append(year)

        return y_edges


class SocialSignature(DynamicEgo):
    def __init__(self, node, egos, bin_type='linear', bin_n=3, max_rank=20, ns=True):
        """
        node: focus node
        ego_times: dict of outgoing letters
        bin_type: 'linear', 'distribution' or 'year'
        bin_n: number of cuts for linear/distribution edge types, or number of years to cut for
        max_rank: maximum number of alters in the social signature
        """
        super().__init__(node, egos, bin_type, bin_n, kind='out')
        self.max_rank = max_rank
        self._get_signatures()
        self.get_avg_signature()
        if ns:
            self.get_neighbor_similarity()


    def update(self, bin_type, bin_n, sim=True, avg=True):
        """
        Update the social signature with new binning
        bin_type = 'linar', 'distribution' or 'year'
        bin_n = if 'linear' or 'distribution', the number of bins;\
                if 'year', the nunber of years in each bin
        sim: if True, compute neighbor similarity (self.ns and self.jsd)
        avg: if True, compute average social signature (self.average_signature)
        """
        self.bin_type = bin_type
        self.bin_n = bin_n
        self._get_bin_edges(bin_type, bin_n)
        self._get_signatures()
        if avg:
            self.get_avg_signature()
        if sim:
            self.get_neighbor_similarity()


    def add_reference_distance(self, ref):
        assert len(ref) == self.max_rank, "Ref. distribution must be of size 'max_rank'"
        self.reference = ref
        self.dist_ref = self.js(ref, self.average_signature)
        if self.jsd is None:
            dist_self = []
            for i, sgn in self.t_signatures.items():
                ref_i = self.get_avg_signature(i)
                dist_self.append(self.js(ref_i, sgn.values()))
            self.dist_self = np.mean(dist_self)
        else:
            self.dist_self = np.mean(self.jsd.diagonal())


    def _create_signature(self, times):
        x = dict((k, len(time)) for k, time in times.items())
        l = sum(x.values())
        signature = OrderedDict((k, v/l) for k, v in sorted(x.items(), key=lambda item: item[1], reverse=True))
        return signature


    def _get_signatures(self):
        """
        Calculate social signatures for each bin
        """
        t_signatures = {i: {} for i in range(len(self.edges) - 1)}
        w_signatures = {i: 0 for i in range(len(self.edges) - 1)}
        for neigh, ts in self.times.items():
            sgn_ts = np.digitize(ts, self.edges, True) - 1
            for t, sgn in zip(ts, sgn_ts):
                t_signatures[sgn].setdefault(neigh, []).append(t)
                w_signatures[sgn] += 1

        self.total_letters = sum(w_signatures.values())
        w_signatures = {k: w/self.total_letters for k, w in w_signatures.items()}
        t_signatures = {k: self._create_signature(v) for k, v in t_signatures.items()}

        self.w_signatures = w_signatures
        self.t_signatures = t_signatures

    def _entropy(self, p):
        return - sum([pi * np.log(pi) for pi in p])

    def js(self, p, q):
        """
        Jensen-Shannon Divergence for measuring differences between distributions
        """
        if (len(p) == 0) or (len(q)) == 0:
            return np.nan
        if len(p) < self.max_rank:
            p = list(p) + [0.] * (self.max_rank - len(p))
        else:
            p = list(p)[:self.max_rank]
        if len(q) < self.max_rank:
            q = list(q) + [0.] * (self.max_rank - len(q))
        else:
            q = list(q)[:self.max_rank]
        p, q = np.array(p), np.array(q)
        p /= p.sum()
        q /= q.sum()
        m = (p + q) / 2
        jsd = entropy((p + q)/2) - (entropy(p) + entropy(q)) / 2
        return np.sqrt(jsd)

    def get_neighbor_similarity(self):
        """
        Jaccard Similarity for the set of neighbors at different times. Allowing to \
                check whether the set of neighbors changes at different times.
        """
        n_sgn = len(self.t_signatures)
        ns = np.zeros((n_sgn, n_sgn))
        jsd = ns.copy()
        for i in range(n_sgn):
            ref_i = self.get_avg_signature(i)
            js_ii = self.js(ref_i, self.t_signatures[i].values())
            jsd[i, i] = js_ii
            for j in range(i + 1, n_sgn):
                s_ij = self.jaccard_similarity(self.t_signatures[i], self.t_signatures[j])
                js_ij = self.js(self.t_signatures[i].values(), self.t_signatures[j].values())
                ns[i, j] = s_ij
                jsd[i, j] = js_ij

        self.ns = ns
        self.jsd = jsd

    def get_avg_signature(self, remove=None):
        """
        Compute average social signature. If remove is an int, compute the
        avg soc sign without the signature of time 'remove'
        """
        n_sign = len(self.t_signatures)
        av_ss = np.zeros(self.max_rank)
        for k, v in self.t_signatures.items():
            if k != remove:
                lv = len(v)
                if lv >= self.max_rank:
                    hpr = list(v.values())[:self.max_rank]
                if lv < self.max_rank:
                    hpr = list(v.values()) + [0.] * (self.max_rank - lv)
                av_ss += self.w_signatures[k] * np.array(hpr)

        if remove is None:
            self.average_signature = av_ss
        else:
            return (1/self.w_signatures[remove]) * av_ss if \
                    self.w_signatures[remove] > 0 else av_ss


    def plot_signature(self, signature, ax=None):
        if ax is None:
            fig, ax = plt.subplots(1)
        y = list(signature.values())[:self.max_rank]
        ax.plot(y, '.')
        if self.average_signature is not None:
            idx = self.average_signature > 0
            ax.plot(self.average_signature[idx], alpha=.2, c='grey')
        return ax

    def plot_all_signatures(self):
        fig, axs = plt.subplots(len(self.t_signatures))
        for k, t in self.t_signatures.items():
            self.plot_signature(t, axs[k])


class DynamicAttv(DynamicEgo):
    def __init__(self, node, egos, bin_type, bin_n):
        super().__init__(node, egos, bin_type, bin_n, kind='all')
        self._get_net_attractiveness()

    def _get_net_attractiveness(self):
        """
        Calculate netowrk attractiveness (statistics on interaction) for each bin
        """
        in_sets = self._ego_to_temporal(self.egos['in_ego'])
        out_sets = self._ego_to_temporal(self.egos['out_ego'])
        t_stats = {}
        for t, in_set in in_sets.items():
            t_stats[t] = ego_reciprocity(in_set, out_sets[t])
        self.t_stats = t_stats


    def _ego_to_temporal(self, ego):
        """
        Convert simple ego network to a series of ego networks defined by self.edges
        """
        t_egos = {i: {} for i in range(len(self.edges) - 1)}
        for neigh, ts in ego.items():
            sgn_ts = np.digitize(ts, self.edges, True) - 1
            for t, sgn in zip(ts, sgn_ts):
                try:
                    t_egos[sgn][neigh] += 1
                except:
                    t_egos[sgn][neigh] = 1
                #t_egos[sgn].setdefault(neigh, 1) = 1
        return t_egos


    def update(self, bin_type, bin_n):
        """
        Update the social signature with new binning
        bin_type = 'linar', 'distribution' or 'year'
        bin_n = if 'linear' or 'distribution', the number of bins;\
                if 'year', the nunber of years in each bin
        """
        self.bin_type = bin_type
        self.bin_n = bin_n
        self._get_bin_edges(bin_type, bin_n)
        self._get_net_attractiveness()


    def plot(self):
        fig, axs = plt.subplots(3, 1, sharex=True)
        out_w = self._parse_stat('out_w')
        att_b = self._parse_stat('att_b')
        bal = self._parse_stat('bal')

        self._basic_plot(axs[0], 'out_w', out_w)
        self._basic_plot(axs[1], 'att_b', att_b)
        self._basic_plot(axs[2], 'bal', bal)

        return fig, axs


    def _parse_stat(self, stat_key):
        stat_ts = [t_stats[stat_key] for t_stats in self.t_stats.values()]


    def _basic_plot(self, ax, ax_key, data):
        ax.plot(self.edges[1:], data, label=ax_key)



def read_ego(node):
    """
    Read ego network of sent letters for node
    """
    #TODO: erase this function, replaced by queries
    ego = defaultdict(list)
    ego_in = defaultdict(list)
    with open(logs, 'r') as r:
        line = r.readline()
        t = line.split('|')
        t0_idx, t1_idx, time_idx = t.index('source'), t.index('target'), t.index('start\n')
        while line:
            t = line.split('|')
            if t[t0_idx] == node:
                ego[t[t1_idx]] += [str_to_timestamp(t[time_idx])]
            if t[t1_idx] == node:
                ego_in[t[t0_idx]] += [str_to_timestamp(t[time_idx])]
            line = r.readline()
        ego = {k: sorted(v) for k, v in ego.items()}
        ego_in = {k: sorted(v) for k, v in ego_in.items()}
    return ego, ego_in


if __name__ == '__main__':
    import argparse
    import json
    from os import path

    parser = argparse.ArgumentParser()
    parser.add_argument('--node', default='cccc8972-7adb-463d-b039-bcee2898b222', type=str) #John Locke
    parser.add_argument('--bin_type', default='year', type=str)
    parser.add_argument('--bin_n', default=2, type=int)
    parser.add_argument('--savepath', default='', type=str)
    pargs = parser.parse_args()
    node, bin_type, bin_n, savepath = pargs.node, pargs.bin_type, pargs.bin_n, pargs.savepath

    ego = read_ego(node)
    a = SocialSignature(node, ego, bin_type=bin_type, bin_n=bin_n)
    a.get_avg_signature()
    a.get_neighbor_similarity()

    if savepath:
        spath = path.join(savepath, 'signatures.json')
        with open(spath, 'w') as f:
            json.dump(a.t_signatures, f)


