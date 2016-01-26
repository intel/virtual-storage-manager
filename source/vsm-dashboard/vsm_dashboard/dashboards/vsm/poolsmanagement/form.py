
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
from vsm_dashboard.utils.validators import validate_pool_name

LOG = logging.getLogger(__name__)

class CreateErasureCodedPool(forms.SelfHandlingForm):

    failure_url = 'horizon:vsm:poolsmanagement:index'
    name = forms.CharField(label=_("Pool name"),
                           max_length=255,
                           min_length=1,
                           error_messages={
                               'required': _('This field is required.'),
                               'invalid': _("The string may only contain"
                                            " ASCII characters and numbers.")},
                           validators=[validate_pool_name])
    tag = forms.CharField(label=_("Tag"),
                          max_length=16,
                          min_length=1,
                          error_messages={
                              'required': _('This field is required.'),})
    storage_group = forms.ChoiceField(label=_('Storage Group'))
    ec_profile = forms.ChoiceField(label=_('Erasure Coded Profile'))
    ec_failure_domain = forms.ChoiceField(label=_('Erasure Coded Failure Domain'))

    def __init__(self, request, *args, **kwargs):
        super(CreateErasureCodedPool, self).__init__(request, *args, **kwargs)
        storage_group_list = []
        ec_profile_list = []
        ec_failure_domain_list = [('osd', "OSD (default)"), ("zone", "Zone"), ('host', "Host")]
        ec_profiles = vsm_api.ec_profiles(self.request)
        for k, v in enumerate(ec_profiles):
            ec_profile_list.append((v['id'], v['name']))
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
        self.fields['ec_profile'].choices = ec_profile_list
        self.fields['ec_failure_domain'].choices = ec_failure_domain_list

    def handle(self, request, data):
        pass


        

class RemoveCacheTier(forms.SelfHandlingForm):

    failure_url = 'horizon:vsm:poolsmanagement:index'
    cache_tier_pool = forms.ChoiceField(label=_('Cache Tier Pool'), required=False)

    def __init__(self, request, *args, **kwargs):
        super(RemoveCacheTier, self).__init__(request, *args, **kwargs)
        cache_tier_pool_list = [('',"Select a Cache Tier Pool")]
        pools = vsm_api.pool_status(request)
        cache_tier_pool_list += [(pool.pool_id, pool.name) for pool in pools if str(pool.cache_tier_status).startswith("Cache pool for")]
        self.fields['cache_tier_pool'].choices = cache_tier_pool_list

    def handle(self, request, data):
        pass

