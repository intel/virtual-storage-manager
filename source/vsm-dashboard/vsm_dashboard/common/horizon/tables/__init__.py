
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

from .mixin import BatchActionMixin
from horizon.tables import BatchAction

import logging
from horizon import exceptions
from horizon import messages
from horizon.utils import functions
from django.utils.translation import ugettext_lazy as _
from django import shortcuts
LOG = logging.getLogger(__name__)

class BatchAction(BatchAction):
    def handle(self, table, request, obj_ids):
        action_success = []
        action_failure = []
        action_not_allowed = []
        for datum_id in obj_ids:
            datum = table.get_object_by_id(datum_id)
            datum_display = table.get_object_display(datum) or _("N/A")
            if not table._filter_action(self, request, datum):
                action_not_allowed.append(datum_display)
                LOG.info('Permission denied to %s: "%s"' %
                         (self._get_action_name(past=True).lower(),
                          datum_display))
                continue
            try:
                self.action(request, datum_id)
                #Call update to invoke changes if needed
                self.update(request, datum)
                action_success.append(datum_display)
                self.success_ids.append(datum_id)
                LOG.info('%s: "%s"' %
                         (self._get_action_name(past=True), datum_display))
            except Exception as ex:
                # Handle the exception but silence it since we'll display
                # an aggregate error message later. Otherwise we'd get
                # multiple error messages displayed to the user.
                if getattr(ex, "_safe_message", None):
                    ignore = False
                else:
                    ignore = True
                    action_failure.append(datum_display)
                exceptions.handle(request, ignore=ignore)

        # Begin with success message class, downgrade to info if problems.
        success_message_level = messages.success
        if action_not_allowed:
            msg = 'You are not allowed to %(action)s: %(objs)s'
            params = {"action":
                      self._get_action_name(action_not_allowed).lower(),
                      "objs": functions.lazy_join(", ", action_not_allowed)}
            messages.error(request, msg % params)
            success_message_level = messages.info
        if action_failure:
            msg = _('Unable to %(action)s: %(objs)s')
            params = {"action": self._get_action_name(action_failure).lower(),
                      "objs": functions.lazy_join(", ", action_failure)}
            messages.error(request, msg % params)
            success_message_level = messages.info
        if action_success:
            msg = _('%(action)s: %(objs)s')
            params = {"action":
                      self._get_action_name(action_success, past=True),
                      "objs": functions.lazy_join(", ", action_success)}
            success_message_level(request, msg % params)

        return shortcuts.redirect(self.get_success_url(request))
