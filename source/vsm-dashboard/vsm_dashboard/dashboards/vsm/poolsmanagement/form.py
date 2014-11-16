
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
from vsm_dashboard.utils.validators import validate_pool_name

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
                            validators=[validate_pool_name])
    storage_group = forms.ChoiceField(label=_('Storage Group'))
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
                            'required': _('This field is required.'),},
                            #'invalid': _("The string may only contain"
                            #             " ASCII characters and numbers.")},
                            #validators=[validators.validate_slug]
                            )

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
                                _('%s Failed to create storage pool!')
                                % ret['message'])

            return ret
        except:
            redirect = reverse("horizon:vsm:poolsmanagement:index")
            exceptions.handle(request,
                              _('Unable to create storage pool.'),
                              redirect=redirect)

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
    storage_group = forms.ChoiceField(label=_('Storage Group'))
    ec_profile = forms.ChoiceField(label=_('Erasure Coded Profile'))
    ec_failure_domain = forms.ChoiceField(label=_('Erasure Coded Failure Domain'))
    tag = forms.CharField(label=_("Tag"),
                          max_length=16,
                          min_length=1,
                          error_messages={
                              'required': _('This field is required.'),},
                          #'invalid': _("The string may only contain"
                          #             " ASCII characters and numbers.")},
                          #validators=[validators.validate_slug]
    )
    enable_pool_quota = forms.BooleanField(label="Enable Pool Quota",required=False,initial=False)

    pool_quota = forms.IntegerField(label=_("Pool Quota (GB)"),
                           error_messages={
                               'invalid': _("The string may only contain"
                                            " numbers.")},
                           initial=0,
                           required=True
                           )

    def __init__(self, request, *args, **kwargs):
        super(CreateErasureCodedPool, self).__init__(request, *args, **kwargs)
        storage_group_list = [('', _("Select a storage group"))]
        ec_profile_list = [('', _("Select an erasure coded profile"))]
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
        try:
            body = {
                'pool': {
                    'name': data['name'],
                    'storageGroupId': data['storage_group'],
                    'tag': data['tag'],
                    'clusterId': '0',
                    'createdBy': 'VSM',
                    'ecProfileId': data['ec_profile'],
                    'ecFailureDomain': data['ec_failure_domain'],
                    'enablePoolQuota': data['enable_pool_quota'],
                    'poolQuota': data['pool_quota'],
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
                               _('%s Failed to create storage pool!')
                               % ret['message'])

            return ret
        except:
            redirect = reverse("horizon:vsm:poolsmanagement:index")
            exceptions.handle(request,
                              _('Unable to create storage pool.'),
                              redirect=redirect)

class AddCacheTier(forms.SelfHandlingForm):

    failure_url = 'horizon:vsm:poolsmanagement:index'
    cache_tier_pool = forms.ChoiceField(label=_('Cache Tier Pool'), required=False)
    storage_tier_pool = forms.ChoiceField(label=_('Storage Tier Pool'), required=False)
    cache_mode = forms.ChoiceField(label=_('Cache Mode'), required=False)
    hit_set_type = forms.ChoiceField(label=_('Hit Set Type'), required=False)
    hit_set_count = forms.CharField(label=_("Hit set count"), required=False)
    hit_set_period = forms.CharField(label=_("Hit set period(s)"), required=False)
    target_max_mem = forms.CharField(label=_("Target maximum memory(MB)"), required=False)
    target_dirty_ratio = forms.CharField(label=_("Target dirty ratio"), required=False)
    target_full_ratio = forms.CharField(label=_("Target full ratio"), required=False)
    target_max_capacity = forms.CharField(label=_("Target maximum capacity(GB)"), required=False)
    target_max_objects = forms.CharField(label=_("Target maximum objects"), required=False)
    target_minimum_flush_age = forms.CharField(label=_("Target minimum flush age(m)"), required=False)
    target_minimum_evict_age = forms.CharField(label=_("Target minimum evict age(m)"), required=False)

    def __init__(self, request, *args, **kwargs):
        super(AddCacheTier, self).__init__(request, *args, **kwargs)
        cache_tier_pool_list = [('',"Select a Cache Tier Pool")]
        storage_tier_pool_list = [('',"Select a Storage Tier Pool")]
        cache_mode_list = [('',"Select Cache Tier Mode"), ('writeback', "Writeback"), ('readonly', "Read-only")]
        hit_set_type_list = [('',"Select Hit Set type"), ('bloom', "bloom")]
        pools = vsm_api.pool_status(request)
        cache_tier_pool_list += [(pool.pool_id, pool.name) for pool in pools if not pool.cache_tier_status]
        storage_tier_pool_list += [(pool.pool_id, pool.name) for pool in pools if not pool.cache_tier_status]
        self.fields['cache_tier_pool'].choices = cache_tier_pool_list
        self.fields['storage_tier_pool'].choices = storage_tier_pool_list
        self.fields['cache_mode'].choices = cache_mode_list
        self.fields['hit_set_type'].choices = hit_set_type_list

    def handle(self, request, data):

        try:
            body = {
                'cache_tier': {
                    'storage_pool_id': data['storage_tier_pool'],
                    'cache_pool_id': data['cache_tier_pool'],
                    'cache_mode': data['cache_mode']
                    }
            }
            if(data['cache_tier_pool'] == data['storage_tier_pool']):
                messages.error(request,
                                 _('Failed to add cache tier: cache_pool, storage_pool cannot be the same!'))
                return False

            ret = vsm_api.add_cache_tier(request,body=body)

            messages.success(request,
                                 _('Successfully add cache tier: '))
            return True
        except:
            redirect = reverse("horizon:vsm:poolsmanagement:index")
            exceptions.handle(request,
                              _('Unable to add a cache tier.'),
                              redirect=redirect)

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

        try:
            body = {
                'cache_tier': {
                    'cache_pool_id': data['cache_tier_pool'],
                    }
            }

            ret = vsm_api.remove_cache_tier(request,body=body)

            messages.success(request,
                                 _('Successfully remove cache tier: '))
            return True
        except:
            redirect = reverse("horizon:vsm:poolsmanagement:index")
            exceptions.handle(request,
                              _('Unable to remove cache tier.'),
                              redirect=redirect)

