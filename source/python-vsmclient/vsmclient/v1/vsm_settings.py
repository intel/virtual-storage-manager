#  Copyright 2014 Intel Corporation, All Rights Reserved.
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

"""
VSM Settings interface.
"""

import urllib
from vsmclient import base


class VsmSetting(base.Resource):
    """"""
    def __repr__(self):

        return "<VsmSetting: %s>" % self.id

class VsmSettingsManager(base.ManagerWithFind):
    """
    Manage :class:`VsmSetting` resources.
    """
    resource_class = VsmSetting

    def get(self, name):
        """
        Get a vsm setting by name.

        :param name: the setting name.
        """
        qparams = {}
        if name:
            qparams['name'] = name

        query_string = "?%s" % urllib.urlencode(qparams) if qparams else ""

        return self._get("/vsm_settings/get_by_name%s" % query_string,
                         "setting")

    def list(self, detailed=False, search_opts=None):
        """
        Get a list of all vsm settings.

        :rtype: list of :class:`VsmSettings`
        """
        if search_opts is None:
            search_opts = {}

        qparams = {}

        for opt, val in search_opts.iteritems():
            if val:
                qparams[opt] = val

        query_string = "?%s" % urllib.urlencode(qparams) if qparams else ""

        detail = ""
        if detailed:
            detail = "/detail"

        ret = self._list("/vsm_settings%s%s" % (detail, query_string),
                         "settings")
        return ret

    def create(self, settings=None):

        """
        Create vsm settings.
        Param: a list of vsm settings.
        """

        body = {'setting':  settings}
        return self._create('/vsm_settings', body, 'setting')

