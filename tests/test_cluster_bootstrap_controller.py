#!/usr/bin/env python
# -*- coding: utf-8 -*-
from mock import MagicMock
from unittest import TestCase
from solrcloud_cli.controllers.cluster_bootstrap_controller import ClusterBootstrapController
from solrcloud_cli.services.senza_deployment_service import DeploymentService
from solrcloud_cli.services.solr_collections_service import SolrCollectionsService
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
    __solr_sollections_service = None

    def setUp(self):
        deployment_service = MagicMock(spec=DeploymentService)
        self.__solr_collections_service = SolrCollectionsService(base_url=BASE_URL,
                                                          oauth_token=OAUTH_TOKEN,
                                                          replication_factor=REPLICATION_FACTOR,
                                                          sharding_level=SHARDING_LEVEL)

        self.__controller = ClusterBootstrapController(stack_name=STACK_NAME,
                                                       sharding_level=SHARDING_LEVEL,
                                                       replication_factor=REPLICATION_FACTOR,
                                                       image_version=IMAGE_VERSION,
                                                       solr_collections_service=self.__solr_collections_service,
                                                       deployment_service=deployment_service)
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
        solr_collections_service_mock = MagicMock()
        solr_collections_service_mock.add_collection_to_cluster.return_value = 0
        solr_collections_service_mock.get_cluster_state.return_value = CLUSTER_NORMAL
        self.__controller.set_solr_collections_service(solr_collections_service_mock)

        os.listdir = MagicMock(side_effect=self.__side_effect_config_list)

        self.__controller.add_all_collections_to_cluster()

        self.assertEquals(solr_collections_service_mock.add_collection_to_cluster.call_count, 2)


    def test_should_not_raise_any_exception_when_creating_a_new_cluster(self):
        deployment_service_mock = MagicMock(spec=DeploymentService)
        senza_create_mock = deployment_service_mock.create_node_set = MagicMock()

        controller = ClusterBootstrapController(stack_name=STACK_NAME,
                                                sharding_level=SHARDING_LEVEL,
                                                replication_factor=REPLICATION_FACTOR,
                                                image_version=IMAGE_VERSION,
                                                solr_collections_service=self.__solr_collections_service,
                                                deployment_service=deployment_service_mock)
        controller.create_cluster()

        senza_create_mock.assert_called_once_with(STACK_NAME, INITIAL_BOOTSTRAP_VERSION, IMAGE_VERSION)

    def test_should_not_raise_any_exception_when_switching_to_another_cluster_version(self):
        deployment_service_mock = MagicMock(spec=DeploymentService)
        senza_switch_mock = deployment_service_mock.switch_traffic = MagicMock()

        controller = ClusterBootstrapController(stack_name=STACK_NAME,
                                                sharding_level=SHARDING_LEVEL,
                                                replication_factor=REPLICATION_FACTOR,
                                                image_version=IMAGE_VERSION,
                                                solr_collections_service=self.__solr_collections_service,
                                                deployment_service=deployment_service_mock)
        controller.switch_on_traffic()

        senza_switch_mock.assert_called_once_with(STACK_NAME, INITIAL_BOOTSTRAP_VERSION, 100)

    @log_capture()
    def test_should_not_write_warning_when_waiting_for_cluster_to_be_ready_and_all_nodes_are_available(self, log):
        deployment_service_mock = MagicMock(spec=DeploymentService)
        controller = ClusterBootstrapController(stack_name=STACK_NAME,
                                                sharding_level=SHARDING_LEVEL,
                                                replication_factor=REPLICATION_FACTOR,
                                                image_version=IMAGE_VERSION,
                                                solr_collections_service=self.__solr_collections_service,
                                                deployment_service=deployment_service_mock)
        controller.set_retry_count(1)
        controller.set_retry_wait(0)

        urlopen_mock = MagicMock(side_effect=self.__side_effect_return_cluster_state)
        urllib.request.urlopen = urlopen_mock

        controller.wait_for_cluster_to_be_ready()

        log.check()

    @log_capture()
    def test_should_write_warning_when_waiting_for_cluster_to_be_ready_and_not_enough_nodes_are_available(self, log):
        deployment_service_mock = MagicMock(spec=DeploymentService)
        sharding_level = SHARDING_LEVEL + 1
        controller = ClusterBootstrapController(stack_name=STACK_NAME,
                                                sharding_level=sharding_level,
                                                replication_factor=REPLICATION_FACTOR,
                                                image_version=IMAGE_VERSION,
                                                solr_collections_service=self.__solr_collections_service,
                                                deployment_service=deployment_service_mock)
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
        deployment_service_mock = MagicMock(spec=DeploymentService)
        controller = ClusterBootstrapController(stack_name=STACK_NAME,
                                                sharding_level=SHARDING_LEVEL,
                                                replication_factor=REPLICATION_FACTOR,
                                                image_version=IMAGE_VERSION,
                                                solr_collections_service=self.__solr_collections_service,
                                                deployment_service=deployment_service_mock)
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
        deployment_service_mock = MagicMock(spec=DeploymentService)
        senza_create_mock = deployment_service_mock.create_node_set = MagicMock()
        senza_switch_mock = deployment_service_mock.switch_traffic = MagicMock(return_value=True)
        os.listdir = MagicMock(side_effect=self.__side_effect_config_list)
        controller = ClusterBootstrapController(stack_name=STACK_NAME,
                                                sharding_level=SHARDING_LEVEL,
                                                replication_factor=REPLICATION_FACTOR,
                                                image_version=IMAGE_VERSION,
                                                solr_collections_service=self.__solr_collections_service,
                                                deployment_service=deployment_service_mock)
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
