# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2014 Intel Inc.
# All Rights Reserved.
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


from vsm.common import constant
from vsm import utils

def get_ceph_version():
    """

    Get the ceph version from ceph cluster.
    Run command "ceph --version" to get it.

    :return: string: version
    """

    args = ["ceph",
            "--version"]
    try:
        out, err = utils.execute(*args, run_as_root=True)
        version = out.split(" ")[2]
    except:
        version = ""
    return version

def get_ceph_version_code():
    """

    Get the ceph version first from funtion get_ceph_version.
    Then analyze and return the ceph version code.

    :return: string: code
    """

    code = "firefly"
    version = get_ceph_version()
    prefix_version = ".".join(version.split(".")[0:2])
    for k,v in constant.CEPH_VERSION_CODE:
        if prefix_version == k:
            code = v
    return code
