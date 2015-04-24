# coding=utf-8


import diamond.collector


class CephMetricsCollector(diamond.collector.Collector):

    def get_default_config_help(self):
        config_help = super(ExampleCollector, self).get_default_config_help()
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

        # Set Metric Name
        metric_name = "osd1.iops"
        # Set Metric Value
        metric_value = 343
        # Publish Metric
        self.publish(metric_name, metric_value)
        # Set Metric Name
        metric_name = "osd1.latency"
        metric_value = 343
        self.publish(metric_name, metric_value)
        metric_name = "osd1.bandwidth"
        metric_value = 343
        self.publish(metric_name, metric_value)
