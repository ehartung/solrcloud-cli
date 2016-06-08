#!/usr/bin/env python
# -*- coding: utf-8 -*-
from mock import MagicMock
from unittest import TestCase
from solrcloud_cli.controllers.cluster_bootstrap_controller import ClusterBootstrapController
from solrcloud_cli.services.senza_wrapper import SenzaWrapper
from testfixtures import log_capture

import json
import os
import urllib.error
import urllib.request
import urllib.response

BASE_URL = 'http://example.org/solr'
API_URL = BASE_URL + '/admin/collections'
STACK_NAME = 'test'
IMAGE_VERSION = '0.0.0'
OAUTH_TOKEN = 'test0token'
INITIAL_BOOTSTRAP_VERSION = 'blue'
CONFIG = 'test.yaml'

HTTP_CODE_OK = 200
HTTP_CODE_UNKNOWN = 111
HTTP_CODE_BAD_REQUEST = 400
HTTP_CODE_ERROR = 500
HTTP_CODE_UNAVAILABLE = 503
HTTP_CODE_TIMEOUT = 504
HTTP_CODE_UNKNOWN_ERROR = 555

REPLICATION_FACTOR = 3
SHARDING_LEVEL = 1

CLUSTER_NORMAL = {
    "cluster": {
        "collections": {
            "test-collection01": {
                "replicationFactor": str(REPLICATION_FACTOR),
                "shards": {
                    "shard1": {
                        "state": "active",
                        "replicas": {
                            "test-node01_shard1_replica1": {
                                "node_name": "0.0.0.0:8983_solr",
                                "state": "active",
                                "leader": "true"
                            },
                            "test-node01_shard1_replica2": {
                                "node_name": "0.0.0.1:8983_solr",
                                "state": "active"
                            },
                            "test-node01_shard1_replica3": {
                                "node_name": "0.0.0.2:8983_solr",
                                "state": "active"
                            }
                        }
                    }
                }
            }
        },
        "live_nodes": [
            '0.0.0.0:8983_solr',
            '0.0.0.1:8983_solr',
            '0.0.0.2:8983_solr'
        ]
    }
}


class TestClusterBootstrapController(TestCase):

    __controller = None
    __urlopen_mock = None

    def setUp(self):
        senza_wrapper = SenzaWrapper(CONFIG)
        self.__controller = ClusterBootstrapController(base_url=BASE_URL, stack_name=STACK_NAME,
                                                       sharding_level=SHARDING_LEVEL,
                                                       replication_factor=REPLICATION_FACTOR,
                                                       image_version=IMAGE_VERSION, oauth_token=OAUTH_TOKEN,
                                                       senza_wrapper=senza_wrapper)
        self.__controller.set_retry_count(1)
        self.__controller.set_retry_wait(0)

    def test_should_return_success_when_adding_collection_to_cluster(self):
        urllib.request.urlopen = MagicMock(side_effect=self.__side_effect_all_ok)
        self.assertEqual(0, self.__controller.add_collection_to_cluster('test'))

    def test_should_return_failure_because_of_unknown_status_code_from_solr_when_adding_collection_to_cluster(self):
        urllib.request.urlopen = MagicMock(side_effect=self.__side_effect_unknown_http_code)
        with self.assertRaisesRegex(Exception, 'Received unexpected status code from Solr: \[{}\]'
                                               .format(str(HTTP_CODE_UNKNOWN))):
            self.__controller.add_collection_to_cluster('test')

    def test_should_return_failure_because_of_unknown_error_from_solr_when_adding_collection_to_cluster(self):
        urllib.request.urlopen = MagicMock(side_effect=self.__side_effect_unknown_http_error)
        with self.assertRaisesRegex(Exception, 'Failed sending request to Solr \[{}\]: HTTP Error {}: .*'
                                               .format(API_URL + '[^\]]+', str(HTTP_CODE_UNKNOWN_ERROR))):
            self.__controller.add_collection_to_cluster('test')

    def test_should_return_success_after_timeout_when_deleting_collection_in_cluster(self):
        urllib.request.urlopen = MagicMock(side_effect=self.__side_effect_timeout)
        self.assertEqual(0, self.__controller.add_collection_to_cluster('test'))

    def test_should_return_success_after_a_bad_request_error_followed_by_a_ok_on_the_retry_when_adding_collection(self):
        response_mock = MagicMock()
        response_mock.getcode.return_value = HTTP_CODE_OK
        side_effects = [
            urllib.error.HTTPError(url=None, code=HTTP_CODE_BAD_REQUEST, msg=None, hdrs=None, fp=None),
            response_mock
        ]
        urllib.request.urlopen = MagicMock(side_effect=side_effects)
        self.assertEqual(0, self.__controller.add_collection_to_cluster('test'))

    def test_should_return_success_after_an_error_followed_by_a_ok_on_the_retry_when_adding_collection(self):
        response_mock = MagicMock()
        response_mock.getcode.return_value = HTTP_CODE_OK
        side_effects = [
            urllib.error.HTTPError(url=None, code=HTTP_CODE_ERROR, msg=None, hdrs=None, fp=None),
            response_mock
        ]
        urllib.request.urlopen = MagicMock(side_effect=side_effects)
        self.assertEqual(0, self.__controller.add_collection_to_cluster('test'))

    def test_should_return_success_after_a_unavailable_error_followed_by_a_ok_on_the_retry_when_adding_collection(self):
        response_mock = MagicMock()
        response_mock.getcode.return_value = HTTP_CODE_OK
        side_effects = [
            urllib.error.HTTPError(url=None, code=HTTP_CODE_UNAVAILABLE, msg=None, hdrs=None, fp=None),
            response_mock
        ]
        urllib.request.urlopen = MagicMock(side_effect=side_effects)
        self.assertEqual(0, self.__controller.add_collection_to_cluster('test'))

    def test_should_add_all_collections_to_cluster(self):
        urlopen_mock = MagicMock(side_effect=self.__side_effect_return_cluster_state)
        urllib.request.urlopen = urlopen_mock
        os.listdir = MagicMock(side_effect=self.__side_effect_config_list)
        collections = self.__side_effect_config_list(None)
        urls = list()
        for collection in collections:
            url = API_URL + '?action=CREATE'
            url += '&name=' + collection
            url += '&numShards=' + str(SHARDING_LEVEL)
            url += '&replicationFactor=' + str(REPLICATION_FACTOR)
            url += '&maxShardsPerNode=1'
            url += '&collection.configName=' + collection.replace('_', '')
            urls.append(url)
        result = self.__controller.add_all_collections_to_cluster()
        self.assertEquals(0, result, "Adding collections to cluster failed.")
        called_urls = list(map(lambda x: x[0][0].get_full_url(), urlopen_mock.call_args_list))
        for url in urls:
            self.assertIn(url, called_urls, 'URL was not called')

    def test_should_not_raise_any_exception_when_creating_a_new_cluster(self):
        senza_mock = SenzaWrapper(CONFIG)
        senza_create_mock = senza_mock.create_stack = MagicMock()

        controller = ClusterBootstrapController(base_url=BASE_URL, stack_name=STACK_NAME,
                                                sharding_level=SHARDING_LEVEL,
                                                replication_factor=REPLICATION_FACTOR,
                                                image_version=IMAGE_VERSION, oauth_token=OAUTH_TOKEN,
                                                senza_wrapper=senza_mock)
        controller.create_cluster()

        senza_create_mock.assert_called_once_with(STACK_NAME, INITIAL_BOOTSTRAP_VERSION, IMAGE_VERSION)

    def test_should_not_raise_any_exception_when_switching_to_another_cluster_version(self):
        senza_mock = SenzaWrapper(CONFIG)
        senza_switch_mock = senza_mock.switch_traffic = MagicMock()

        controller = ClusterBootstrapController(base_url=BASE_URL, stack_name=STACK_NAME,
                                                sharding_level=SHARDING_LEVEL,
                                                replication_factor=REPLICATION_FACTOR,
                                                image_version=IMAGE_VERSION, oauth_token=OAUTH_TOKEN,
                                                senza_wrapper=senza_mock)
        controller.switch_on_traffic()

        senza_switch_mock.assert_called_once_with(STACK_NAME, INITIAL_BOOTSTRAP_VERSION, 100)

    @log_capture()
    def test_should_not_write_warning_when_waiting_for_cluster_to_be_ready_and_all_nodes_are_available(self, log):
        senza_mock = SenzaWrapper(CONFIG)
        controller = ClusterBootstrapController(base_url=BASE_URL, stack_name=STACK_NAME,
                                                sharding_level=SHARDING_LEVEL,
                                                replication_factor=REPLICATION_FACTOR,
                                                image_version=IMAGE_VERSION, oauth_token=OAUTH_TOKEN,
                                                senza_wrapper=senza_mock)
        controller.set_retry_count(1)
        controller.set_retry_wait(0)

        urlopen_mock = MagicMock(side_effect=self.__side_effect_return_cluster_state)
        urllib.request.urlopen = urlopen_mock

        controller.wait_for_cluster_to_be_ready()

        log.check()

    @log_capture()
    def test_should_write_warning_when_waiting_for_cluster_to_be_ready_and_not_enough_nodes_are_available(self, log):
        senza_mock = SenzaWrapper(CONFIG)
        sharding_level = SHARDING_LEVEL + 1
        controller = ClusterBootstrapController(base_url=BASE_URL, stack_name=STACK_NAME,
                                                sharding_level=sharding_level,
                                                replication_factor=REPLICATION_FACTOR,
                                                image_version=IMAGE_VERSION, oauth_token=OAUTH_TOKEN,
                                                senza_wrapper=senza_mock)
        controller.set_retry_count(1)
        controller.set_retry_wait(0)

        urlopen_mock = MagicMock(side_effect=self.__side_effect_return_cluster_state)
        urllib.request.urlopen = urlopen_mock

        controller.wait_for_cluster_to_be_ready()

        log.check(
            ('root', 'WARNING', 'Cluster is not ready, yet, retrying ...'),
            ('root', 'WARNING', 'Cluster is not ready, yet, retrying ...'),
            ('root', 'WARNING', 'Cluster did not become ready in time.')
        )

    @log_capture()
    def test_should_write_warning_when_waiting_for_cluster_to_be_ready_and_timeout_on_cluster_state(self, log):
        senza_mock = SenzaWrapper(CONFIG)
        controller = ClusterBootstrapController(base_url=BASE_URL, stack_name=STACK_NAME,
                                                sharding_level=SHARDING_LEVEL,
                                                replication_factor=REPLICATION_FACTOR,
                                                image_version=IMAGE_VERSION, oauth_token=OAUTH_TOKEN,
                                                senza_wrapper=senza_mock)
        controller.set_retry_count(1)
        controller.set_retry_wait(0)

        urlopen_mock = MagicMock(side_effect=self.__side_effect_timeout)
        urllib.request.urlopen = urlopen_mock

        controller.wait_for_cluster_to_be_ready()

        log.check(
            ('root', 'WARNING',
             'Clould not get cluster state: Failed sending request to Solr '
             '[' + BASE_URL + '/admin/collections?action=CLUSTERSTATUS&wt=json]: '
             'HTTP Error 504: None'),
            ('root', 'WARNING', 'Cluster is not ready, yet, retrying ...'),
            ('root', 'WARNING',
             'Clould not get cluster state: Failed sending request to Solr '
             '[' + BASE_URL + '/admin/collections?action=CLUSTERSTATUS&wt=json]: '
             'HTTP Error 504: None'),
            ('root', 'WARNING', 'Cluster is not ready, yet, retrying ...'),
            ('root', 'WARNING', 'Cluster did not become ready in time.')
        )

    def test_should_not_raise_exceptions_when_executing_all_bootstrap_steps(self):
        senza_mock = SenzaWrapper(CONFIG)
        senza_create_mock = senza_mock.create_stack = MagicMock()
        senza_switch_mock = senza_mock.switch_traffic = MagicMock(return_value=True)
        os.listdir = MagicMock(side_effect=self.__side_effect_config_list)
        controller = ClusterBootstrapController(base_url=BASE_URL, stack_name=STACK_NAME,
                                                sharding_level=SHARDING_LEVEL,
                                                replication_factor=REPLICATION_FACTOR,
                                                image_version=IMAGE_VERSION, oauth_token=OAUTH_TOKEN,
                                                senza_wrapper=senza_mock)
        controller.set_retry_count(1)
        controller.set_retry_wait(0)

        urlopen_mock = MagicMock(side_effect=self.__side_effect_return_cluster_state)
        urllib.request.urlopen = urlopen_mock

        controller.bootstrap_cluster()

        senza_create_mock.assert_called_once_with(STACK_NAME, INITIAL_BOOTSTRAP_VERSION, IMAGE_VERSION)
        senza_switch_mock.assert_called_once_with(STACK_NAME, INITIAL_BOOTSTRAP_VERSION, 100)

    def __side_effect_all_ok(self, value):
        self.assertIsNotNone(value)
        response_mock = MagicMock()
        response_mock.getcode.return_value = HTTP_CODE_OK
        return response_mock

    def __side_effect_timeout(self, value):
        self.assertIsNotNone(value)
        raise urllib.error.HTTPError(url=None, code=HTTP_CODE_TIMEOUT, msg=None, hdrs=None, fp=None)

    def __side_effect_unknown_http_code(self, value):
        self.assertIsNotNone(value)
        response_mock = MagicMock()
        response_mock.getcode.return_value = HTTP_CODE_UNKNOWN
        return response_mock

    def __side_effect_unknown_http_error(self, value):
        raise urllib.error.HTTPError(url=None, code=HTTP_CODE_UNKNOWN_ERROR, msg=None, hdrs=None, fp=None)

    def __side_effect_error(self, value):
        raise urllib.error.HTTPError(url=None, code=HTTP_CODE_ERROR, msg=None, hdrs=None, fp=None)

    def __side_effect_return_cluster_state(self, value):
        response_mock = MagicMock()
        # return OK for all HTTP requests
        response_mock.getcode.return_value = HTTP_CODE_OK
        response_mock.read.return_value = bytes(json.dumps(CLUSTER_NORMAL), 'utf-8')
        return response_mock

    def __side_effect_config_list(self, value):
        return ['test1', 'test2']
