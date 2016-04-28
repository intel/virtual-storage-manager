# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2014 Intel Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from vsm.api import common
import logging

LOG = logging.getLogger(__name__)

class ViewBuilder(common.ViewBuilder):
    _collection_name = "settings"

    def __init__(self):
        pass

    def basic(self, request, setting):
        #LOG.info("vsm settings api view %s " % setting)

        return {
            "setting": {
                "id": setting.get('id'),
                "name": setting.get('name'),
                "value": setting.get('value'),
            }
        }

    def _detail(self, request, setting):
        #LOG.info("vsm settings api view %s " % setting)
        return {
            "setting": {
                "id": setting['id'],
                "name": setting['name'],
                "value": setting['value'],
                "default_value": setting['default_value']
            }
        }

    def detail(self, request, settings):
        return self._list_view(self._detail, request, settings)

    def index(self, request, settings):
        """Show a list of vsm settings without many details."""
        return self._list_view(self.basic, request, settings)

    def _list_view(self, func, request, settings):
        """Provide a view for a list of vsm settings."""
        s_list = [func(request, setting)["setting"] for setting in settings]
        s_dict = dict(settings=s_list)
        return s_dict

