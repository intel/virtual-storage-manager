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

import webob
from webob import exc
from vsm.api.openstack import wsgi
from vsm.api import xmlutil
from vsm import flags
from vsm.openstack.common import log as logging
from vsm.api.views import vsm_settings as set_views
from vsm.openstack.common.db import exception as db_exc
from vsm import db
from vsm import utils
from vsm import exception
from vsm import scheduler

LOG = logging.getLogger(__name__)

FLAGS = flags.FLAGS

def make_setting(elem, detailed=False):
    elem.set('id')
    elem.set('name')
    elem.set('value')
    elem.set('default_value')

    if detailed:
        pass

setting_nsmap = {None: xmlutil.XMLNS_V11, 'atom': xmlutil.XMLNS_ATOM}

class SettingTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('setting', selector='setting')
        make_setting(root, detailed=True)
        return xmlutil.MasterTemplate(root, 1, nsmap=setting_nsmap)

class SettingsTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('settings')
        elem = xmlutil.SubTemplateElement(root, 'setting', selector='settings')
        make_setting(elem, detailed=True)
        return xmlutil.MasterTemplate(root, 1, nsmap=setting_nsmap)

class Controller(wsgi.Controller):
    """The Monitor API controller for the OpenStack API."""
    _view_builder_class = set_views.ViewBuilder

    def __init__(self, ext_mgr):
        super(Controller, self).__init__()
        self.scheduler_api = scheduler.API()

    @wsgi.serializers(xml=SettingsTemplate)
    @wsgi.response(202)
    def get_by_name(self, req):
        """ Get one vsm setting by name
        """
        context = req.environ['vsm.context']
        search_opts = {}
        search_opts.update(req.GET)

        LOG.debug('search options %s' % search_opts)
        vsm_name = search_opts.pop('name', None)
        if not vsm_name:
            raise exc.HTTPBadRequest(explanation=_('Invalid request: vsm name is required.'))

        try:
            utils.check_string_length(vsm_name, 'name', min_length=1, max_length=255)
            setting = db.vsm_settings_get_by_name(context, vsm_name)
        except db_exc.DBError as e:
            raise exc.HTTPServerError(explanation=e.message)
        except exception.InvalidInput as e:
            raise exc.HTTPBadRequest(explanation=e.message)

        if not setting:
            raise exc.HTTPNotFound(explanation=_('The vsm setting(%s) does not exists.' % vsm_name))

        return self._view_builder.basic(req, setting)

    @wsgi.serializers(xml=SettingsTemplate)
    def index(self, req):
        """Get a vsm setting list."""
        context = req.environ['vsm.context']

        settings = db.vsm_settings_get_all(context)
        LOG.info('vsm/api/v1/vsm_settings.py settings:%s' % settings)

        return self._view_builder.index(req, settings)

    @wsgi.serializers(xml=SettingsTemplate)
    def detail(self, req):
        """Get a detailed vsm setting list."""
        context = req.environ['vsm.context']

        settings = db.vsm_settings_get_all(context)
        LOG.info('vsm/api/v1/vsm_settings.py settings:%s' % settings)

        return self._view_builder.detail(req, settings)

    @wsgi.serializers(xml=SettingsTemplate)
    @wsgi.response(202)
    def create(self, req, body=None):
        """Create or update the vsm setting.
        {
         'setting': {
                        'name' : 'xxx',
                        'value': 'yyy'
                    }

        }
        """
        if not self.is_valid_body(body, 'setting'):
            raise exc.HTTPBadRequest(explanation=_('Invalid request body.'))

        context = req.environ['vsm.context']
        setting_dict = body['setting']

        self._validate_body(setting_dict)
        instance = self._create_setting(context, setting_dict)
        return self._view_builder.basic(req, instance)

    def _create_setting(self, context, setting_dict):

        try:
            if setting_dict.get('name') in ['cpu_diamond_collect_interval','ceph_diamond_collect_interval']:
                 self.scheduler_api.reconfig_diamond(context, setting_dict)
            return db.vsm_settings_update_or_create(context, setting_dict)

        except db_exc.DBError as e:
            raise exc.HTTPServerError(explanation=e.message)

    def _validate_body(self, setting_dict):
        if not isinstance(setting_dict, dict):
            raise exc.HTTPBadRequest(explanation=_('Invalid request body.'))

        if not 'name' in setting_dict.keys():
            LOG.debug('dict keys %s %s' % (setting_dict, setting_dict.keys()))
            msg = _("vsm setting name is not defined in vsm setting request.")
            raise exc.HTTPBadRequest(explanation=msg)

        name = setting_dict.get('name')
        value = setting_dict.get('value')
        default_value = setting_dict.get('default_value')

        try:
            if name:
                utils.check_string_length(name, 'name', min_length=1, max_length=255)
            else:
                msg = _('key name cannot be null or empty.')
                raise exc.HTTPBadRequest(explanation=msg)
            if value:
                utils.check_string_length(value, 'value', max_length=255)
            if default_value:
                utils.check_string_length(default_value, 'default value', max_length=255)
        except exception.InvalidInput as e:
            raise exc.HTTPBadRequest(explanation=e.message)

def create_resource(ext_mgr):
    return wsgi.Resource(Controller(ext_mgr))
