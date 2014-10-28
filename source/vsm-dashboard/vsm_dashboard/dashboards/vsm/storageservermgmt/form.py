
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
from horizon.utils import fields
import logging

from vsm_dashboard.api import vsm as vsm_api

LOG = logging.getLogger(__name__)

class AddHost(forms.SelfHandlingForm):

    failure_url = 'horizon:vsm:storageservermgmt:index'
    host_name = forms.CharField(label=_("Host name"),
                            max_length=255,
                            min_length=1,
                            error_messages={
                            'required': _('This field is required.'),
                            'invalid': _("The string may only contain"
                                         " ASCII characters and numbers.")},
                            validators=[validators.validate_slug])

    password = forms.CharField(label=_("Password"),
                            widget=forms.PasswordInput(),
                            max_length=255,
                            min_length=1,
                            error_messages={
                            'required': _('This field is required.'),
                            'invalid': _("The string may only contain"
                                         " ASCII characters and numbers.")},
                            validators=[validators.validate_slug])

    server_type = forms.ChoiceField(label=_('Server Type'))
    zone = forms.ChoiceField(label=_('Zone'))

    def __init__(self, request, *args, **kwargs):
        super(AddHost, self).__init__(request, *args, **kwargs)

        self.fields['server_type'].choices = [('storage', 'storage'),
                                              ('monitor', 'monitor'),
                                              ('mixed', 'storage, monitor')]
        self.fields['zone'].choices = [('zone_a', 'zone_a'),
                                              ('zone_b', 'zone_b')]

    def handle(self, request, data):
        try:

            body = {
                    'pool': {
                        'name': data['name'],
                        'storageGroupId': data['storage_group'],
                        'replicationFactor': data['replication_factor'],
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

class AddHosts(forms.SelfHandlingForm):

    failure_url = 'horizon:vsm:storageservermgmt:index'
    host_name = forms.CharField(label=_("Host name"),
                            max_length=255,
                            min_length=1,
                            error_messages={
                            'required': _('This field is required.'),
                            'invalid': _("The string may only contain"
                                         " ASCII characters and numbers.")},
                            validators=[validators.validate_slug])

    password = forms.CharField(label=_("Password"),
                            widget=forms.PasswordInput(),
                            max_length=255,
                            min_length=1,
                            error_messages={
                            'required': _('This field is required.'),
                            'invalid': _("The string may only contain"
                                         " ASCII characters and numbers.")},
                            validators=[validators.validate_slug])

    server_type = forms.ChoiceField(label=_('Server Type'))
    zone = forms.ChoiceField(label=_('Zone'))

    def __init__(self, request, *args, **kwargs):
        super(AddHosts, self).__init__(request, *args, **kwargs)

        self.fields['server_type'].choices = [('storage', 'storage'),
                                              ('monitor', 'monitor'),
                                              ('mixed', 'storage, monitor')]
        self.fields['zone'].choices = [('zone_a', 'zone_a'),
                                              ('zone_b', 'zone_b')]

    def handle(self, request, data):
        try:

            body = {
                    'pool': {
                        'name': data['name'],
                        'storageGroupId': data['storage_group'],
                        'replicationFactor': data['replication_factor'],
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

