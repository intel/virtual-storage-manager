# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from vsmclient.v1 import appnodes
from vsmclient.tests.unit import utils
from vsmclient.tests.unit.v1 import fakes


cs = fakes.FakeClient()


class AppnodesTest(utils.TestCase):

    def test_create_appnode(self):
        cs.appnodes.create({
            'os_username': 'admin',
            'os_password': 'admin',
            'os_tenant_name': 'admin',
            'os_auth_url': 'http://192.168.100.100:5000/v2.0',
            'os_region_name': 'RegionOne',
            'ssh_user': 'root'
        })
        cs.assert_called('POST', '/appnodes')

    def test_list_appnodes(self):
        ans = cs.appnodes.list()
        cs.assert_called('GET', '/appnodes')
        for an in ans:
            self.assertIsInstance(an, appnodes.AppNode)
