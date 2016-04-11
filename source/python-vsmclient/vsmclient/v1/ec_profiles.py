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
RBDGroup interface.
"""

import urllib
from vsmclient import base


class ECProfile(base.Resource):
    """A ECProfile is an extra block level storage to the OpenStack instances."""
    def __repr__(self):
        return "<ECProfile: %s>" % self.id

class ECProfilesManager(base.ManagerWithFind):
    """
    Manage :class:`ECProfile` resources.
    """
    resource_class = ECProfile



    def list(self, detailed=True, search_opts=None, paginate_opts=None):
        """
        Get a list of all ECProfile.

        :rtype: list of :class:`ECProfile`
        """
        if search_opts is None:
            search_opts = {}

        if paginate_opts is None:
            paginate_opts = {}

        qparams = {}

        for opt, val in search_opts.iteritems():
            if val:
                qparams[opt] = val

        for opt, val in paginate_opts.iteritems():
            if val:
                qparams[opt] = val

        query_string = "?%s" % urllib.urlencode(qparams) if qparams else ""

        detail = ""
        if detailed:
            detail = "/detail"

        ret = self._list("/ec_profiles%s%s" % (detail, query_string),
                          "ec_profiles")
        return ret


    def ec_profile_create(self, body):
        '''
        :param request:
        :param body:{'ec_profiles':[
                            {'name':,#
                            'plugin':,#...
                            ]
                    }
        :return:
        '''
        url = '/ec_profiles/ec_profile_create'
        return self.api.client.post(url, body=body)

    def ec_profile_update(self, body):
        '''
        :param request:
        :param body:{'ec_profiles':[
                            {'name':,#
                            'plugin':,#
                            'id':,
                            ]
                    }
        :return:
        '''
        url = '/ec_profiles/ec_profile_update'
        return self.api.client.post(url, body=body)

    def ec_profiles_remove(self, body):
        '''
        :param request:
        :param body:{'ec_profiles':[2,]}
        :return:
        '''
        url = '/ec_profiles/ec_profiles_remove'
        return self.api.client.post(url, body=body)

