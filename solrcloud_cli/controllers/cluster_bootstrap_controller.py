#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import time
import urllib.error
import urllib.request

from solrcloud_cli.controllers.cluster_controller import ClusterController
from solrcloud_cli.services.senza_wrapper import SenzaWrapper

CONFIG_DIR = os.path.join(os.getcwd(), 'configs')
INITIAL_STACK_VERSION = 'blue'
DEFAULT_RETRY_COUNT = 30
DEFAULT_RETRY_WAIT = 10
COLLECTIONS_API_PATH = '/admin/collections'


class ClusterBootstrapController(ClusterController):
    __sharding_level = 0
    __replication_factor = 0
    __image_version = ''
    __retry_count = DEFAULT_RETRY_COUNT
    __retry_wait = DEFAULT_RETRY_WAIT

    def __init__(self, base_url: str, stack_name: str, sharding_level: int, replication_factor: int, image_version: str,
                 oauth_token: str, senza_wrapper: SenzaWrapper):
        self._api_url = base_url.strip('/') + COLLECTIONS_API_PATH
        self._oauth_token = oauth_token
        self._stack_name = stack_name
        self.__replication_factor = replication_factor
        self.__sharding_level = sharding_level
        self.__image_version = image_version
        self._senza = senza_wrapper

    def bootstrap_cluster(self):
        self.create_cluster()
        self.switch_on_traffic()
        self.wait_for_cluster_to_be_ready()
        self.add_all_collections_to_cluster()

    def set_retry_count(self, retry_count: int):
        self.__retry_count = retry_count

    def set_retry_wait(self, retry_wait: int):
        self.__retry_wait = retry_wait

    def create_cluster(self):
        self._senza.create_stack(self._stack_name, INITIAL_STACK_VERSION, self.__image_version)

    def switch_on_traffic(self):
        self._senza.switch_traffic(self._stack_name, INITIAL_STACK_VERSION, 100)

    def wait_for_cluster_to_be_ready(self):
        retry = True
        retry_count = 0
        expected_number_of_nodes = int(self.__sharding_level) * int(self.__replication_factor)
        while retry and retry_count <= self.__retry_count:
            try:
                cluster_state = self.get_cluster_state()
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
        url = self._api_url + '?action=CREATE'
        url += '&name=' + collection_name
        url += '&numShards=' + str(self.__sharding_level)
        url += '&replicationFactor=' + str(self.__replication_factor)
        url += '&maxShardsPerNode=1'
        url += '&collection.configName=' + collection_name.replace('_', '')
        retry = True
        retry_count = 0
        while retry and retry_count <= self.__retry_count:
            try:
                headers = dict()
                headers['Authorization'] = 'Bearer ' + self._oauth_token
                request = urllib.request.Request(url, headers=headers)
                response = urllib.request.urlopen(request)
                code = response.getcode()
                response.close()
                if code != 200:
                    raise Exception('Received unexpected status code from Solr: [{}]'.format(code))
                retry = False
            except urllib.error.HTTPError as e:
                if e.code == 500:
                    logging.warning('Adding collection [{}] failed, retrying ...'
                                    .format(collection_name))
                elif e.code == 503:
                    logging.warning('Service for adding collection [{}] not available, retrying ...'
                                    .format(collection_name))
                elif e.code == 504:
                    logging.warning('HTTP timeout while adding collection [{}], but it should have been added anyways.'
                                    .format(collection_name))
                    retry = False
                elif e.code == 400:
                    logging.warning('HTTP error 400 (Bad Request) while adding collection [{}]'.format(collection_name))
                else:
                    raise Exception('Failed sending request to Solr [{}]: {}'.format(url, e))
            except Exception as e:
                raise Exception('Failed sending request to Solr [{}]: {}'.format(url, e))
            finally:
                if retry:
                    time.sleep(self.__retry_wait)
                    retry_count += 1
        return 0
