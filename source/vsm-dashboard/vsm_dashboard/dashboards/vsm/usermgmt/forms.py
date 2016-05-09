
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

import logging

from horizon import forms
from horizon.utils import validators

from django.forms import ValidationError
from django.conf import settings
try:
    from django.utils.translation import force_unicode
except:
    from django.utils.translation import force_text as force_unicode
from django.utils.translation import  ugettext_lazy as _

from vsm_dashboard import api
from vsm_dashboard.utils.validators import validate_user_name
from vsm_dashboard.utils.validators import password_validate_regrex

LOG = logging.getLogger(__name__)


class BaseUserForm(forms.SelfHandlingForm):
    def __init__(self, request, *args, **kwargs):
        super(BaseUserForm, self).__init__(request, *args, **kwargs)
        # Populate tenant choices

    def clean(self):
        '''Check to make sure password fields match.'''
        data = super(forms.Form, self).clean()
        if 'password' in data:

            if data['password'] != data.get('confirm_password', None):
                raise ValidationError(_('Passwords do not match.'))
        return data

class CreateUserForm(BaseUserForm):

    failure_url = 'horizon:vsm:usermgmt:index'
    name = forms.CharField(label=_("User name"),
           max_length=255,
           min_length=1,
           error_messages={
           'required': _('This field is required.'),
           'invalid': _("Please enter a vaild User Name")},
           validators= [validate_user_name,]
           )
    password = forms.RegexField(label=_("Password"),
            widget=forms.PasswordInput(render_value=False),
            regex=password_validate_regrex,
            required=False,
            max_length=255,
            min_length=8,
            error_messages={'invalid':
                    validators.password_validator_msg()})
    confirm_password = forms.RegexField(label=_("Confirm Password"),
            widget=forms.PasswordInput(render_value=False),
            regex=validators.password_validator(),
            required=False,
            error_messages={'invalid':
                    validators.password_validator_msg()})
#    email = forms.CharField(label=_("Email"),
#            max_length=255,
#            min_length=1,
#            required=False,
#            error_messages={
#                'required': _('This field is required.'),
#                'invalid': _('Please enter an email address.'),
#            },)

    def handle(self, request, data):
        pass


class UpdateUserForm(BaseUserForm):
    id = forms.CharField(label=_("ID"), widget=forms.HiddenInput)
    #name = forms.CharField(label=_("User Name"))
    #email = forms.EmailField(label=_("Email"))
    password = forms.RegexField(label=_("Password"),
            widget=forms.PasswordInput(render_value=False),
            regex=password_validate_regrex,
            required=False,
            error_messages={'invalid':
                    validators.password_validator_msg()})
    confirm_password = forms.CharField(
            label=_("Confirm Password"),
            widget=forms.PasswordInput(render_value=False),
            required=False)

    def __init__(self, request, *args, **kwargs):
        super(UpdateUserForm, self).__init__(request, *args, **kwargs)

        if api.keystone.keystone_can_edit_user() is False:
            for field in ('name', 'email', 'password', 'confirm_password'):
                self.fields.pop(field)

    def handle(self, request, data):
        pass


class UserSettingsForm(forms.SelfHandlingForm):
    pagesize = forms.IntegerField(label=_("Items Per Page"),
                                  min_value=1,
                                  max_value=getattr(settings,
                                                    'API_RESULT_LIMIT',
                                                    1000))

    def __init__(self, *args, **kwargs):
        super(UserSettingsForm, self).__init__(*args, **kwargs)


    def handle(self, request, data):
        pass