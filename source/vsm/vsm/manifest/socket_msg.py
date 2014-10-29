# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2014 Intel
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

"""
Use socket to transfer msg.
This file is never used. Instead by WSGI interfaces to add Agents.
"""

import socket
import time
import json
from vsm import flags
from vsm.openstack.common import log as logging

LOG = logging.getLogger(__name__)
FLAGS = flags.FLAGS

def _to_json_data(msg):
    """Check the message is already json format."""
    LOG.info('msg = %s' % msg)
    try:
        json.loads(msg)
        return msg
    except TypeError:
        return json.dumps(msg)

class SocketMessage(object):
    """This class is main used to send message."""

    def __init__(self,
                 server_host,
                 msg=None,
                 socket_port=FLAGS.sockclient_port):
        self.port = socket_port
        self.protocol = socket.SOCK_STREAM
        self.family = socket.AF_INET
        self.data_size = 102400
        self.server_host = server_host
        self.send_data = _to_json_data(msg)

    def send(self, once=False):
        """Send the message until success."""
        LOG.info('Try to send the message = %s' % self.send_data)
        recive = None
        while recive is None and once == False:
            recive = self._send_and_rec_msg()
            time.sleep(1)

        LOG.info('Rec msg from vsm-api node, msg = %s' % recive)
        return recive

    def _send_and_rec_msg(self):
        """Try to connect and send the msg.

        If success, feed back the recived message.
        If failed, return None.

        If can not connect to server, we still try to
        connect and send the message.
        """

        try:
            sock = socket.socket(self.family, self.protocol)
        except socket.error:
            LOG.info("Failed to create socket!")
            return None

        try:
            sock.connect((self.server_host, self.port))
            sock.send(self.send_data + "\n")
            res = sock.recv(self.data_size)
            sock.close()
            return res
        except socket.error:
            LOG.info("Can not to connect to socket!")

            return None
