# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2014 Intel Corporation, All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
from django.core.validators import RegexValidator
import re
from django.utils.translation import ugettext_lazy as _

_user_name_re = re.compile("^[A-Za-z0-9\@\.\_]+$")
validate_user_name = RegexValidator(_user_name_re, _("Enter a valid User name! "), "invalid")

password_validate_regrex = "^(?=.*[a-z].*)(?=.*[A-Z].*)(?=.*[0-9].*)(?=.*[!@#$%^&*()\.:;~\\\|\[\]\{\}].*).{8,255}$"

_zone_name_re = re.compile("^[A-Za-z0-9\.\_]+$")
validate_zone_name = RegexValidator(_zone_name_re, _("Enter a valid Zone name! "), "invalid")

_pool_name_re = re.compile("^[A-Za-z0-9\@\.\_]+$")
validate_pool_name = RegexValidator(_pool_name_re, _("Enter a valid Pool name! "), "invalid")

_storage_group_name_re = re.compile("^[A-Za-z0-9\.\_]+$")
validate_storage_group_name = RegexValidator(_storage_group_name_re, _("Enter a valid Zone name! "), "invalid")
