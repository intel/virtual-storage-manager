
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
from vsm_dashboard.utils.validators import validate_pool_name
from vsm_dashboard.utils.validators import StorageGroupValidator

LOG = logging.getLogger(__name__)

class CreateConfigurationForm(forms.SelfHandlingForm):
    failure_url = 'horizon:vsm:configuration:index'
    name = forms.CharField(label=_("Name"),
            max_length=255,
            min_length=1,
            error_messages={
            'required': _('This field is required.'),
            'invalid': _("Please enter a vaild name")},
          )
    section = forms.ChoiceField(label=_('Section'), 
          )
    default_value = forms.CharField(label=_("Default Value"),
           max_length=255,
           min_length=1,
           error_messages={
           'required': _('This field is required.'),
           'invalid': _("Please enter a vaild default value")},
          )
    current_value = forms.CharField(label=_("Current Value"),
           max_length=255,
           min_length=1,
           error_messages={
           'required': _('This field is required.'),
           'invalid': _("Please enter a vaild current value")},
          )
    def __init__(self, request, *args, **kwargs):
        super(CreateConfigurationForm, self).__init__(request, *args, **kwargs)
        section_list = [
            ('',_("Select a section")),
            ('global',_("global")),
            ('mon',_("mon")),
            ('osd',_("osd")),
            ('mds',_("mds")),
        ]
        self.fields['section'].choices = section_list

    def handle(self, request, data):
        pass


class UpdateConfigurationForm(forms.SelfHandlingForm):
    failure_url = 'horizon:vsm:configuration:index'
    name = forms.CharField(label=_("Name"),
            max_length=255,
            min_length=1,
            error_messages={
            'required': _('This field is required.'),
            'invalid': _("Please enter a vaild name")},
          )
    section = forms.ChoiceField(label=_('Section'), 
          )
    default_value = forms.CharField(label=_("Default Value"),
           max_length=255,
           min_length=1,
           error_messages={
           'required': _('This field is required.'),
           'invalid': _("Please enter a vaild default value")},
          )
    current_value = forms.CharField(label=_("Current Value"),
           max_length=255,
           min_length=1,
           error_messages={
           'required': _('This field is required.'),
           'invalid': _("Please enter a vaild current value")},
          )
    def __init__(self, request, *args, **kwargs):
        super(UpdateConfigurationForm, self).__init__(request, *args, **kwargs)
        section_list = [
            ('',_("Select a section")),
            ('global',_("global")),
            ('mon',_("mon")),
            ('osd',_("osd")),
            ('mds',_("mds")),
        ]
        self.fields['section'].choices = section_list

    def handle(self, request, data):
        pass
