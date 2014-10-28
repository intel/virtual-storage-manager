
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

from horizon import tables
from .base import BaseUsage

LOG = logging.getLogger(__name__)

class UsageView(tables.DataTableView):
    usage_class = None
    show_terminated = True

    def __init__(self, *args, **kwargs):
        super(UsageView, self).__init__(*args, **kwargs)
        if not issubclass(self.usage_class, BaseUsage):
            raise AttributeError("You must specify a usage_class attribute "
                                 "which is a subclass of BaseUsage.")

    def get_template_names(self):
        if self.request.GET.get('format', 'html') == 'csv':
            return ".".join((self.template_name.rsplit('.', 1)[0], 'csv'))
        return self.template_name

    def get_content_type(self):
        if self.request.GET.get('format', 'html') == 'csv':
            return "text/csv"
        return "text/html"

    def get_data(self):
        tenant_id = self.kwargs.get('tenant_id', self.request.user.tenant_id)
        self.usage = self.usage_class(self.request, tenant_id)
        self.usage.summarize(*self.usage.get_date_range())
        self.usage.get_quotas()
        self.kwargs['usage'] = self.usage
        return self.usage.usage_list

    def get_context_data(self, **kwargs):
        context = super(UsageView, self).get_context_data(**kwargs)
        context['table'].kwargs['usage'] = self.usage
        context['form'] = self.usage.form
        context['usage'] = self.usage
        return context

    def render_to_response(self, context, **response_kwargs):
        resp = self.response_class(request=self.request,
                                   template=self.get_template_names(),
                                   context=context,
                                   content_type=self.get_content_type(),
                                   **response_kwargs)
        if self.request.GET.get('format', 'html') == 'csv':
            resp['Content-Disposition'] = 'attachment; filename=usage.csv'
            resp['Content-Type'] = 'text/csv'
        return resp
