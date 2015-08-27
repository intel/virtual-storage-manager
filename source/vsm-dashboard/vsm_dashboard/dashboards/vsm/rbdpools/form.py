
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
import logging

from vsm_dashboard.api import vsm as vsm_api

LOG = logging.getLogger(__name__)

class CreatePool(forms.SelfHandlingForm):

    failure_url = 'horizon:vsm:poolsmanagement:index'
    name = forms.CharField(label=_("Pool name"),
                            max_length=255,
                            min_length=1,
                            error_messages={
                            'required': _('This field is required.'),
                            'invalid': _("The string may only contain"
                                         " ASCII characters and numbers.")},
                            validators=[validators.validate_slug])
    storage_group = forms.ChoiceField(label=_('Storage Group'))
    openstack_region = forms.ChoiceField(label=_('OpenStack/Region'))
    cinder_volume_host = forms.ChoiceField(label=_('Cinder Volume Host'))
    replication_factor = forms.IntegerField(label=_("Replication Factor"),
                                        min_value=1,
                                        help_text=_('The replication'
                                        ' required to set as an integer,'
                                        'the default number is 3'),
                                        required=True)
    tag = forms.CharField(label=_("Tag"),
                            max_length=16,
                            min_length=1,
                            error_messages={
                            'required': _('This field is required.'),
                            'invalid': _("The string may only contain"
                                         " ASCII characters and numbers.")},
                            validators=[validators.validate_slug])

    def __init__(self, request, *args, **kwargs):
        super(CreatePool, self).__init__(request, *args, **kwargs)
        storage_group_list = [('', _("Select a storage group"))]
        try:
            rsp, group_list= vsm_api.get_storage_group_list(self.request)
            for key in group_list:
                storage_group_list.append((key, group_list[key]))
        except:
            msg = _('Failed to get storage_group_list.')
            redirect = reverse(self.failure_url)
            exceptions.handle(request, msg, redirect=redirect)
            return False
        self.fields['storage_group'].choices = storage_group_list
        self.fields['cinder_volume_host'].choices = [('host1', 'host1'),
                                              ('host2', 'host2')]

    def handle(self, request, data):
        try:

            body = {
                    'pool': {
                        'name': data['name'],
                        'storageGroupId': data['storage_group'],
                        'replicationFactor': data['replication_factor'],
                        'tag': data['tag'],
                        'clusterId': '0',
                        'createdBy': 'VSM'
                    }
            }
            rsp, ret = vsm_api.create_storage_pool(request,body=body)

            res = str(ret['message']).strip( )
            if res.startswith('pool') and res.endswith('created'):
                messages.success(request,
                                _('Successfully created storage pool: %s')
                                % data['name'])
            else:
                messages.error(request,
                                _('Because %s, failed to create storage pool')
                                % ret['message'])

            return ret
        except:
            redirect = reverse("horizon:vsm:poolsmanagement:index")
            exceptions.handle(request,
                              _('Unable to create storage pool.'),
                              redirect=redirect)

