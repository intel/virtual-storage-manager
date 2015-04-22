# coding=utf-8


import diamond.collector


class ExampleCollector(diamond.collector.Collector):

    def get_default_config_help(self):
        config_help = super(ExampleCollector, self).get_default_config_help()
        config_help.update({
        })
        return config_help

    def get_default_config(self):
        """
        Returns the default collector settings
        """
        config = super(ExampleCollector, self).get_default_config()
        config.update({
            'path':     'example'
        })
        return config

    def collect(self):
        """
        Overrides the Collector.collect method
        """

        # Set Metric Name
        metric_name = "iops"
        # Set Metric Value
        metric_value = 343
        # Publish Metric
        self.publish(metric_name, metric_value)
        # Set Metric Name
        metric_name = "latency"
        metric_value = 343
        self.publish(metric_name, metric_value)
        metric_name = "bandwidth"
        metric_value = 343
        self.publish(metric_name, metric_value)