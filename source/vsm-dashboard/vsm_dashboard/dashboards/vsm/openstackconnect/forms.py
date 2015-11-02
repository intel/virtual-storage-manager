
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

from django.utils.translation import ugettext_lazy as _

from horizon import forms

LOG = logging.getLogger(__name__)

class AddOpenstackEndpointForm(forms.SelfHandlingForm):

    failure_url = 'horizon:vsm:openstackconnect:index'

    os_tenant_name = forms.CharField(
        label = _("Tenant Name"),
        max_length = 255,
        min_length = 1,
        error_messages = {
            'required': _('This field is required.')
        }
    )
    os_username = forms.CharField(
        label = _("UserName"),
        max_length = 255,
        min_length = 1,
        error_messages = {
            'required': _('This field is required.')
        }
    )
    os_password = forms.CharField(
        label = _("Password"),
        widget=forms.PasswordInput(render_value=False),
        max_length=255,
        min_length=1,
        error_messages = {
            'required': _('This field is required.')
        }
    )
    os_auth_url = forms.CharField(
        label = _("Auth Url"),
        max_length = 255,
        min_length = 1,
        error_messages = {
            'required': _('This field is required.')
        }
    )
    os_region_name = forms.CharField(
        label = _("Region Name"),
        max_length = 255,
        min_length = 0,
        required = False
    )
    ssh_user = forms.CharField(
        label = _("SSH User Name"),
        max_length = 255,
        min_length = 1,
        error_messages = {
            'required': _('This field is required.')
        }
    )

    def handle(self, request, data):
        pass
        # TODO deliver a cluster id in data
        # data['cluster_id'] = 1
        # try:
        #     LOG.info("CEPH_LOG in ADD ip, %s" % str(data))
        #     os_tenant_name = data['os_tenant_name']
        #     os_username = data['os_username']
        #     os_password = data['os_password']
        #     os_auth_url = data['os_auth_url']
        #     ip = os_auth_url.split(":")[1][2:]
        #     appnodes = vsm_api.appnode_list(request)
        #     for appnode in appnodes:
        #         old_os_auth_url = appnode.os_auth_url
        #         old_ip = old_os_auth_url.split(":")[1][2:]
        #         if ip == old_ip:
        #             messages.error(request, "duplicate ip address")
        #             return False
        #     body = {
        #         'appnodes': {
        #             'os_tenant_name': os_tenant_name,
        #             'os_username': os_username,
        #             'os_password': os_password,
        #             'os_auth_url': os_auth_url
        #         }
        #     }
        #     LOG.info("CEPH_LOG in handle body %s" % str(body))
        #     ret = vsm_api.add_appnodes(request, body['appnodes'])
        #
        #     messages.success(request,
        #                      _('Successfully add openstack: %s')
        #                      % data['os_auth_url'])
        #     return ret
        # except:
        #     redirect = reverse("horizon:vsm:openstackconnect:index")
        #     exceptions.handle(request,
        #                       _('Unable to create appnode.'),
        #                       redirect=redirect)

class UpdateOpenstackEndpointForm(forms.SelfHandlingForm):
    id = forms.CharField(label=_("ID"), widget=forms.HiddenInput)

    os_tenant_name = forms.CharField(
        label = _("Tenant Name"),
        max_length = 255,
        min_length = 1,
        error_messages = {
            'required': _('This field is required.')
        }
    )
    os_username = forms.CharField(
        label = _("UserName"),
        max_length = 255,
        min_length = 1,
        error_messages = {
            'required': _('This field is required.')
        }
    )
    os_password = forms.CharField(
        label = _("Password"),
        widget=forms.PasswordInput(render_value=False),
        max_length=255,
        min_length=1,
        error_messages = {
            'required': _('This field is required.')
        }
    )
    os_auth_url = forms.CharField(
        label = _("Auth Url"),
        max_length = 255,
        min_length = 1,
        error_messages = {
            'required': _('This field is required.')
        }
    )
    os_region_name = forms.CharField(
        label = _("Region Name"),
        max_length = 255,
        min_length = 0,
        required = False
    )
    ssh_user = forms.CharField(
        label = _("SSH User Name"),
        max_length = 255,
        min_length = 1,
        error_messages = {
            'required': _('This field is required.')
        }
    )

    def handle(self, request, data):
        pass
        # failed, succeeded = [], []
        # id = data.pop('id')
        # # ip = data.pop('ip')
        # os_tenant_name = data.pop('os_tenant_name')
        # os_username = data.pop('os_username')
        # os_password = data.pop('os_password')
        # os_auth_url = data.pop('os_auth_url')
        # vsm_api.update_appnode(request, id,
        #                        os_tenant_name=os_tenant_name,
        #                        os_username=os_username,
        #                        os_password=os_password,
        #                        os_auth_url=os_auth_url,
        #                        ssh_status="",
        #                        log_info="")
        #
        # messages.success(request, _('OpenStack auth has been updated successfully.'))
        # return True
        #
        # if failed:
        #     failed = map(force_unicode, failed)
        #     messages.error(request,
        #                    _('Unable to update %(attributes)s for the user.')
        #                      % {"attributes": ", ".join(failed)})
        # return True
