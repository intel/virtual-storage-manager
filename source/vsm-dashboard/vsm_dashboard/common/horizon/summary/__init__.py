
# Copyright 2014 Intel Corporation, All Rights Reserved.

# Licensed under the Apache License, Version 2.0 (the"License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#  http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied. See the License for the
# specific language governing permissions and limitations
# under the License.

from django import template
from django.views.generic import View
import logging
LOG = logging.getLogger(__name__)

class SummaryRenderer(View):
    def __init__(self, request):
        self.request = request

    def render(self):
        summary_template = template.loader.get_template("vsm/summary.html")

        try:
            datas = self.get_summary()
        except Exception,e:
            datas = {}
            #LOG.info("CRITICAL: %s"%e)
            #LOG.error(e)

        try:
            summary_list = self.get_summary_list()
        except Exception,e:
            summary_list = []

        context = template.Context({"name": self.name,
                                    "verbose_name": self.verbose_name,
                                    "detail": getattr(self, "detail", None),
                                    "datas": datas,
                                    "summary_list": summary_list})
        return summary_template.render(context)
