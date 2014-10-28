
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
from vsm_dashboard.utils.validators import validate_zone_name

LOG = logging.getLogger(__name__)

class CreateZoneForm(forms.SelfHandlingForm):

    failure_url = 'horizon:vsm:zonemgmt:index'
    name = forms.CharField(label=_("Zone name"),
                            max_length=255,
                            min_length=1,
                            error_messages={
                            'required': _('This field is required.'),
                            'invalid': _("The string may only contain"
                                         " ASCII characters and numbers.")},
                            validators=[validate_zone_name])

    def handle(self, request, data):
        # TODO deliver a cluster id in data
        data['cluster_id'] = 1
        #try:
        if True:
            LOG.error("DEBUG in zones, %s" % str(data))
            body = {
                    'zone': {
                        'name': data['name'],
                        'cluster_id': data['cluster_id']
                    }
            }
            LOG.error("DEBUG in handle body %s" % str(body))
            rsp, ret = vsm_api.create_zone(request, opts=body)

            LOG.error("DEBUG in handle retsadsa %s" % ret)
            res = str(ret['message']).strip( )
            LOG.error("DEBUG in handle return, %s" % res)
            messages.success(request,
                     _('Successfully created zone: %s')
                     % data['name'])
            return ret
        #except:
        #    redirect = reverse("horizon:vsm:zonemgmt:index")
        #    exceptions.handle(request,
        #                      _('Unable to create zone.'),
        #                      redirect=redirect)

