#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import time
import urllib.error
import urllib.request

COLLECTIONS_API_PATH = '/admin/collections'
DEFAULT_RETRY_COUNT = 30
DEFAULT_RETRY_WAIT = 10
DEFAULT_LEADER_CHECK_RETRY_COUNT = 30
DEFAULT_LEADER_CHECK_RETRY_WAIT = 1
DEFAULT_ADD_NODE_RETRY_COUNT = 30
DEFAULT_ADD_NODE_RETRY_WAIT = 10
DEFAULT_ADD_NODE_TIMEOUT = 900
DEFAULT_CREATE_CLUSTER_RETRY_WAIT = 10
DEFAULT_CREATE_CLUSTER_TIMEOUT = 120


class SolrCollectionsService:

    __retry_count = DEFAULT_RETRY_COUNT
    __retry_wait = DEFAULT_RETRY_WAIT
    __leader_check_retry_count = DEFAULT_LEADER_CHECK_RETRY_COUNT
    __leader_check_retry_wait = DEFAULT_LEADER_CHECK_RETRY_WAIT
    __add_node_retry_count = DEFAULT_ADD_NODE_RETRY_COUNT
    __add_node_retry_wait = DEFAULT_ADD_NODE_RETRY_WAIT
    __add_node_timeout = DEFAULT_ADD_NODE_TIMEOUT
    __create_cluster_retry_wait = DEFAULT_CREATE_CLUSTER_RETRY_WAIT
    __create_cluster_timeout = DEFAULT_CREATE_CLUSTER_TIMEOUT

    def __init__(self, base_url: str, sharding_level: int, replication_factor: int, oauth_token: str):
        self._api_url = base_url.strip('/') + COLLECTIONS_API_PATH
        self._oauth_token = oauth_token
        self.__replication_factor = replication_factor
        self.__sharding_level = sharding_level

    def set_retry_count(self, retry_count: int):
        self.__retry_count = retry_count

    def set_retry_wait(self, retry_wait: int):
        self.__retry_wait = retry_wait

    def set_add_node_retry_count(self, retry_count: int):
        self.__add_node_retry_count = retry_count

    def set_add_node_retry_wait(self, retry_wait: int):
        self.__add_node_retry_wait = retry_wait

    def set_add_node_timeout(self, timeout: int):
        self.__add_node_timeout = timeout

    def set_create_cluster_retry_wait(self, retry_wait: int):
        self.__create_cluster_retry_wait = retry_wait

    def set_create_cluster_timeout(self, timeout: int):
        self.__create_cluster_timeout = timeout

    def get_cluster_state(self):
        url = self._api_url + '?action=CLUSTERSTATUS&wt=json'
        try:
            code, content = self.__send_request_to_solr(url)
            if code != 200:
                raise Exception('Received unexpected status code from Solr: [{}]'.format(code))
            return json.loads(content)
        except Exception as e:
            raise Exception('Failed sending request to Solr [{}]: {}'.format(url, e))

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
                code, content = self.__send_request_to_solr(url)
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

    def delete_collection_in_cluster(self, collection_name: str):
        url = self._api_url + '?action=DELETE&name=' + collection_name
        try:
            code, content = self.__send_request_to_solr(url)
            if code != 200:
                raise Exception('Received unexpected status code from Solr: [{}]'.format(code))
        except urllib.error.HTTPError as e:
            if e.code == 504:
                logging.warning('HTTP Timeout while deleting collection [{}], but it should have been deleted anyways.'
                                .format(collection_name))
            elif e.code == 400:
                logging.warning('HTTP error 400 (Bad Request) while deleting collection [{}]: [{}]'
                                .format(collection_name, e.reason))
            else:
                raise Exception('Failed sending request to Solr [{}]: {}'.format(url, e))
        except Exception as e:
            raise Exception('Failed sending request to Solr [{}]: {}'.format(url, e))
        return 0

    def add_replica_to_cluster(self, collection_name: str, shard_name: str, node_name: str):
        url = self._api_url + '?action=ADDREPLICA'
        url += '&collection=' + collection_name
        url += '&shard=' + shard_name
        url += '&node=' + node_name
        retry = True
        retry_count = 0
        while retry and retry_count <= self.__add_node_retry_count:
            try:
                code, content = self.__send_request_to_solr(url)
                if code != 200:
                    raise Exception('Received unexpected status code from Solr: [{}]'.format(code))
                retry = False
            except urllib.error.HTTPError as e:
                if e.code == 504:
                    logging.warning('HTTP Timeout while adding node [{}], but replica should have been added anyways.'
                                    .format(node_name))
                    retry = False
                elif e.code == 400:
                    logging.warning('HTTP error 400 (Bad Request) while adding node [{}] to shard [{}] of collection '
                                    '[{}]'.format(node_name, shard_name, collection_name))
                else:
                    raise Exception('Failed sending request to Solr [{}]: {}'.format(url, e))
            except Exception as e:
                raise Exception('Failed sending request to Solr [{}]: {}'.format(url, e))
            finally:
                if retry:
                    time.sleep(self.__add_node_retry_wait)
                    retry_count += 1
        return 0

    def delete_replica_from_cluster(self, collection: str, shard: str, replica: str):
        url = self._api_url + '?action=DELETEREPLICA'
        url += '&collection=' + collection
        url += '&shard=' + shard
        url += '&replica=' + replica
        try:
            code, content = self.__send_request_to_solr(url)
            if code != 200:
                raise Exception('Received unexpected status code from Solr: [{}]'.format(code))
        except urllib.error.HTTPError as e:
            if e.code == 504:
                logging.warning('HTTP Timeout while deleting replica [{}], but replica should have been deleted '
                                'anyways.'.format(replica))
            elif e.code == 500:
                logging.warning('Error while deleting replica [{}]: {}.'.format(replica, e))
            else:
                raise Exception('Failed sending request to Solr [{}]: {}'.format(url, e))
        except Exception as e:
            raise Exception('Failed sending request to Solr [{}]: {}'.format(url, e))

    def __send_request_to_solr(self, url: str):
        headers = dict()
        if self._oauth_token:
            headers['Authorization'] = 'Bearer ' + self._oauth_token
        request = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(request)
        code = response.getcode()
        content = response.read().decode('utf-8')
        response.close()
        return code, content
