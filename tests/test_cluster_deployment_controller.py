#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mock import MagicMock
from unittest import TestCase
from solrcloud_cli.controllers.cluster_deployment_controller import ClusterDeploymentController
from solrcloud_cli.services.senza_deployment_service import DeploymentService
from solrcloud_cli.services.solr_collections_service import SolrCollectionsService

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

NOT_ENOUGH_NODES = [{'name': 'test', 'nodes': ['2.2.2.0', '2.2.2.1'], 'weight': '0'}]

SINGLE_NODE_SET = [{'name': 'blue', 'nodes': ['1.1.1.0', '1.1.1.1', '1.1.1.2'], 'weight': '100'}]
TWO_NODE_SETS_OLD_ACTIVE = [
    {'name': 'green', 'nodes': ['1.1.1.0', '1.1.1.1', '1.1.1.2'], 'weight': '0'},
    {'name': 'blue', 'nodes': ['0.0.0.0', '0.0.0.1', '0.0.0.2'], 'weight': '100'}
]
TWO_NODE_SETS_NEW_ACTIVE = [
    {'name': 'green', 'nodes': ['1.1.1.0', '1.1.1.1', '1.1.1.2'], 'weight': '100'},
    {'name': 'blue', 'nodes': ['0.0.0.0', '0.0.0.1', '0.0.0.2'], 'weight': '0'}
]

COLLECTION = 'test-collection01'
SHARD = 'shard1'

CLUSTER_OLD_NODES = {
    "cluster": {
        "collections": {
            COLLECTION: {
                "replicationFactor": str(REPLICATION_FACTOR),
                "shards": {
                    SHARD: {
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
            COLLECTION: {
                "replicationFactor": str(REPLICATION_FACTOR),
                "shards": {
                    SHARD: {
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
            COLLECTION: {
                "replicationFactor": str(REPLICATION_FACTOR),
                "shards": {
                    SHARD: {
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
            COLLECTION: {
                "replicationFactor": str(REPLICATION_FACTOR),
                "shards": {
                    SHARD: {
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
            COLLECTION: {
                "replicationFactor": str(REPLICATION_FACTOR),
                "shards": {
                    SHARD: {
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
            COLLECTION: {
                "replicationFactor": str(REPLICATION_FACTOR),
                "shards": {
                    SHARD: {
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
            COLLECTION: {
                "replicationFactor": str(REPLICATION_FACTOR),
                "shards": {
                    SHARD: {
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
            COLLECTION: {
                "replicationFactor": str(REPLICATION_FACTOR),
                "shards": {
                    SHARD: {
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
    __solr_collections_service = None

    def setUp(self):
        urllib.request.urlopen = MagicMock(side_effect=self.__side_effect_return_cluster_state_old_nodes)
        deployment_service = MagicMock(spec=DeploymentService)

        self.__solr_collections_service = SolrCollectionsService(base_url=BASE_URL,
                                                                 oauth_token=OAUTH_TOKEN,
                                                                 replication_factor=REPLICATION_FACTOR,
                                                                 sharding_level=-1)

        self.__controller = ClusterDeploymentController(stack_name=STACK_NAME,
                                                        image_version=IMAGE_VERSION,
                                                        solr_collections_service=self.__solr_collections_service,
                                                        deployment_service=deployment_service)
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
        deployment_service_mock = MagicMock()
        deployment_service_mock.get_all_node_sets.return_value = TWO_NODE_SETS_OLD_ACTIVE
        self.__controller.set_deployment_service(deployment_service_mock)

        solr_collections_service_mock = MagicMock()
        solr_collections_service_mock.add_replica_to_cluster.return_value = 0
        cluster_states = [
            CLUSTER_ALL_REGISTERED,
            CLUSTER_ALL_NODES
        ]
        solr_collections_service_mock.get_cluster_state.side_effect = cluster_states
        self.__controller.set_solr_collections_service(solr_collections_service_mock)

        self.__controller.add_new_nodes_to_cluster()

        self.assertEquals(solr_collections_service_mock.get_cluster_state.call_count, 2)
        self.assertEquals(solr_collections_service_mock.add_replica_to_cluster.call_count, 3)

    def test_should_return_error_because_of_not_enough_nodes_for_cluster_layout(self):
        urllib.request.urlopen = MagicMock(side_effect=self.__side_effect_return_cluster_state_old_nodes)
        deployment_service_mock = MagicMock()
        deployment_service_mock.get_nodes_of_node_set.return_value = NOT_ENOUGH_NODES
        self.__controller.set_deployment_service(deployment_service_mock)
        with self.assertRaises(Exception, msg='Not enough instances for current cluster layout: [2]<[3]'):
            self.__controller.add_new_nodes_to_cluster()

    def test_should_wait_until_all_nodes_are_active(self):
        deployment_service_mock = MagicMock()
        deployment_service_mock.get_all_node_sets.return_value = TWO_NODE_SETS_OLD_ACTIVE
        self.__controller.set_deployment_service(deployment_service_mock)

        solr_collections_service_mock = MagicMock()
        solr_collections_service_mock.add_replica_to_cluster.return_value = 0
        cluster_states = [
            CLUSTER_ALL_REGISTERED,
            CLUSTER_ALL_NODES_ONE_NOT_ACTIVE,
            CLUSTER_ALL_NODES
        ]
        solr_collections_service_mock.get_cluster_state.side_effect = cluster_states
        self.__controller.set_solr_collections_service(solr_collections_service_mock)

        self.__controller.add_new_nodes_to_cluster()

        self.assertEquals(solr_collections_service_mock.get_cluster_state.call_count, 3)
        self.assertEquals(solr_collections_service_mock.add_replica_to_cluster.call_count, 3)

    def test_should_raise_exception_on_timeout_when_adding_nodes(self):
        deployment_service_mock = MagicMock()
        deployment_service_mock.get_all_node_sets.return_value = TWO_NODE_SETS_OLD_ACTIVE
        self.__controller.set_deployment_service(deployment_service_mock)

        solr_collections_service_mock = MagicMock()
        solr_collections_service_mock.add_replica_to_cluster.return_value = 0
        cluster_states = [
            CLUSTER_ALL_REGISTERED,
            CLUSTER_ALL_NODES_ONE_NOT_ACTIVE
        ]
        solr_collections_service_mock.get_cluster_state.side_effect = cluster_states
        self.__controller.set_solr_collections_service(solr_collections_service_mock)
        self.__controller.set_add_node_retry_wait(1)

        with self.assertRaisesRegex(Exception, 'Timeout while adding new nodes to cluster'):
            self.__controller.add_new_nodes_to_cluster()

        self.assertEquals(solr_collections_service_mock.get_cluster_state.call_count, 2)
        self.assertEquals(solr_collections_service_mock.add_replica_to_cluster.call_count, 3)

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
        deployment_service_mock = MagicMock()
        deployment_service_mock.get_all_node_sets.return_value = TWO_NODE_SETS_NEW_ACTIVE
        self.__controller.set_deployment_service(deployment_service_mock)

        solr_collections_service_mock = MagicMock()
        solr_collections_service_mock.delete_replica_from_cluster.return_value = 0
        solr_collections_service_mock.get_cluster_state.return_value = CLUSTER_OLD_NODES
        self.__controller.set_solr_collections_service(solr_collections_service_mock)

        self.__controller.delete_old_nodes_from_cluster()

        self.assertEquals(solr_collections_service_mock.get_cluster_state.call_count, 5)
        self.assertEquals(solr_collections_service_mock.delete_replica_from_cluster.call_count, 3)

    def test_should_return_failure_after_deleting_multiple_nodes_from_shard_without_leader(self):
        urlopen_mock = MagicMock(side_effect=self.__side_effect_return_cluster_state_no_leader)
        urllib.request.urlopen = urlopen_mock
        deployment_service_mock = MagicMock()
        deployment_service_mock.get_all_node_sets.return_value = SINGLE_NODE_SET
        self.__controller.set_deployment_service(deployment_service_mock)
        with self.assertRaisesRegex(Exception, 'Shard \[shard[0-9]\] of collection \[[a-z0-9\-]+\] has no active '
                                               'leader'):
            self.__controller.delete_old_nodes_from_cluster()

    def test_should_return_failure_after_deleting_multiple_nodes_with_only_one_active_replica(self):
        urlopen_mock = MagicMock(side_effect=self.__side_effect_return_cluster_state_only_one_active_replica)
        urllib.request.urlopen = urlopen_mock
        deployment_service_mock = MagicMock()
        deployment_service_mock.get_all_node_sets.return_value = SINGLE_NODE_SET
        self.__controller.set_deployment_service(deployment_service_mock)
        with self.assertRaisesRegex(Exception, 'Shard \[shard[0-9]\] of collection \[[a-z0-9\-]+\] has not enough '
                                               'active nodes: \[[1]\]'):
            self.__controller.delete_old_nodes_from_cluster()

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
        deployment_service_mock = MagicMock(spec=DeploymentService)
        deployment_service_mock.create_node_set.return_value = 0
        node_sets = [
            SINGLE_NODE_SET
        ]
        deployment_service_mock.get_all_node_sets.side_effect = node_sets

        solr_collections_service_mock = MagicMock(spec=SolrCollectionsService)
        solr_collections_service_mock.get_cluster_state.return_value = CLUSTER_ALL_REGISTERED

        controller = ClusterDeploymentController(stack_name=STACK_NAME,
                                                 image_version=IMAGE_VERSION,
                                                 solr_collections_service=solr_collections_service_mock,
                                                 deployment_service=deployment_service_mock)

        self.assertEquals('green', controller.get_passive_stack_version(), 'Wrong stack version')
        deployment_service_mock.get_all_node_sets.assert_called_once()

    def test_should_not_raise_any_exception_when_creating_a_new_cluster(self):
        deployment_service_mock = MagicMock(spec=DeploymentService)
        deployment_service_mock.create_node_set.return_value = 0
        node_sets = [
            SINGLE_NODE_SET,
            TWO_NODE_SETS_OLD_ACTIVE
        ]
        deployment_service_mock.get_all_node_sets.side_effect = node_sets

        solr_collections_service_mock = MagicMock(spec=SolrCollectionsService)
        solr_collections_service_mock.get_cluster_state.return_value = CLUSTER_ALL_REGISTERED

        controller = ClusterDeploymentController(stack_name=STACK_NAME,
                                                 image_version=IMAGE_VERSION,
                                                 solr_collections_service=solr_collections_service_mock,
                                                 deployment_service=deployment_service_mock)
        controller.create_cluster()

        deployment_service_mock.create_node_set.assert_called_once_with(STACK_NAME, 'green', IMAGE_VERSION)
        self.assertEquals(deployment_service_mock.get_all_node_sets.call_count, 2)
        self.assertEquals(solr_collections_service_mock.get_cluster_state.call_count, 2)

    def test_should_wait_until_all_nodes_are_registered_when_creating_a_new_cluster(self):
        deployment_service_mock = MagicMock(spec=DeploymentService)
        deployment_service_mock.create_node_set.return_value = 0
        node_sets = [
            SINGLE_NODE_SET,
            TWO_NODE_SETS_OLD_ACTIVE
        ]
        deployment_service_mock.get_all_node_sets.side_effect = node_sets

        solr_collections_service_mock = MagicMock(spec=SolrCollectionsService)
        cluster_states = [
            CLUSTER_OLD_NODES,
            CLUSTER_OLD_NODES,
            CLUSTER_ALL_REGISTERED
        ]
        solr_collections_service_mock.get_cluster_state.side_effect = cluster_states

        controller = ClusterDeploymentController(stack_name=STACK_NAME,
                                                 image_version=IMAGE_VERSION,
                                                 solr_collections_service=solr_collections_service_mock,
                                                 deployment_service=deployment_service_mock)
        controller.set_create_cluster_retry_wait(0)
        controller.set_create_cluster_timeout(1)
        controller.create_cluster()

        deployment_service_mock.create_node_set.assert_called_once_with(STACK_NAME, 'green', IMAGE_VERSION)
        self.assertEquals(deployment_service_mock.get_all_node_sets.call_count, 2)
        self.assertEquals(solr_collections_service_mock.get_cluster_state.call_count, 3)

    def test_should_raise_exception_on_timeout_when_creating_a_new_cluster(self):
        deployment_service_mock = MagicMock(spec=DeploymentService)
        deployment_service_mock.create_node_set.return_value = 0
        node_sets = [
            SINGLE_NODE_SET,
            TWO_NODE_SETS_OLD_ACTIVE
        ]
        deployment_service_mock.get_all_node_sets.side_effect = node_sets

        solr_collections_service_mock = MagicMock(spec=SolrCollectionsService)
        solr_collections_service_mock.get_cluster_state.return_value = CLUSTER_OLD_NODES

        controller = ClusterDeploymentController(stack_name=STACK_NAME,
                                                 image_version=IMAGE_VERSION,
                                                 solr_collections_service=solr_collections_service_mock,
                                                 deployment_service=deployment_service_mock)
        controller.set_create_cluster_retry_wait(1)
        controller.set_create_cluster_timeout(1)
        with self.assertRaisesRegex(Exception, 'Timeout while creating new cluster, not all new nodes have been '
                                               'registered in time'):
            controller.create_cluster()

        deployment_service_mock.create_node_set.assert_called_once_with(STACK_NAME, 'green', IMAGE_VERSION)
        self.assertEquals(deployment_service_mock.get_all_node_sets.call_count, 2)
        self.assertEquals(solr_collections_service_mock.get_cluster_state.call_count, 2)

    def test_should_not_raise_any_exception_when_deleting_a_cluster(self):
        deployment_service_mock = MagicMock(spec=DeploymentService)
        deployment_service_mock.delete_node_set.return_value = 0
        deployment_service_mock.get_all_node_sets.return_value = TWO_NODE_SETS_NEW_ACTIVE

        solr_collections_service_mock = MagicMock(spec=SolrCollectionsService)
        solr_collections_service_mock.get_cluster_state.return_value = CLUSTER_ALL_NODES

        controller = ClusterDeploymentController(stack_name=STACK_NAME,
                                                 image_version=IMAGE_VERSION,
                                                 solr_collections_service=solr_collections_service_mock,
                                                 deployment_service=deployment_service_mock)
        controller.delete_cluster()

        deployment_service_mock.delete_node_set.assert_called_once_with(STACK_NAME, 'blue')
        deployment_service_mock.get_all_node_sets.assert_called_once()
        solr_collections_service_mock.get_cluster_state.assert_called_once()

    def test_should_not_raise_any_exception_when_switching_to_another_cluster_version(self):
        deployment_service_mock = MagicMock(spec=DeploymentService)
        deployment_service_mock.switch_traffic.return_value = 0
        deployment_service_mock.get_all_node_sets.return_value = TWO_NODE_SETS_OLD_ACTIVE

        solr_collections_service_mock = MagicMock(spec=SolrCollectionsService)
        solr_collections_service_mock.get_cluster_state.return_value = CLUSTER_ALL_NODES

        controller = ClusterDeploymentController(stack_name=STACK_NAME,
                                                 image_version=IMAGE_VERSION,
                                                 solr_collections_service=solr_collections_service_mock,
                                                 deployment_service=deployment_service_mock)
        controller.switch_traffic()

        deployment_service_mock.switch_traffic.assert_called_once_with(STACK_NAME, 'green', 100)
        deployment_service_mock.get_all_node_sets.assert_called_once()
        solr_collections_service_mock.get_cluster_state.assert_called_once()

    def test_should_not_raise_exceptions_when_executing_all_deployment_steps(self):
        deployment_service_mock = MagicMock(spec=DeploymentService)
        deployment_service_mock.create_node_set.return_value = 0
        deployment_service_mock.switch_traffic.return_value = 0
        deployment_service_mock.delete_node_set.return_value = 0
        node_sets = [
            SINGLE_NODE_SET, # create node set
            TWO_NODE_SETS_OLD_ACTIVE,  # create node set
            TWO_NODE_SETS_OLD_ACTIVE,  # add new nodes
            TWO_NODE_SETS_OLD_ACTIVE,  # add new nodes
            TWO_NODE_SETS_OLD_ACTIVE,  # switch traffic
            TWO_NODE_SETS_NEW_ACTIVE,  # delete old nodes
            TWO_NODE_SETS_NEW_ACTIVE,  # delete old nodes
            TWO_NODE_SETS_NEW_ACTIVE,  # delete node set
        ]
        deployment_service_mock.get_all_node_sets.side_effect = node_sets

        solr_collections_service_mock = MagicMock(spec=SolrCollectionsService)
        cluster_states = [
            CLUSTER_ALL_REGISTERED,  # create node set
            CLUSTER_ALL_NODES,  # create node set
            CLUSTER_ALL_NODES,  # add new nodes
            CLUSTER_ALL_NODES,  # add new nodes
            CLUSTER_ALL_NODES,  # delete old nodes
            CLUSTER_ALL_NODES,  # delete old nodes
            CLUSTER_ALL_NODES,  # delete old nodes
            CLUSTER_ALL_NODES,  # delete old nodes
            CLUSTER_ALL_NODES,  # delete old nodes
        ]
        solr_collections_service_mock.get_cluster_state.side_effect = cluster_states

        controller = ClusterDeploymentController(stack_name=STACK_NAME,
                                                 image_version=IMAGE_VERSION,
                                                 solr_collections_service=solr_collections_service_mock,
                                                 deployment_service=deployment_service_mock)

        controller.set_leader_check_retry_count(1)
        controller.set_leader_check_retry_wait(0)
        controller.set_add_node_retry_count(1)
        controller.set_add_node_retry_wait(0)
        controller.set_add_node_timeout(1)

        controller.deploy_new_version()

        deployment_service_mock.create_node_set.assert_called_once_with(STACK_NAME, 'green', '0.0.0')
        deployment_service_mock.switch_traffic.assert_called_once_with(STACK_NAME, 'green', 100)
        deployment_service_mock.delete_node_set.assert_called_once_with(STACK_NAME, 'blue')
        self.assertEquals(deployment_service_mock.get_all_node_sets.call_count, 8)
        self.assertEquals(solr_collections_service_mock.get_cluster_state.call_count, 9)

    def test_should_not_raise_exception_if_shard_is_healthy(self):
        self.__controller.verify_shard_health(COLLECTION, SHARD)

    def test_should_raise_exception_if_shard_has_no_active_leader(self):
        urlopen_mock = MagicMock(side_effect=self.__side_effect_return_cluster_state_no_leader)
        urllib.request.urlopen = urlopen_mock
        with self.assertRaisesRegex(Exception, 'Shard \[{}\] of collection \[{}\] has no active leader'
                                               .format(SHARD, COLLECTION)):
            self.__controller.verify_shard_health(COLLECTION, SHARD)

    def test_should_raise_exception_if_shard_has_not_enough_active_nodes(self):
        urlopen_mock = MagicMock(side_effect=self.__side_effect_return_cluster_state_only_one_active_replica)
        urllib.request.urlopen = urlopen_mock
        with self.assertRaisesRegex(Exception, 'Shard \[{}\] of collection \[{}\] has not enough active nodes: \[{}\]'
                                               .format(SHARD, COLLECTION, '1')):
            self.__controller.verify_shard_health(COLLECTION, SHARD)

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
        response_mock.read.return_value = bytes(json.dumps(CLUSTER_OLD_NODES), 'utf-8')
        return response_mock

    def __side_effect_return_cluster_state_all_registered_nodes(self, value):
        response_mock = MagicMock()
        # return OK for all HTTP requests
        response_mock.getcode.return_value = HTTP_CODE_OK
        response_mock.read.return_value = bytes(json.dumps(CLUSTER_ALL_REGISTERED), 'utf-8')
        return response_mock

    def __side_effect_return_cluster_state_new_nodes(self, value):
        response_mock = MagicMock()
        # return OK for all HTTP requests
        response_mock.getcode.return_value = HTTP_CODE_OK
        response_mock.read.return_value = bytes(json.dumps(CLUSTER_NEW_NODES), 'utf-8')
        return response_mock

    def __side_effect_return_cluster_state_old_nodes(self, value):
        response_mock = MagicMock()
        # return OK for all HTTP requests
        response_mock.getcode.return_value = HTTP_CODE_OK
        response_mock.read.return_value = bytes(json.dumps(CLUSTER_OLD_NODES), 'utf-8')
        return response_mock

    def __side_effect_return_cluster_state_all_nodes(self, value):
        response_mock = MagicMock()
        # return OK for all HTTP requests
        response_mock.getcode.return_value = HTTP_CODE_OK
        response_mock.read.return_value = bytes(json.dumps(CLUSTER_ALL_NODES), 'utf-8')
        return response_mock

    def __side_effect_return_cluster_state_all_nodes_one_not_active(self, value):
        response_mock = MagicMock()
        # return OK for all HTTP requests
        response_mock.getcode.return_value = HTTP_CODE_OK
        response_mock.read.return_value = bytes(json.dumps(CLUSTER_ALL_NODES_ONE_NOT_ACTIVE), 'utf-8')
        return response_mock

    def __side_effect_return_cluster_state_no_leader(self, value):
        regex_api_cluster_status = re.compile('^' + API_URL.replace('.', '\.') + '.*' + '\?action=CLUSTERSTATUS')
        cluster_status_match = regex_api_cluster_status.match(value.get_full_url())
        response_mock = MagicMock()
        # return OK for all HTTP requests
        response_mock.getcode.return_value = HTTP_CODE_OK
        if cluster_status_match:
            response_mock.read.return_value = bytes(json.dumps(CLUSTER_NO_LEADER), 'utf-8')
        return response_mock

    def __side_effect_return_cluster_state_only_one_active_replica(self, value):
        regex_api_cluster_status = re.compile('^' + API_URL.replace('.', '\.') + '.*' + '\?action=CLUSTERSTATUS')
        cluster_status_match = regex_api_cluster_status.match(value.get_full_url())
        response_mock = MagicMock()
        # return OK for all HTTP requests
        response_mock.getcode.return_value = HTTP_CODE_OK
        if cluster_status_match:
            response_mock.read.return_value = bytes(json.dumps(CLUSTER_ONLY_ONE_ACTIVE_REPLICA), 'utf-8')
        return response_mock
