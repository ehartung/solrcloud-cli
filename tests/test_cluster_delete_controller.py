#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mock import MagicMock, call
from unittest import TestCase
from solrcloud_cli.controllers.cluster_delete_controller import ClusterDeleteController
from solrcloud_cli.services.senza_wrapper import SenzaWrapper

import json
import urllib.error
import urllib.request
import urllib.response

BASE_URL = 'http://example.org/solr'
API_URL = BASE_URL + '/admin/collections'
STACK_NAME = 'test'
OAUTH_TOKEN = 'test0token'
CONFIG = 'test.yaml'

HTTP_CODE_OK = 200
HTTP_CODE_UNKNOWN = 111
HTTP_CODE_BAD_REQUEST = 400
HTTP_CODE_TIMEOUT = 504
HTTP_CODE_ERROR = 500
HTTP_CODE_UNKNOWN_ERROR = 555

REPLICATION_FACTOR = 3

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
        }
    },
}


class TestClusterDeleteController(TestCase):

    __controller = None
    __urlopen_mock = None

    def setUp(self):
        senza_wrapper = SenzaWrapper(CONFIG)
        self.__controller = ClusterDeleteController(base_url=BASE_URL, stack_name=STACK_NAME, oauth_token=OAUTH_TOKEN,
                                                    senza_wrapper=senza_wrapper)

    def test_should_return_success_when_deleting_collection_in_cluster(self):
        urllib.request.urlopen = MagicMock(side_effect=self.__side_effect_all_ok)
        self.assertEqual(0, self.__controller.delete_collection_in_cluster('test'))

    def test_should_return_failure_because_of_unknown_status_code_from_solr_when_deleting_collection_in_cluster(self):
        urllib.request.urlopen = MagicMock(side_effect=self.__side_effect_unknown_http_code)
        with self.assertRaisesRegex(Exception, 'Received unexpected status code from Solr: \[{}\]'
                                               .format(str(HTTP_CODE_UNKNOWN))):
            self.__controller.delete_collection_in_cluster('test')

    def test_should_return_failure_because_of_unknown_error_from_solr_when_deleting_collection_in_cluster(self):
        urllib.request.urlopen = MagicMock(side_effect=self.__side_effect_unknown_http_error)
        with self.assertRaisesRegex(Exception, 'Failed sending request to Solr \[{}\]: HTTP Error {}: .*'
                                               .format(API_URL + '[^\]]+', str(HTTP_CODE_UNKNOWN_ERROR))):
            self.__controller.delete_collection_in_cluster('test')

    def test_should_return_success_after_timeout_when_deleting_collection_in_cluster(self):
        urllib.request.urlopen = MagicMock(side_effect=self.__side_effect_timeout)
        self.assertEqual(0, self.__controller.delete_collection_in_cluster('test'))

    def test_should_return_success_after_a_bad_request_error_when_deleting_collection_in_cluster(self):
        urllib.request.urlopen = MagicMock(side_effect=self.__side_effect_bad_request)
        self.assertEqual(0, self.__controller.delete_collection_in_cluster('test'))

    def test_should_delete_all_collections_in_cluster(self):
        urlopen_mock = MagicMock(side_effect=self.__side_effect_return_cluster_state)
        urllib.request.urlopen = urlopen_mock
        collections = CLUSTER_NORMAL['cluster']['collections'].keys()
        urls = list()
        for collection in collections:
            url = API_URL + '?action=DELETE'
            url += '&name=' + collection
            urls.append(url)
        result = self.__controller.delete_all_collections_in_cluster()
        self.assertEquals(0, result, "Deleting collections from cluster failed.")
        called_urls = list(map(lambda x: x[0][0].get_full_url(), urlopen_mock.call_args_list))
        for url in urls:
            self.assertIn(url, called_urls, 'URL was not called')

    def test_should_return_success_on_errors_when_deleting_all_collections_in_cluster(self):
        side_effects = [
            self.__side_effect_return_cluster_state(None),
            urllib.error.HTTPError(url=None, code=HTTP_CODE_UNKNOWN_ERROR, msg=None, hdrs=None, fp=None),
        ]
        urlopen_mock = MagicMock(side_effect=side_effects)
        urllib.request.urlopen = urlopen_mock
        collections = CLUSTER_NORMAL['cluster']['collections'].keys()
        urls = list()
        for collection in collections:
            url = API_URL + '?action=DELETE'
            url += '&name=' + collection
            urls.append(url)
        result = self.__controller.delete_all_collections_in_cluster()
        self.assertEquals(0, result, "Deleting collections from cluster failed.")
        called_urls = list(map(lambda x: x[0][0].get_full_url(), urlopen_mock.call_args_list))
        for url in urls:
            self.assertIn(url, called_urls, 'URL was not called')

    def test_should_forward_method_call_to_senza_when_deleting_a_cluster_version(self):
        senza_mock = SenzaWrapper(CONFIG)
        senza_delete_mock = senza_mock.delete_stack_version = MagicMock()

        controller = ClusterDeleteController(base_url=BASE_URL, stack_name=STACK_NAME, oauth_token=OAUTH_TOKEN,
                                             senza_wrapper=senza_mock)
        controller.delete_cluster_version('test-version')
        senza_delete_mock.assert_called_once_with(STACK_NAME, 'test-version')

    def test_should_forward_method_call_to_senza_when_switching_off_a_cluster_version(self):
        senza_mock = SenzaWrapper(CONFIG)
        senza_switch_mock = senza_mock.switch_traffic = MagicMock()

        controller = ClusterDeleteController(base_url=BASE_URL, stack_name=STACK_NAME, oauth_token=OAUTH_TOKEN,
                                             senza_wrapper=senza_mock)
        controller.switch_off_traffic('test-version')
        senza_switch_mock.assert_called_once_with(STACK_NAME, 'test-version', 0)

    def test_should_not_raise_exception_when_weight_was_already_zero_before_switching_off_a_cluster_version(self):
        senza_mock = SenzaWrapper(CONFIG)
        senza_switch_mock = senza_mock.switch_traffic = MagicMock(side_effect=Exception('Traffic weight did not change'
                                                                                        ', traffic for stack \[{}\] '
                                                                                        'version \[{}\] is still at '
                                                                                        '\[{}\]%'.format('test', 'test',
                                                                                                         '0')))

        controller = ClusterDeleteController(base_url=BASE_URL, stack_name=STACK_NAME, oauth_token=OAUTH_TOKEN,
                                             senza_wrapper=senza_mock)
        controller.switch_off_traffic('test-version')
        senza_switch_mock.assert_called_once_with(STACK_NAME, 'test-version', 0)

    def test_should_raise_exception_when_switching_off_a_cluster_version_failed(self):
        senza_mock = SenzaWrapper(CONFIG)
        senza_switch_mock = senza_mock.switch_traffic = MagicMock(side_effect=Exception('Some exception'))
        controller = ClusterDeleteController(base_url=BASE_URL, stack_name=STACK_NAME, oauth_token=OAUTH_TOKEN,
                                             senza_wrapper=senza_mock)
        with self.assertRaisesRegex(Exception, 'Some exception'):
            controller.switch_off_traffic('test-version')

        senza_switch_mock.assert_called_once_with(STACK_NAME, 'test-version', 0)

    def test_should_not_raise_exceptions_when_deleting_a_complete_cluster(self):
        versions = [{'version': 'test-version1'}, {'version': 'test-version2'}]
        senza_mock = SenzaWrapper(CONFIG)
        senza_versions_mock = senza_mock.get_all_stack_versions = MagicMock(return_value=versions)
        senza_switch_mock = senza_mock.switch_traffic = MagicMock(return_value=True)
        senza_delete_mock = senza_mock.delete_stack_version = MagicMock()
        controller = ClusterDeleteController(base_url=BASE_URL, stack_name=STACK_NAME, oauth_token=OAUTH_TOKEN,
                                             senza_wrapper=senza_mock)

        urlopen_mock = MagicMock(side_effect=self.__side_effect_return_cluster_state)
        urllib.request.urlopen = urlopen_mock
        controller.delete_cluster()

        senza_versions_mock.assert_called_once_with(STACK_NAME)

        switch_calls = senza_switch_mock.call_args_list
        self.assertEquals(2, len(switch_calls), 'Unexpected number of switch calls')
        self.assertIn(call(STACK_NAME, 'test-version1', 0), switch_calls)
        self.assertIn(call(STACK_NAME, 'test-version2', 0), switch_calls)

        delete_calls = senza_delete_mock.call_args_list
        self.assertEquals(2, len(delete_calls), 'Unexpected number of delete calls')
        self.assertIn(call(STACK_NAME, 'test-version1'), delete_calls)
        self.assertIn(call(STACK_NAME, 'test-version2'), delete_calls)

    def test_should_raise_exception_when_deleting_a_complete_cluster_without_version(self):
        versions = []
        senza_mock = SenzaWrapper(CONFIG)
        senza_versions_mock = senza_mock.get_all_stack_versions = MagicMock(return_value=versions)
        controller = ClusterDeleteController(base_url=BASE_URL, stack_name=STACK_NAME, oauth_token=OAUTH_TOKEN,
                                             senza_wrapper=senza_mock)

        with self.assertRaisesRegex(Exception, 'No active stack version found'):
            controller.delete_cluster()
        senza_versions_mock.assert_called_once_with(STACK_NAME)

    def __side_effect_return_cluster_state(self, value):
        response_mock = MagicMock()
        # return OK for all HTTP requests
        response_mock.getcode.return_value = HTTP_CODE_OK
        response_mock.readall.return_value = bytes(json.dumps(CLUSTER_NORMAL), 'utf-8')
        return response_mock

    def __side_effect_all_ok(self, value):
        self.assertIsNotNone(value)
        response_mock = MagicMock()
        response_mock.getcode.return_value = HTTP_CODE_OK
        return response_mock

    def __side_effect_unknown_http_code(self, value):
        self.assertIsNotNone(value)
        response_mock = MagicMock()
        response_mock.getcode.return_value = HTTP_CODE_UNKNOWN
        return response_mock

    def __side_effect_unknown_http_error(self, value):
        raise urllib.error.HTTPError(url=None, code=HTTP_CODE_UNKNOWN_ERROR, msg=None, hdrs=None, fp=None)

    def __side_effect_error(self, value):
        raise urllib.error.HTTPError(url=None, code=HTTP_CODE_ERROR, msg=None, hdrs=None, fp=None)

    def __side_effect_timeout(self, value):
        self.assertIsNotNone(value)
        raise urllib.error.HTTPError(url=None, code=HTTP_CODE_TIMEOUT, msg=None, hdrs=None, fp=None)

    def __side_effect_bad_request(self, value):
        raise urllib.error.HTTPError(url=None, code=HTTP_CODE_BAD_REQUEST, msg=None, hdrs=None, fp=None)
