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

from vsmclient import exceptions as vsmclient
from keystoneclient import exceptions as keystoneclient

UNAUTHORIZED = (keystoneclient.Unauthorized,
                keystoneclient.Forbidden,
                vsmclient.Unauthorized,
                vsmclient.Forbidden)

NOT_FOUND = (keystoneclient.NotFound,
             vsmclient.NotFound)

# NOTE(gabriel): This is very broad, and may need to be dialed in.
RECOVERABLE = (keystoneclient.ClientException,
               # AuthorizationFailure is raised when Keystone is "unavailable".
               keystoneclient.AuthorizationFailure,
               vsmclient.ClientException)
