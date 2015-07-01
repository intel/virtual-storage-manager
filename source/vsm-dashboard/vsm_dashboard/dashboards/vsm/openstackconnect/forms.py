
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
# from horizon.utils import fields
#from horizon.utils import validators

import logging
LOG = logging.getLogger(__name__)

from vsm_dashboard.api import vsm as vsm_api

class AddOpenstackIPForm(forms.SelfHandlingForm):

    failure_url = 'horizon:vsm:openstackconnect:index'
    ip = forms.CharField(label=_("IP"),
                            max_length=255,
                            min_length=1,
                            error_messages={
                            'required': _('This field is required.'),
                            'invalid': _("The string may only contain"
                                         " IP.")},
                            validators=[validators.validate_ipv46_address,])

    def handle(self, request, data):
        pass
        # TODO deliver a cluster id in data
        # data['cluster_id'] = 1
        # try:
        #     LOG.info("CEPH_LOG in ADD ip, %s" % str(data))
        #     appnodes = vsm_api.appnode_list(request)
        #     for appnode in appnodes:
        #         if data['ip'] == appnode.ip:
        #             messages.error(request, "duplicate ip address")
        #             return False
        #     body = {
        #             'appnodes': [data['ip'],]
        #     }
        #     ips = [data['ip'],]
        #     LOG.info("CEPH_LOG in handle body %s" % str(body))
        #     ret = vsm_api.add_appnodes(request, ips)

        #     messages.success(request,
        #              _('Successfully add ip: %s')
        #              % data['ip'])
        #     return ret
        # except:
        #     redirect = reverse("horizon:vsm:zonemgmt:index")
        #     exceptions.handle(request,
        #                       _('Unable to create zone.'),
        #                       redirect=redirect)

class UpdateOpenstackIPForm(forms.SelfHandlingForm):
    id = forms.CharField(label=_("ID"), widget=forms.HiddenInput)

    ip = forms.CharField(label=_("IP"),
                            max_length=255,
                            min_length=1,
                            error_messages={
                            'required': _('This field is required.'),
                            'invalid': _("The string may only contain"
                                         " IP.")},
                            validators=[validators.validate_ipv46_address,])

    def handle(self, request, data):
        pass
        # failed, succeeded = [], []
        # id = data.pop('id')
        # ip = data.pop('ip')
        # vsm_api.update_appnode(request, id, ip=ip, ssh_status="", log_info="")

        # messages.success(request, _('User has been updated successfully.'))
        # return True

        # if failed:
        #     failed = map(force_unicode, failed)
        #     messages.error(request,
        #                    _('Unable to update %(attributes)s for the user.')
        #                      % {"attributes": ", ".join(failed)})
        # return True
