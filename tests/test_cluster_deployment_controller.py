#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mock import MagicMock
from unittest import TestCase
from solrcloud_cli.controllers.cluster_deployment_controller import ClusterDeploymentController
from solrcloud_cli.services.senza_wrapper import SenzaWrapper

import json
import re
import urllib.error
import urllib.request
import urllib.response

BASE_URL = 'http://example.org/solr'
API_URL = BASE_URL + '/admin/collections'
STACK_NAME = 'test'
IMAGE_VERSION = '0.0.0'
OAUTH_TOKEN = 'test0token'
CONFIG = 'test.yaml'

HTTP_CODE_OK = 200
HTTP_CODE_UNKNOWN = 111
HTTP_CODE_BAD_REQUEST = 400
HTTP_CODE_TIMEOUT = 504
HTTP_CODE_ERROR = 500
HTTP_CODE_UNKNOWN_ERROR = 555

REPLICATION_FACTOR = 3

NEW_NODES = ['1.1.1.0', '1.1.1.1', '1.1.1.2']
OLD_NODES = ['0.0.0.0', '0.0.0.1', '0.0.0.2']
NOT_ENOUGH_NODES = ['2.2.2.0', '2.2.2.1']

CLUSTER_OLD_NODES = {
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
    },
}

CLUSTER_NEW_NODES = {
    "cluster": {
        "collections": {
            "test-collection01": {
                "replicationFactor": str(REPLICATION_FACTOR),
                "shards": {
                    "shard1": {
                        "state": "active",
                        "replicas": {
                            "test-node01_shard1_replica1": {
                                "node_name": "1.1.1.0:8983_solr",
                                "state": "active",
                                "leader": "true"
                            },
                            "test-node01_shard1_replica2": {
                                "node_name": "1.1.1.1:8983_solr",
                                "state": "active"
                            },
                            "test-node01_shard1_replica3": {
                                "node_name": "1.1.1.2:8983_solr",
                                "state": "active"
                            }
                        }
                    }
                }
            }
        },
        "live_nodes": [
            '1.1.1.0:8983_solr',
            '1.1.1.1:8983_solr',
            '1.1.1.2:8983_solr'
        ]
    },
}

CLUSTER_ALL_REGISTERED = {
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
            '0.0.0.2:8983_solr',
            '1.1.1.0:8983_solr',
            '1.1.1.1:8983_solr',
            '1.1.1.2:8983_solr'
        ]
    },
}

CLUSTER_ALL_NODES = {
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
                            },
                            "test-node01_shard1_replica4": {
                                "node_name": "1.1.1.0:8983_solr",
                                "state": "active"
                            },
                            "test-node01_shard1_replica5": {
                                "node_name": "1.1.1.1:8983_solr",
                                "state": "active"
                            },
                            "test-node01_shard1_replica6": {
                                "node_name": "1.1.1.2:8983_solr",
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
            '0.0.0.2:8983_solr',
            '1.1.1.0:8983_solr',
            '1.1.1.1:8983_solr',
            '1.1.1.2:8983_solr'
        ]
    },
}

CLUSTER_ALL_NODES_ONE_NOT_ACTIVE = {
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
                            },
                            "test-node01_shard1_replica4": {
                                "node_name": "1.1.1.0:8983_solr",
                                "state": "active"
                            },
                            "test-node01_shard1_replica5": {
                                "node_name": "1.1.1.1:8983_solr",
                                "state": "active"
                            },
                            "test-node01_shard1_replica6": {
                                "node_name": "1.1.1.2:8983_solr",
                                "state": "recovering"
                            }
                        }
                    }
                }
            }
        },
        "live_nodes": [
            '0.0.0.0:8983_solr',
            '0.0.0.1:8983_solr',
            '0.0.0.2:8983_solr',
            '1.1.1.0:8983_solr',
            '1.1.1.1:8983_solr',
            '1.1.1.2:8983_solr'
        ]
    },
}

CLUSTER_NO_LEADER = {
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
                                "state": "active"
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

CLUSTER_ONLY_ONE_ACTIVE_REPLICA = {
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
                                "state": "down"
                            },
                            "test-node01_shard1_replica3": {
                                "node_name": "0.0.0.2:8983_solr",
                                "state": "down"
                            }
                        }
                    }
                }
            }
        }
    },
}

CLUSTER_INACTIVE_SHARD_NO_REPLICAS = {
    "cluster": {
        "collections": {
            "test-collection01": {
                "replicationFactor": str(REPLICATION_FACTOR),
                "shards": {
                    "shard1": {
                        "state": "down",
                        "replicas": {}
                    }
                }
            }
        }
    },
}


class TestClusterDeploymentController(TestCase):

    __controller = None
    __urlopen_mock = None

    def setUp(self):
        urllib.request.urlopen = MagicMock(side_effect=self.__side_effect_return_cluster_state_old_nodes)
        senza_wrapper = SenzaWrapper(CONFIG)
        self.__controller = ClusterDeploymentController(base_url=BASE_URL, stack_name=STACK_NAME,
                                                        image_version=IMAGE_VERSION, oauth_token=OAUTH_TOKEN,
                                                        senza_wrapper=senza_wrapper)
        self.__controller.set_leader_check_retry_count(1)
        self.__controller.set_leader_check_retry_wait(0)
        self.__controller.set_add_node_retry_count(1)
        self.__controller.set_add_node_retry_wait(0)
        self.__controller.set_add_node_timeout(1)
        self.__controller.set_create_cluster_retry_wait(0)
        self.__controller.set_create_cluster_timeout(1)

    def test_should_return_success_after_adding_new_replica_to_cluster(self):
        urllib.request.urlopen = MagicMock(side_effect=self.__side_effect_all_ok)
        self.assertEqual(0, self.__controller.add_replica_to_cluster('test', 'test', 'test'))

    def test_should_return_failure_because_of_unknown_status_code_from_solr_when_adding_new_replica_to_cluster(self):
        urllib.request.urlopen = MagicMock(side_effect=self.__side_effect_unknown_http_code)
        with self.assertRaisesRegex(Exception, 'Received unexpected status code from Solr: \[{}\]'
                                               .format(str(HTTP_CODE_UNKNOWN))):
            self.__controller.add_replica_to_cluster('test', 'test', 'test')

    def test_should_return_success_after_timeout_when_adding_new_replica_to_cluster(self):
        urllib.request.urlopen = MagicMock(side_effect=self.__side_effect_timeout)
        self.assertEqual(0, self.__controller.add_replica_to_cluster('test', 'test', 'test'))

    def test_should_return_success_after_a_bad_request_error_followed_by_a_ok_on_the_retry_when_adding_replica(self):
        response_mock = MagicMock()
        response_mock.getcode.return_value = HTTP_CODE_OK
        side_effects = [
            urllib.error.HTTPError(url=None, code=HTTP_CODE_BAD_REQUEST, msg=None, hdrs=None, fp=None),
            response_mock
        ]
        urllib.request.urlopen = MagicMock(side_effect=side_effects)
        self.assertEqual(0, self.__controller.add_replica_to_cluster('test', 'test', 'test'))

    def test_should_return_failure_because_of_unknown_http_error_when_adding_new_replica_to_cluster(self):
        urllib.request.urlopen = MagicMock(side_effect=self.__side_effect_unknown_http_error)
        with self.assertRaisesRegex(Exception, 'Failed sending request to Solr \[{}\]: HTTP Error {}: .*'
                                               .format(API_URL + '[^\]]+', str(HTTP_CODE_UNKNOWN_ERROR))):
            self.__controller.add_replica_to_cluster('test', 'test', 'test')

    def test_should_return_success_after_adding_multiple_nodes_to_cluster(self):
        cluster_states = [
            self.__side_effect_return_cluster_state_all_registered_nodes(None),
            self.__side_effect_all_ok(''),
            self.__side_effect_all_ok(''),
            self.__side_effect_all_ok(''),
            self.__side_effect_return_cluster_state_all_nodes(None)
        ]
        urlopen_mock = MagicMock(side_effect=cluster_states)
        urllib.request.urlopen = urlopen_mock
        collection = list(CLUSTER_OLD_NODES['cluster']['collections'].keys())[0]
        shard = list(CLUSTER_OLD_NODES['cluster']['collections'][collection]['shards'].keys())[0]
        urls = list()
        for node_ip in NEW_NODES:
            node = node_ip + ':8983_solr'
            url = API_URL + '?action=ADDREPLICA'
            url += '&collection=' + collection
            url += '&shard=' + shard
            url += '&node=' + node
            urls.append(url)

        senza_mock = MagicMock()
        senza_mock.get_stack_instances.return_value = NEW_NODES
        self.__controller.set_senza_wrapper(senza_mock)

        self.__controller.add_new_nodes_to_cluster()

        called_urls = list(map(lambda x: x[0][0].get_full_url(), urlopen_mock.call_args_list))
        for url in urls:
            self.assertIn(url, called_urls, 'URL was not called')

    def test_should_return_error_because_of_not_enough_nodes_for_cluster_layout(self):
        urllib.request.urlopen = MagicMock(side_effect=self.__side_effect_return_cluster_state_old_nodes)
        senza_mock = MagicMock()
        senza_mock.get_stack_instances.return_value = NOT_ENOUGH_NODES
        self.__controller.set_senza_wrapper(senza_mock)
        with self.assertRaises(Exception, msg='Not enough instances for current cluster layout: [2]<[3]'):
            self.__controller.add_new_nodes_to_cluster()

    def test_should_wait_until_all_nodes_are_active(self):
        http_calls = [
            self.__side_effect_return_cluster_state_all_registered_nodes(None),
            self.__side_effect_all_ok(''),
            self.__side_effect_all_ok(''),
            self.__side_effect_all_ok(''),
            self.__side_effect_return_cluster_state_all_nodes_one_not_active(None),
            self.__side_effect_return_cluster_state_all_nodes(None)
        ]
        urlopen_mock = MagicMock(side_effect=http_calls)
        urllib.request.urlopen = urlopen_mock
        collection = list(CLUSTER_OLD_NODES['cluster']['collections'].keys())[0]
        shard = list(CLUSTER_OLD_NODES['cluster']['collections'][collection]['shards'].keys())[0]
        urls = list()
        for node_ip in NEW_NODES:
            node = node_ip + ':8983_solr'
            url = API_URL + '?action=ADDREPLICA'
            url += '&collection=' + collection
            url += '&shard=' + shard
            url += '&node=' + node
            urls.append(url)

        senza_mock = MagicMock()
        senza_mock.get_stack_instances.return_value = NEW_NODES
        self.__controller.set_senza_wrapper(senza_mock)

        self.__controller.add_new_nodes_to_cluster()

        called_urls = list(map(lambda x: x[0][0].get_full_url(), urlopen_mock.call_args_list))
        for url in urls:
            self.assertIn(url, called_urls, 'URL was not called')

    def test_should_raise_exception_on_timeout_when_adding_nodes(self):
        http_calls = [
            self.__side_effect_return_cluster_state_all_registered_nodes(None),
            self.__side_effect_all_ok(''),
            self.__side_effect_all_ok(''),
            self.__side_effect_all_ok(''),
        ]
        urlopen_mock = MagicMock(side_effect=http_calls)
        urllib.request.urlopen = urlopen_mock
        collection = list(CLUSTER_OLD_NODES['cluster']['collections'].keys())[0]
        shard = list(CLUSTER_OLD_NODES['cluster']['collections'][collection]['shards'].keys())[0]
        urls = list()
        for node_ip in NEW_NODES:
            node = node_ip + ':8983_solr'
            url = API_URL + '?action=ADDREPLICA'
            url += '&collection=' + collection
            url += '&shard=' + shard
            url += '&node=' + node
            urls.append(url)

        senza_mock = MagicMock()
        senza_mock.get_stack_instances.return_value = NEW_NODES
        self.__controller.set_senza_wrapper(senza_mock)
        self.__controller.set_add_node_timeout(0)

        with self.assertRaisesRegex(Exception, 'Timeout while adding new nodes to cluster'):
            self.__controller.add_new_nodes_to_cluster()

        called_urls = list(map(lambda x: x[0][0].get_full_url(), urlopen_mock.call_args_list))
        for url in urls:
            self.assertIn(url, called_urls, 'URL was not called')

    def test_should_not_raise_exception_when_deleting_replica_from_cluster(self):
        urllib.request.urlopen = MagicMock(side_effect=self.__side_effect_all_ok)
        self.__controller.delete_replica_from_cluster('test', 'test', 'test')

    def test_should_return_failure_because_of_unknown_status_code_from_solr_when_deleting_replica_from_cluster(self):
        urllib.request.urlopen = MagicMock(side_effect=self.__side_effect_unknown_http_code)
        with self.assertRaisesRegex(Exception, 'Received unexpected status code from Solr: \[{}\]'
                                               .format(str(HTTP_CODE_UNKNOWN))):
            self.__controller.delete_replica_from_cluster('test', 'test', 'test')

    def test_should_not_raise_exception_after_timeout_when_deleting_replica_from_cluster(self):
        urllib.request.urlopen = MagicMock(side_effect=self.__side_effect_timeout)
        self.__controller.delete_replica_from_cluster('test', 'test', 'test')

    def test_should_not_raise_exception_after_error_when_deleting_replica_from_cluster(self):
        urllib.request.urlopen = MagicMock(side_effect=self.__side_effect_error)
        self.__controller.delete_replica_from_cluster('test', 'test', 'test')

    def test_should_return_failure_because_of_unknown_http_error_when_deleting_replica_from_cluster(self):
        urllib.request.urlopen = MagicMock(side_effect=self.__side_effect_unknown_http_error)
        with self.assertRaisesRegex(Exception, 'Failed sending request to Solr \[{}\]: HTTP Error {}: .*'
                                               .format(API_URL + '[^\]]+', str(HTTP_CODE_UNKNOWN_ERROR))):
            self.__controller.delete_replica_from_cluster('test', 'test', 'test')

    def test_should_return_success_after_deleting_multiple_nodes_from_cluster(self):
        urlopen_mock = MagicMock(side_effect=self.__side_effect_return_cluster_state_old_nodes)
        urllib.request.urlopen = urlopen_mock
        collection = list(CLUSTER_OLD_NODES['cluster']['collections'].keys())[0]
        shard = list(CLUSTER_OLD_NODES['cluster']['collections'][collection]['shards'].keys())[0]
        replicas = list(CLUSTER_OLD_NODES['cluster']['collections'][collection]['shards'][shard]['replicas'].keys())
        urls = list()
        for replica in replicas:
            url = API_URL + '?action=DELETEREPLICA'
            url += '&collection=' + collection
            url += '&shard=' + shard
            url += '&replica=' + replica
            urls.append(url)
        senza_mock = MagicMock()
        senza_mock.get_stack_instances.return_value = OLD_NODES
        self.__controller.set_senza_wrapper(senza_mock)

        self.__controller.delete_old_nodes_from_cluster()
        called_urls = list(map(lambda x: x[0][0].get_full_url(), urlopen_mock.call_args_list))
        for url in urls:
            self.assertIn(url, called_urls, 'URL was not called')

    def test_should_return_failure_after_deleting_multiple_nodes_from_shard_without_leader(self):
        urlopen_mock = MagicMock(side_effect=self.__side_effect_return_cluster_state_no_leader)
        urllib.request.urlopen = urlopen_mock
        senza_mock = MagicMock()
        senza_mock.get_stack_instances.return_value = OLD_NODES
        self.__controller.set_senza_wrapper(senza_mock)
        with self.assertRaisesRegex(Exception, 'Shard \[shard[0-9]\] of collection \[[a-z0-9\-]+\] has no active '
                                               'leader'):
            self.__controller.delete_old_nodes_from_cluster()

    def test_should_return_failure_after_deleting_multiple_nodes_with_only_one_active_replica(self):
        urlopen_mock = MagicMock(side_effect=self.__side_effect_return_cluster_state_only_one_active_replica)
        urllib.request.urlopen = urlopen_mock
        senza_mock = MagicMock()
        senza_mock.get_stack_instances.return_value = OLD_NODES
        self.__controller.set_senza_wrapper(senza_mock)
        with self.assertRaisesRegex(Exception, 'Shard \[shard[0-9]\] of collection \[[a-z0-9\-]+\] has not enough '
                                               'active nodes: \[[1]\]'):
            self.__controller.delete_old_nodes_from_cluster()

    def test_should_return_current_cluster_state(self):
        urllib.request.urlopen = MagicMock(side_effect=self.__side_effect_return_cluster_state_old_nodes)
        cluster_state = self.__controller.get_cluster_state()
        self.assertEqual(CLUSTER_OLD_NODES, cluster_state, 'Cluster state does not match test cluster')

    def test_should_return_failure_because_of_unknown_status_code_from_solr_when_requesting_cluster_state(self):
        urllib.request.urlopen = MagicMock(side_effect=self.__side_effect_unknown_http_code)
        with self.assertRaisesRegex(Exception, 'Received unexpected status code from Solr: \[{}\]'
                                               .format(str(HTTP_CODE_UNKNOWN))):
            self.__controller.get_cluster_state()

    def test_should_return_failure_because_of_unknown_http_error_when_requesting_cluster_state(self):
        urllib.request.urlopen = MagicMock(side_effect=self.__side_effect_unknown_http_error)
        with self.assertRaisesRegex(Exception, 'Failed sending request to Solr \[{}\]: HTTP Error {}: .*'
                                               .format(API_URL + '[^\]]+', str(HTTP_CODE_UNKNOWN_ERROR))):
            self.__controller.get_cluster_state()

    def test_should_return_failure_because_of_inactive_shard_in_cluster(self):
        collection = list(CLUSTER_INACTIVE_SHARD_NO_REPLICAS['cluster']['collections'].keys())[0]
        shard = list(CLUSTER_INACTIVE_SHARD_NO_REPLICAS['cluster']['collections'][collection]['shards'].keys())[0]
        self.assertFalse(ClusterDeploymentController.has_active_leader(CLUSTER_INACTIVE_SHARD_NO_REPLICAS, collection,
                                                                       shard),
                         'Cluster should have no active shards')

    def test_should_return_zero_if_shard_has_no_replicas(self):
        collection = list(CLUSTER_INACTIVE_SHARD_NO_REPLICAS['cluster']['collections'].keys())[0]
        shard = list(CLUSTER_INACTIVE_SHARD_NO_REPLICAS['cluster']['collections'][collection]['shards'].keys())[0]
        self.assertEquals(0, ClusterDeploymentController.get_number_of_active_nodes(CLUSTER_INACTIVE_SHARD_NO_REPLICAS,
                                                                                    collection, shard),
                          'Shard should have no replicas')

    def test_should_return_green_when_only_blue_stack_is_running_and_passive_stack_version_is_requested(self):

        active_version = 'blue'
        senza_mock = SenzaWrapper(CONFIG)
        senza_passive_versions_mock = senza_mock.get_passive_stack_version = MagicMock(return_value=None)
        senza_active_versions_mock = senza_mock.get_active_stack_version = MagicMock(return_value=active_version)

        controller = ClusterDeploymentController(base_url=BASE_URL, stack_name=STACK_NAME,
                                                 image_version=IMAGE_VERSION, oauth_token=OAUTH_TOKEN,
                                                 senza_wrapper=senza_mock)

        self.assertEquals('green', controller.get_passive_stack_version(), 'Wrong stack version')

        senza_passive_versions_mock.assert_called_once_with(STACK_NAME)
        senza_active_versions_mock.assert_called_once_with(STACK_NAME)

    def test_should_not_raise_any_exception_when_creating_a_new_cluster(self):
        instances = [
            NEW_NODES
        ]
        senza_mock = SenzaWrapper(CONFIG)
        senza_create_mock = senza_mock.create_stack = MagicMock()
        senza_passive_versions_mock = senza_mock.get_passive_stack_version = MagicMock(return_value='test-version')
        senza_instances_mock = senza_mock.get_stack_instances = MagicMock(side_effect=instances)

        http_calls = self.__side_effect_return_cluster_state_all_registered_nodes

        urlopen_mock = MagicMock(side_effect=http_calls)
        urllib.request.urlopen = urlopen_mock

        controller = ClusterDeploymentController(base_url=BASE_URL, stack_name=STACK_NAME,
                                                 image_version=IMAGE_VERSION, oauth_token=OAUTH_TOKEN,
                                                 senza_wrapper=senza_mock)
        controller.create_cluster()

        senza_passive_versions_mock.assert_called_with(STACK_NAME)
        self.assertEquals(2, len(senza_passive_versions_mock.call_args_list))
        senza_create_mock.assert_called_once_with(STACK_NAME, 'test-version', IMAGE_VERSION)
        senza_instances_mock.assert_called_once_with(STACK_NAME, 'test-version')

    def test_should_wait_until_all_nodes_are_registered_when_creating_a_new_cluster(self):
        instances = [
            NEW_NODES
        ]
        senza_mock = SenzaWrapper(CONFIG)
        senza_create_mock = senza_mock.create_stack = MagicMock()
        senza_passive_versions_mock = senza_mock.get_passive_stack_version = MagicMock(return_value='test-version')
        senza_instances_mock = senza_mock.get_stack_instances = MagicMock(side_effect=instances)

        http_calls = [
            self.__side_effect_return_cluster_state_old_nodes(None),
            self.__side_effect_return_cluster_state_old_nodes(None),
            self.__side_effect_return_cluster_state_all_registered_nodes(None)
        ]

        urlopen_mock = MagicMock(side_effect=http_calls)
        urllib.request.urlopen = urlopen_mock

        controller = ClusterDeploymentController(base_url=BASE_URL, stack_name=STACK_NAME,
                                                 image_version=IMAGE_VERSION, oauth_token=OAUTH_TOKEN,
                                                 senza_wrapper=senza_mock)
        controller.set_create_cluster_retry_wait(0)
        controller.set_create_cluster_timeout(1)
        controller.create_cluster()

        senza_passive_versions_mock.assert_called_with(STACK_NAME)
        self.assertEquals(2, len(senza_passive_versions_mock.call_args_list))
        senza_create_mock.assert_called_once_with(STACK_NAME, 'test-version', IMAGE_VERSION)
        senza_instances_mock.assert_called_once_with(STACK_NAME, 'test-version')

    def test_should_raise_exception_on_timeout_when_creating_a_new_cluster(self):
        instances = [
            NEW_NODES
        ]
        senza_mock = SenzaWrapper(CONFIG)
        senza_create_mock = senza_mock.create_stack = MagicMock()
        senza_passive_versions_mock = senza_mock.get_passive_stack_version = MagicMock(return_value='test-version')
        senza_instances_mock = senza_mock.get_stack_instances = MagicMock(side_effect=instances)

        http_calls = [
            self.__side_effect_return_cluster_state_old_nodes(None),
            self.__side_effect_return_cluster_state_old_nodes(None),
        ]

        urlopen_mock = MagicMock(side_effect=http_calls)
        urllib.request.urlopen = urlopen_mock

        controller = ClusterDeploymentController(base_url=BASE_URL, stack_name=STACK_NAME,
                                                 image_version=IMAGE_VERSION, oauth_token=OAUTH_TOKEN,
                                                 senza_wrapper=senza_mock)
        controller.set_create_cluster_retry_wait(0)
        controller.set_create_cluster_timeout(0)
        with self.assertRaisesRegex(Exception, 'Timeout while creating new cluster, not all new nodes have been '
                                               'registered in time'):
            controller.create_cluster()

        senza_passive_versions_mock.assert_called_with(STACK_NAME)
        self.assertEquals(2, len(senza_passive_versions_mock.call_args_list))
        senza_create_mock.assert_called_once_with(STACK_NAME, 'test-version', IMAGE_VERSION)
        senza_instances_mock.assert_called_once_with(STACK_NAME, 'test-version')

    def test_should_not_raise_any_exception_when_deleting_a_cluster(self):
        senza_mock = SenzaWrapper(CONFIG)
        senza_delete_mock = senza_mock.delete_stack_version = MagicMock()
        senza_passive_versions_mock = senza_mock.get_passive_stack_version = MagicMock(return_value='test-version')

        controller = ClusterDeploymentController(base_url=BASE_URL, stack_name=STACK_NAME,
                                                 image_version=IMAGE_VERSION, oauth_token=OAUTH_TOKEN,
                                                 senza_wrapper=senza_mock)
        controller.delete_cluster()

        senza_passive_versions_mock.assert_called_once_with(STACK_NAME)
        senza_delete_mock.assert_called_once_with(STACK_NAME, 'test-version')

    def test_should_not_raise_any_exception_when_switching_to_another_cluster_version(self):
        senza_mock = SenzaWrapper(CONFIG)
        senza_switch_mock = senza_mock.switch_traffic = MagicMock()
        senza_passive_versions_mock = senza_mock.get_passive_stack_version = MagicMock(return_value='test-version')

        controller = ClusterDeploymentController(base_url=BASE_URL, stack_name=STACK_NAME,
                                                 image_version=IMAGE_VERSION, oauth_token=OAUTH_TOKEN,
                                                 senza_wrapper=senza_mock)
        controller.switch_traffic()

        senza_passive_versions_mock.assert_called_once_with(STACK_NAME)
        senza_switch_mock.assert_called_once_with(STACK_NAME, 'test-version', 100)

    def test_should_not_raise_exceptions_when_executing_all_deployment_steps(self):
        test_version = 'test-version'
        instances = [
            OLD_NODES,
            NEW_NODES,
            OLD_NODES
        ]
        senza_mock = SenzaWrapper(CONFIG)
        senza_create_mock = senza_mock.create_stack = MagicMock()
        senza_passive_versions_mock = senza_mock.get_passive_stack_version = MagicMock(return_value=test_version)
        senza_switch_mock = senza_mock.switch_traffic = MagicMock(return_value=True)
        senza_delete_mock = senza_mock.delete_stack_version = MagicMock()
        senza_instances_mock = senza_mock.get_stack_instances = MagicMock(side_effect=instances)

        controller = ClusterDeploymentController(base_url=BASE_URL, stack_name=STACK_NAME,
                                                 image_version=IMAGE_VERSION, oauth_token=OAUTH_TOKEN,
                                                 senza_wrapper=senza_mock)

        controller.set_leader_check_retry_count(1)
        controller.set_leader_check_retry_wait(0)
        controller.set_add_node_retry_count(1)
        controller.set_add_node_retry_wait(0)
        controller.set_add_node_timeout(1)

        http_calls = [
            self.__side_effect_return_cluster_state_all_registered_nodes(None),  # create_cluster
            self.__side_effect_return_cluster_state_all_registered_nodes(None),  # add_new_nodes_to_cluster
            self.__side_effect_all_ok(''),  # add_new_nodes_to_cluster
            self.__side_effect_all_ok(''),  # add_new_nodes_to_cluster
            self.__side_effect_all_ok(''),  # add_new_nodes_to_cluster
            self.__side_effect_return_cluster_state_all_nodes(None),  # add_new_nodes_to_cluster
            self.__side_effect_return_cluster_state_all_nodes(None),  # delete_old_nodes_from_cluster
            self.__side_effect_return_cluster_state_all_nodes(None),  # delete_old_nodes_from_cluster
            self.__side_effect_all_ok(''),  # delete_old_nodes_from_cluster
            self.__side_effect_return_cluster_state_all_nodes(None),  # delete_old_nodes_from_cluster
            self.__side_effect_all_ok(''),  # delete_old_nodes_from_cluster
            self.__side_effect_return_cluster_state_all_nodes(None),  # delete_old_nodes_from_cluster
            self.__side_effect_all_ok(''),  # delete_old_nodes_from_cluster
        ]

        urlopen_mock = MagicMock(side_effect=http_calls)
        urllib.request.urlopen = urlopen_mock

        controller.deploy_new_version()

        senza_passive_versions_mock.assert_called_with(STACK_NAME)
        senza_create_mock.assert_called_once_with(STACK_NAME, test_version, IMAGE_VERSION)
        senza_switch_mock.assert_called_once_with(STACK_NAME, test_version, 100)
        senza_delete_mock.assert_called_once_with(STACK_NAME, test_version)
        senza_instances_mock.assert_called_with(STACK_NAME, test_version)

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
        response_mock.readall.return_value = bytes(json.dumps(CLUSTER_OLD_NODES), 'utf-8')
        return response_mock

    def __side_effect_return_cluster_state_all_registered_nodes(self, value):
        response_mock = MagicMock()
        # return OK for all HTTP requests
        response_mock.getcode.return_value = HTTP_CODE_OK
        response_mock.readall.return_value = bytes(json.dumps(CLUSTER_ALL_REGISTERED), 'utf-8')
        return response_mock

    def __side_effect_return_cluster_state_new_nodes(self, value):
        response_mock = MagicMock()
        # return OK for all HTTP requests
        response_mock.getcode.return_value = HTTP_CODE_OK
        response_mock.readall.return_value = bytes(json.dumps(CLUSTER_NEW_NODES), 'utf-8')
        return response_mock

    def __side_effect_return_cluster_state_old_nodes(self, value):
        response_mock = MagicMock()
        # return OK for all HTTP requests
        response_mock.getcode.return_value = HTTP_CODE_OK
        response_mock.readall.return_value = bytes(json.dumps(CLUSTER_OLD_NODES), 'utf-8')
        return response_mock

    def __side_effect_return_cluster_state_all_nodes(self, value):
        response_mock = MagicMock()
        # return OK for all HTTP requests
        response_mock.getcode.return_value = HTTP_CODE_OK
        response_mock.readall.return_value = bytes(json.dumps(CLUSTER_ALL_NODES), 'utf-8')
        return response_mock

    def __side_effect_return_cluster_state_all_nodes_one_not_active(self, value):
        response_mock = MagicMock()
        # return OK for all HTTP requests
        response_mock.getcode.return_value = HTTP_CODE_OK
        response_mock.readall.return_value = bytes(json.dumps(CLUSTER_ALL_NODES_ONE_NOT_ACTIVE), 'utf-8')
        return response_mock

    def __side_effect_return_cluster_state_no_leader(self, value):
        regex_api_cluster_status = re.compile('^' + API_URL.replace('.', '\.') + '.*' + '\?action=CLUSTERSTATUS')
        cluster_status_match = regex_api_cluster_status.match(value.get_full_url())
        response_mock = MagicMock()
        # return OK for all HTTP requests
        response_mock.getcode.return_value = HTTP_CODE_OK
        if cluster_status_match:
            response_mock.readall.return_value = bytes(json.dumps(CLUSTER_NO_LEADER), 'utf-8')
        return response_mock

    def __side_effect_return_cluster_state_only_one_active_replica(self, value):
        regex_api_cluster_status = re.compile('^' + API_URL.replace('.', '\.') + '.*' + '\?action=CLUSTERSTATUS')
        cluster_status_match = regex_api_cluster_status.match(value.get_full_url())
        response_mock = MagicMock()
        # return OK for all HTTP requests
        response_mock.getcode.return_value = HTTP_CODE_OK
        if cluster_status_match:
            response_mock.readall.return_value = bytes(json.dumps(CLUSTER_ONLY_ONE_ACTIVE_REPLICA), 'utf-8')
        return response_mock
