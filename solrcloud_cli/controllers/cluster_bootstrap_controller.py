#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import time

from solrcloud_cli.controllers.cluster_controller import ClusterController
from solrcloud_cli.services.senza_deployment_service import DeploymentService
from solrcloud_cli.services.solr_collections_service import SolrCollectionsService

CONFIG_DIR = os.path.join(os.getcwd(), 'configs')
INITIAL_STACK_VERSION = 'blue'
DEFAULT_RETRY_COUNT = 30
DEFAULT_RETRY_WAIT = 10


class ClusterBootstrapController(ClusterController):
    __sharding_level = 0
    __replication_factor = 0
    __image_version = ''
    __retry_count = DEFAULT_RETRY_COUNT
    __retry_wait = DEFAULT_RETRY_WAIT

    def __init__(self, stack_name: str, sharding_level: int, replication_factor: int, image_version: str,
                 solr_collections_service: SolrCollectionsService, deployment_service: DeploymentService):
        self._stack_name = stack_name
        self.__replication_factor = replication_factor
        self.__sharding_level = sharding_level
        self.__image_version = image_version
        self._solr_collections_service = solr_collections_service
        self._deployment_service = deployment_service

    def bootstrap_cluster(self):
        self.create_cluster()
        self.switch_on_traffic()
        self.wait_for_cluster_to_be_ready()
        self.add_all_collections_to_cluster()

    def set_retry_count(self, retry_count: int):
        self.__retry_count = retry_count
        self._solr_collections_service.set_retry_count(retry_count)

    def set_retry_wait(self, retry_wait: int):
        self.__retry_wait = retry_wait
        self._solr_collections_service.set_retry_wait(retry_wait)

    def create_cluster(self):
        self._deployment_service.create_node_set(self._stack_name, INITIAL_STACK_VERSION, self.__image_version)

    def switch_on_traffic(self):
        self._deployment_service.switch_traffic(self._stack_name, INITIAL_STACK_VERSION, 100)

    def wait_for_cluster_to_be_ready(self):
        retry = True
        retry_count = 0
        expected_number_of_nodes = int(self.__sharding_level) * int(self.__replication_factor)
        while retry and retry_count <= self.__retry_count:
            try:
                cluster_state = self._solr_collections_service.get_cluster_state()
                nodes_count = len(cluster_state['cluster']['live_nodes'])
                if nodes_count >= expected_number_of_nodes:
                    retry = False
            except Exception as e:
                logging.warning('Clould not get cluster state: {}'.format(e))
            finally:
                if retry:
                    logging.warning('Cluster is not ready, yet, retrying ...')
                    time.sleep(self.__retry_wait)
                    retry_count += 1
        if retry:
            logging.warning('Cluster did not become ready in time.')

    def add_all_collections_to_cluster(self):
        result = 0
        for config in os.listdir(CONFIG_DIR):
            result += self.add_collection_to_cluster(config)
        return result

    def add_collection_to_cluster(self, collection_name):
        return self._solr_collections_service.add_collection_to_cluster(collection_name)
