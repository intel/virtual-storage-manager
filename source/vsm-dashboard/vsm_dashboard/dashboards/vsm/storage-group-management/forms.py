
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
from vsm_dashboard.utils.validators import validate_storage_group_name

LOG = logging.getLogger(__name__)

class CreateStorageGroupForm(forms.SelfHandlingForm):

    failure_url = 'horizon:vsm:storage-group-management:index'
    name = forms.CharField(label=_("Storage Group name"),
                            max_length=255,
                            min_length=1,
                            error_messages={
                            'required': _('This field is required.'),
                            'invalid': _("The string may only contain"
                                         " letters ,numbers, dot and underline")},
                            validators=[validate_storage_group_name])
    friendly_name = forms.CharField(label=_("Storage Group Friendly name"),
                            max_length=255,
                            min_length=1,
                            error_messages={
                            'required': _('This field is required.'),
                            'invalid': _("The string may only contain"
                                         " letters ,numbers, dot and underline")},
                            validators=[validate_storage_group_name])
    storage_class = forms.CharField(label=_("Storage Class"),
                            max_length=24,
                            min_length=1,
                            error_messages={
                            'required': _('This field is required.'),
                            'invalid': _("The string may only contain"
                                         " letters ,numbers, dot and underline")},
                            validators=[validate_storage_group_name])

    def handle(self, request, data):
        # TODO deliver a cluster id in data
        data['cluster_id'] = 1
        #try:
        if True:
            LOG.debug("DEBUG in storage groups, %s" % str(data))
            body = {
                    'storage_group': {
                        'name': data['name'],
                        'friendly_name': data['friendly_name'],
                        'storage_class': data['storage_class'],
                        'cluster_id': data['cluster_id']
                    }
            }
            LOG.debug("DEBUG in handle body %s" % str(body))
            rsp = vsm_api.storage_group_create(request, body=body)
            LOG.debug("DEBUG in storage groups" + str(rsp))

            messages.success(request,
                     _('Successfully created Storage Group: %s')
                     % data['name'])
            return True
        #except:
        #    redirect = reverse("horizon:vsm:storage-group-management:index")
        #    exceptions.handle(request,
        #                      _('Unable to create Storage Group.'),
        #                      redirect=redirect)

