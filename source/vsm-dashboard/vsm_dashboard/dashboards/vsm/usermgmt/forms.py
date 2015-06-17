
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

from django.core.urlresolvers import reverse
try:
    from django.utils.translation import force_unicode
except:
    from django.utils.translation import force_text as force_unicode

from django.utils.translation import  ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon.utils.validators import validate_port_range
from horizon.utils import validators
# from horizon.utils import fields
from .utils import get_admin_tenant
import logging
from django.forms import ValidationError
from django import http
from django.conf import settings
from django import shortcuts

from vsm_dashboard.api import vsm as vsm_api
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
        # LOG.error("CEPH_LOG> data %s " % data)
        # data['email'] = ''

        # try:
        #     admin_tenant = get_admin_tenant(request)
        #     tenant_id = admin_tenant.id
        #     ret = api.keystone.user_create(request, data['name'], data['email'],
        #                                    data['password'], tenant_id, enabled=True)
        #     LOG.error("CEPH_LOG> ret: %s " % ret)

        #     roles = api.keystone.role_list(request)
        #     for role in roles:
        #         if role.name in ['admin', 'KeystoneAdmin']:
        #             api.keystone.add_tenant_user_role(request, tenant_id, ret.id, role.id)

        #     LOG.error(api.keystone.user_get(request, ret.id))
        #     messages.success(request,
        #              _('Successfully created user: %s')
        #              % data['name'])
        #     return ret
        # except:
        #     redirect = reverse("horizon:vsm:usermgmt:index")
        #     exceptions.handle(request,
        #                       _('Unable to create User.'),
        #                       redirect=redirect)

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
        # failed, succeeded = [], []
        # user_is_editable = api.keystone.keystone_can_edit_user()
        # user = data.pop('id')
        # tenant = get_admin_tenant(request)

        # if user_is_editable:
        #     password = data.pop('password')
        #     data.pop('confirm_password', None)

        # if user_is_editable:
        #     # Update user details
        #     msg_bits = (_('name'), _('email'))
        #     try:
        #         api.keystone.user_update(request, user, **data)
        #         succeeded.extend(msg_bits)
        #     except:
        #         failed.extend(msg_bits)
        #         exceptions.handle(request, ignore=True)

        # # Update default tenant
        # msg_bits = (_('primary project'),)
        # try:
        #     api.keystone.user_update_tenant(request, user, tenant)
        #     succeeded.extend(msg_bits)
        # except:
        #     failed.append(msg_bits)
        #     exceptions.handle(request, ignore=True)

        # if user_is_editable:
        #     # If present, update password
        #     if password:
        #         msg_bits = (_('password'),)
        #         try:
        #             api.keystone.user_update_password(request, user, password)
        #             succeeded.extend(msg_bits)
        #         except:
        #             failed.extend(msg_bits)
        #             exceptions.handle(request, ignore=True)

        # if succeeded:
        #     messages.success(request, _('User has been updated successfully.'))
        # if failed:
        #     failed = map(force_unicode, failed)
        #     messages.error(request,
        #                    _('Unable to update %(attributes)s for the user.')
        #                      % {"attributes": ", ".join(failed)})
        # LOG.error(request.user.id)
        # LOG.error(user)
        # if request.user.id == user:
        #     response = http.HttpResponseRedirect(settings.LOGOUT_URL)
        #     return response
        # return True

