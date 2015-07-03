# coding=utf-8


import diamond.collector
import commands
try:
    import json
except ImportError:
    import simplejson as json
import glob
import os
import subprocess

def flatten_dictionary(input, sep='.', prefix=None):
    """Produces iterator of pairs where the first value is
    the joined key names and the second value is the value
    associated with the lowest level key. For example::
    {'a': {'b': 10},
    'c': 20,
    }
    produces::
    [('a.b', 10), ('c', 20)]
    """
    for name, value in sorted(input.items()):
        fullname = sep.join(filter(None, [prefix, name]))
    if isinstance(value, dict):
        for result in flatten_dictionary(value, sep, fullname):
            yield result
    else:
        yield (fullname, value)

class CephMetricsCollector(diamond.collector.Collector):

    def get_default_config_help(self):
        config_help = super(CephMetricsCollector, self).get_default_config_help()
        config_help.update({
        'socket_path': 'The location of the ceph monitoring sockets.'
        ' Defaults to "/var/run/ceph"',
        'socket_prefix': 'The first part of all socket names.'
        ' Defaults to "ceph-"',
        'socket_ext': 'Extension for socket filenames.'
        ' Defaults to "asok"',
        'ceph_binary': 'Path to "ceph" executable. '
        'Defaults to /usr/bin/ceph.',
        })
        return config_help

    def get_default_config(self):
        """
        Returns the default collector settings
        """
        config = super(CephMetricsCollector, self).get_default_config()
        config.update({
        'socket_path': '/var/run/ceph',
        'socket_prefix': 'ceph-',
        'socket_ext': 'asok',
        'ceph_binary': '/usr/bin/ceph',
        })
        return config

    def _get_socket_paths(self,type='all'):
        """Return a sequence of paths to sockets for communicating
        with ceph daemons.
        """
        if type == 'all':
            socket_pattern = os.path.join(self.config['socket_path'],
            (self.config['socket_prefix']
            + '*.' + self.config['socket_ext']))
        else:
            socket_pattern = os.path.join(self.config['socket_path'],
            (self.config['socket_prefix']
            + '%s.*.'%type + self.config['socket_ext']))
        return glob.glob(socket_pattern)

    def _get_counter_prefix_from_socket_name(self, name):
        """Given the name of a UDS socket, return the prefix
        for counters coming from that source.
        """
        base = os.path.splitext(os.path.basename(name))[0]
        if base.startswith(self.config['socket_prefix']):
            base = base[len(self.config['socket_prefix']):]
        return 'ceph.' + base

    def _get_stats_from_socket(self, name):
        """Return the parsed JSON data returned when ceph is told to
        dump the stats from the named socket.
        In the event of an error error, the exception is logged, and
        an empty result set is returned.
        """
        try:
            json_blob = subprocess.check_output(
            [self.config['ceph_binary'],
            '--admin-daemon',
            name,
            'perf',
            'dump',
            ])
        except subprocess.CalledProcessError, err:
            self.log.info('Could not get stats from %s: %s',name, err)
            self.log.exception('Could not get stats from %s' % name)
            return {}
        try:
            json_data = json.loads(json_blob)
        except Exception, err:
            self.log.info('Could not parse stats from %s: %s',name, err)
            self.log.exception('Could not parse stats from %s' % name)
            return {}
        return json_data



    def _publish_stats(self, counter_prefix, stats):
        """Given a stats dictionary from _get_stats_from_socket,
        publish the individual values.
        """
        for stat_name, stat_value in flatten_dictionary(
        stats,
        prefix=counter_prefix,
        ):
            self.publish_gauge(stat_name, stat_value)

    def collect(self):
        """
        Collect stats
        """
        for path in self._get_socket_paths(type='osd'):
            self.log.debug('checking %s', path)
            instance_name = path.split('.')[1]
            osd_perf_value_dict = self._get_stats_from_socket(path)['osd']
            metrics = {
                    "osd%s.ops_r"%instance_name: osd_perf_value_dict['op_r'],
                    "osd%s.ops_w"%instance_name: osd_perf_value_dict['op_w'],
                    "osd%s.ops_rw"%instance_name: osd_perf_value_dict['op_rw'],
                    "osd%s.latency_r"%instance_name: osd_perf_value_dict['op_r_latency']['avgcount'] and osd_perf_value_dict['op_r_latency']['sum']/osd_perf_value_dict['op_r_latency']['avgcount'] or 0,
                    "osd%s.latency_w"%instance_name: osd_perf_value_dict['op_w_latency']['avgcount'] and osd_perf_value_dict['op_w_latency']['sum']/osd_perf_value_dict['op_w_latency']['avgcount'] or 0,
                    "osd%s.latency_rw"%instance_name: osd_perf_value_dict['op_rw_latency']['avgcount'] and osd_perf_value_dict['op_rw_latency']['sum']/osd_perf_value_dict['op_rw_latency']['avgcount'] or 0,
                    "osd%s.bandwidth_in"%instance_name: osd_perf_value_dict['op_in_bytes'],
                    "osd%s.bandwidth_out"%instance_name: osd_perf_value_dict['op_out_bytes'],
                }
            for key,value in metrics.items():
                self.publish(key, value)
        return

