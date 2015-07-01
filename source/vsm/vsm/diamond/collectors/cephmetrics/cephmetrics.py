# coding=utf-8


import diamond.collector
import glob
import commands

class CephMetricsCollector(diamond.collector.Collector):

    def get_default_config_help(self):
        config_help = super(CephMetricsCollector, self).get_default_config_help()
        config_help.update({
        })
        return config_help

    def get_default_config(self):
        """
        Returns the default collector settings
        """
        config = super(CephMetricsCollector, self).get_default_config()
        config.update({
            'path':     'cephmetric'
        })
        return config

    def collect(self):
        """
        Overrides the Collector.collect method
        """
        asoks = glob.glob("/var/run/ceph/ceph-osd.*.asok")
        for asok in asoks:
            osd_name = asok.split('.')[1]
            try:
                osd_perf_value = commands.getoutput("ceph --admin-daemon %s perf dump"%asok)
                osd_perf_value_dict = eval(osd_perf_value)['osd']
                metrics = {
                    "osd%s.ops_r"%osd_name: osd_perf_value_dict['op_r'],
                    "osd%s.ops_w"%osd_name: osd_perf_value_dict['op_w'],
                    "osd%s.ops_rw"%osd_name: osd_perf_value_dict['op_rw'],
                    "osd%s.latency_r"%osd_name: osd_perf_value_dict['op_r_latency']['avgcount'] and osd_perf_value_dict['op_r_latency']['sum']/osd_perf_value_dict['op_r_latency']['avgcount'] or 0,
                    "osd%s.latency_w"%osd_name: osd_perf_value_dict['op_w_latency']['avgcount'] and osd_perf_value_dict['op_w_latency']['sum']/osd_perf_value_dict['op_w_latency']['avgcount'] or 0,
                    "osd%s.latency_rw"%osd_name: osd_perf_value_dict['op_rw_latency']['avgcount'] and osd_perf_value_dict['op_rw_latency']['sum']/osd_perf_value_dict['op_rw_latency']['avgcount'] or 0,
                    "osd%s.bandwidth_in"%osd_name: osd_perf_value_dict['op_in_bytes'],
                    "osd%s.bandwidth_out"%osd_name: osd_perf_value_dict['op_out_bytes'],
                }
                for key,value in metrics.items():
                    self.publish(key, value)
            except:
                import traceback;traceback.print_exc()
