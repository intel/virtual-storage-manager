#  Copyright 2014 Intel Corporation, All Rights Reserved.
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
Clusters interface.
"""

import urllib
from vsmclient import base


class Cluster(base.Resource):
    """A cluster is created to manage ceph."""
    def __repr__(self):
        try:
            return "<Cluster: %s>" % self.id
        except AttributeError:
            return "<Cluster: summary>"

    def delete(self):
        """Delete this vsm."""
        self.manager.delete(self)

    def update(self, **kwargs):
        """Update the display_name or display_description for this vsm."""
        self.manager.update(self, **kwargs)

class ClusterManager(base.ManagerWithFind):
    """
    Manage :class:`Cluster` resources.
    """
    resource_class = Cluster

    def create(self, name="default", file_system="xfs", journal_size=None, 
                size=None, management_network=None,
                ceph_public_network=None, cluster_network=None,
                primary_public_netmask=None, secondary_public_netmask=None,
                cluster_netmask=None, servers=[]):

        """
        Create a cluster.
        """

        body = {'cluster': {'name': name,
                            "file_system": file_system,
                            "journal_size": journal_size,
                            "size": size, 
                            "management_network": management_network,
                            "ceph_public_network": ceph_public_network,
                            "cluster_network": cluster_network,
                            "primary_public_netmask": primary_public_netmask,
                            "secondary_public_netmask": secondary_public_netmask,
                            "cluster_netmask": cluster_netmask,
                            "servers": servers,
                           }}
        return self._create('/clusters', body, 'cluster')

    def get(self, cluster_id):
        """
        Get a cluster.

        :param cluster_id: The ID of the cluster to delete.
        :rtype: :class:`Cluster`
        """
        return self._get("/clusters/%s" % cluster_id, "cluster")

    def list(self, detailed=False, search_opts=None):
        """
        Get a list of all clusters.

        :rtype: list of :class:`Cluster`
        """
        #print ' comes to list'
        if search_opts is None:
            search_opts = {}

        qparams = {}

        for opt, val in search_opts.iteritems():
            if val:
                qparams[opt] = val

        query_string = "?%s" % urllib.urlencode(qparams) if qparams else ""

        detail = ""
        if detailed:
            detail = "/detail"

        ret = self._list("/clusters%s%s" % (detail, query_string),
                          "clusters")
        return ret

    def delete(self, cluster):
        """
        Delete a cluster.

        :param cluster: The :class:`Cluster` to delete.
        """
        self._delete("/clusters/%s" % base.getid(cluster))

    def update(self, cluster, **kwargs):
        """
        Update the display_name or display_description for a cluster.

        :param cluster: The :class:`Cluster` to delete.
        """
        if not kwargs:
            return

        body = {"cluster": kwargs}

        self._update("/clusters/%s" % base.getid(cluster), body)

    # def _action(self, action, vsm, info=None, **kwargs):
    #     """
    #     Perform a vsm "action."
    #     """
    #     body = {action: info}
    #     self.run_hooks('modify_body_for_action', body, **kwargs)
    #     url = '/clusters/%s/action' % base.getid(vsm)
    #     return self.api.client.post(url, body=body)

    def summary(self):
        """
        summary
        """
        url = "/clusters/summary"
        return self._get(url, 'cluster-summary')

    def get_service_list(self):
        """
        get_service_list
        """
        url = "/clusters/get_service_list"
        return self._list(url, 'services')

    def refresh(self):
        url = "/clusters/refresh"
        return self.api.client.post(url)

    def import_ceph_conf(self,cluster_name,ceph_conf_path=None):
        body = {'cluster': {
                            "cluster_name": cluster_name,
                            "ceph_conf_path":ceph_conf_path,
                           }}
        url = "/clusters/import_ceph_conf"
        return self.api.client.post(url,body=body)

    def check_pre_existing_cluster(self,body):
        url = "/clusters/check_pre_existing_cluster"
        return self.api.client.post(url,body=body)

    def import_cluster(self,body):
        url = "/clusters/import_cluster"
        return self.api.client.post(url,body=body)

    def detect_cephconf(self,body):
        url = "/clusters/detect_cephconf"
        return self.api.client.post(url,body=body)

    def detect_crushmap(self,body):
        url = "/clusters/detect_crushmap"
        return self.api.client.post(url,body=body)

    def get_crushmap_tree_data(self,body):
        url = "/clusters/get_crushmap_tree_data"
        return self.api.client.post(url,body=body)

    def integrate(self,servers=[]):
        body = {'cluster': {
                            "servers": servers,
                           }}
        url = "/clusters/integrate"
        return self.api.client.post(url)

    def stop_cluster(self,cluster_id):
        body = {'cluster': {
                            "id": cluster_id,
                           }}
        url = "/clusters/stop_cluster"
        return self.api.client.post(url,body=body)

    def start_cluster(self,cluster_id):
        body = {'cluster': {
                            "id": cluster_id,
                           }}
        url = "/clusters/start_cluster"
        return self.api.client.post(url,body=body)

    def get_ceph_health_list(self):
        """
        ceph_status
        """
        url = "/clusters/get_ceph_health_list"
        resp, ceph_status = self.api.client.get(url)
        return ceph_status