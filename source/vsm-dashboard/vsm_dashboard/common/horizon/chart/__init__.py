
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
import json

class ChartRenderer(View):
    def __init__(self, request):
        self.request = request

    def _get_chart(self):
        return json.dumps(self.get_chart())

    def get_chart(self):
        raise NotImplementedError

    def render(self):
        summary_template = template.loader.get_template("vsm/chart.html")
        context = template.Context({"name": self.name, "datas": self._get_chart()})
        return summary_template.render(context)

