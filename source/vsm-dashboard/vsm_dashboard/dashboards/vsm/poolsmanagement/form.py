
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
from vsm_dashboard.utils.validators import StorageGroupValidator

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
    storage_group = forms.ChoiceField(label=_('Primary Storage Group'), validators=[StorageGroupValidator()])
    replicated_storage_group = forms.ChoiceField(label=_('Replicated Storage Group'), required=False,
                                                 validators=[StorageGroupValidator(replicated=True)],
                                                 error_messages={'invalid': "You should choose \"Default: same as Primary\", if you want to use same storage group"})
    replication_factor = forms.IntegerField(label=_("Replication Factor"),
                                        min_value=1,
                                        help_text=_('The replication'
                                        ' required to set as an integer,'
                                        'the default number is 3'),
                                        required=True)
    max_pg_num_per_osd = forms.IntegerField(label=_("PG Count Factor"),
                                    help_text=_('max pg_num value for per OSD'
                                    ' required to set as an integer,'
                                    'the default number is 100'),
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

    enable_pool_quota = forms.BooleanField(label="Enable Pool Quota",required=False,initial=False)
    pool_quota = forms.IntegerField(label=_("Pool Quota (GB)"),
                           error_messages={
                               'invalid': _("The string may only contain"
                                            " numbers.")},
                           initial=0,
                           max_value=8589934591,
                           required=True
                           )

    def __init__(self, request, *args, **kwargs):
        super(CreatePool, self).__init__(request, *args, **kwargs)
        storage_group_list = [('', _("Select a storage group"))]
        replicated_storage_group_list = [('', _("Default: Same as Primary"))]
        try:
            rsp, group_list= vsm_api.get_storage_group_list(self.request)
            for key in group_list:
                storage_group_list.append((key, group_list[key]))
                replicated_storage_group_list.append((key, group_list[key]))
        except:
            msg = _('Failed to get storage_group_list.')
            redirect = reverse(self.failure_url)
            exceptions.handle(request, msg, redirect=redirect)
            return False
        self.fields['storage_group'].choices = storage_group_list
        self.fields['replicated_storage_group'].choices = replicated_storage_group_list

    def handle(self, request, data):
        pass

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
                           max_value=8589934591,
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
        pass

class AddCacheTier(forms.SelfHandlingForm):

    failure_url = 'horizon:vsm:poolsmanagement:index'
    cache_tier_pool = forms.ChoiceField(label=_('Cache Tier Pool'))
    storage_tier_pool = forms.ChoiceField(label=_('Storage Tier Pool'))
    cache_mode = forms.ChoiceField(label=_('Cache Mode'))
    force_nonempty = forms.BooleanField(label="FORCE NONEMPTY",required=False,initial=False)
    hit_set_type = forms.ChoiceField(label=_('Hit Set Type'))
    hit_set_count = forms.CharField(label=_("Hit set count"))
    hit_set_period_s = forms.CharField(label=_("Hit set period(s)"))
    target_max_mem_mb = forms.CharField(label=_("Target maximum memory(MB)"))
    target_dirty_ratio = forms.CharField(label=_("Target dirty ratio"))
    target_full_ratio = forms.CharField(label=_("Target full ratio"))
    target_max_objects = forms.CharField(label=_("Target maximum objects"))
    target_min_flush_age_m = forms.CharField(label=_("Target minimum flush age(m)"))
    target_min_evict_age_m = forms.CharField(label=_("Target minimum evict age(m)"))

    def __init__(self, request, *args, **kwargs):
        super(AddCacheTier, self).__init__(request, *args, **kwargs)
        cache_tier_pool_list = [('',"Select a Cache Tier Pool")]
        storage_tier_pool_list = [('',"Select a Storage Tier Pool")]
        cache_mode_list = [('',"Select Cache Tier Mode"), ('writeback', "Writeback"), ('readonly', "Read-only")]
        hit_set_type_list = [('bloom', "bloom")]
        pools = vsm_api.pool_status(request)
        cache_tier_pool_list += [(pool.pool_id, pool.name) for pool in pools if not pool.cache_tier_status]
        storage_tier_pool_list += [(pool.pool_id, pool.name) for pool in pools if not pool.cache_tier_status]
        self.fields['cache_tier_pool'].choices = cache_tier_pool_list
        self.fields['storage_tier_pool'].choices = storage_tier_pool_list
        self.fields['cache_mode'].choices = cache_mode_list
        self.fields['hit_set_type'].choices = hit_set_type_list
        settings = vsm_api.get_settings(request)
        setting_dict = dict([(setting.name, setting.value) for setting in settings])
        self.fields['hit_set_count'].initial = setting_dict["ct_hit_set_count"]
        self.fields['hit_set_period_s'].initial = setting_dict["ct_hit_set_period_s"]
        self.fields['target_max_mem_mb'].initial = setting_dict["ct_target_max_mem_mb"]
        self.fields['target_dirty_ratio'].initial = setting_dict["ct_target_dirty_ratio"]
        self.fields['target_full_ratio'].initial = setting_dict["ct_target_full_ratio"]
        self.fields['target_max_objects'].initial = setting_dict["ct_target_max_objects"]
        self.fields['target_min_flush_age_m'].initial = setting_dict["ct_target_min_flush_age_m"]
        self.fields['target_min_evict_age_m'].initial = setting_dict["ct_target_min_evict_age_m"]

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

