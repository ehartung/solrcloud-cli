#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from solrcloud_cli.controllers.cluster_controller import ClusterController
from solrcloud_cli.services.senza_deployment_service import DeploymentService
from solrcloud_cli.services.solr_collections_service import SolrCollectionsService


class ClusterDeleteController(ClusterController):

    def __init__(self, stack_name: str, solr_collections_service: SolrCollectionsService,
                 deployment_service: DeploymentService):
        self._stack_name = stack_name
        self._solr_collections_service = solr_collections_service
        self._deployment_service = deployment_service

    def delete_cluster(self):
        stack_versions = self._deployment_service.get_all_stack_versions(self._stack_name)
        if not stack_versions:
            raise Exception('No active stack version found')
        self.delete_all_collections_in_cluster()
        for version in stack_versions:
            self.switch_off_traffic(version['version'])
            self.delete_cluster_version(version['version'])

    def delete_cluster_version(self, stack_version: str):
        self._deployment_service.delete_stack_version(self._stack_name, stack_version)

    def switch_off_traffic(self, stack_version: str):
        try:
            self._deployment_service.switch_traffic(self._stack_name, stack_version, 0)
        except Exception as e:
            if str(e).startswith("Traffic weight did not change"):
                logging.info('Traffic was not switched, it was already off for stack version [{}]'
                             .format(stack_version))
            else:
                raise e

    def delete_all_collections_in_cluster(self):
        cluster_state = self._solr_collections_service.get_cluster_state()
        for collection in cluster_state['cluster']['collections'].keys():
            try:
                self.delete_collection_in_cluster(collection)
            except Exception as e:
                logging.warning('Could not delete collection [{}] in cluster: [{}]'.format(collection, e))
        return 0

    def delete_collection_in_cluster(self, collection_name: str):
        return self._solr_collections_service.delete_collection_in_cluster(collection_name)
