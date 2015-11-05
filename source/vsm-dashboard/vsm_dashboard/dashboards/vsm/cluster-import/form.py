
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

from django.core import validators
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon.utils.validators import validate_port_range
import logging

from vsm_dashboard.api import vsm as vsm_api

LOG = logging.getLogger(__name__)

class ImportCluster(forms.SelfHandlingForm):
    failure_url = 'horizon:vsm:cluster-import:index'
    monitor_host = forms.ChoiceField(label=_("Monitor Host"),
                                    required=True)
    monitor_keyring = forms.CharField(label=_("Monitor Keyring"),
                                    max_length=255,
                                    min_length=1,
                                    required=True)
    cluster_conf = forms.CharField(label=_("Cluster Conf"),
                                    max_length=255,
                                    min_length=1,
                                    required=True)
    def __init__(self, request, *args, **kwargs):
        super(ImportCluster, self).__init__(request, *args, **kwargs)
        monitor_list = []
        try:
            #get the serverlist
            _servers = vsm_api.get_server_list(self.request,)
            for _server in _servers:
                if "monitor" in _server.type:
                    monitor_list.append((_server.id,_server.host))
        except:
            msg = _('Failed to get server_list.')
            redirect = reverse(self.failure_url)
            exceptions.handle(request, msg, redirect=redirect)
            return False
        self.fields["monitor_host"].choices = monitor_list

    def handle(self,request,data):
        pass