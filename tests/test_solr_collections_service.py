import json
import urllib.error
import urllib.request

from mock import MagicMock
from unittest import TestCase

from solrcloud_cli.services.solr_collections_service import SolrCollectionsService

BASE_URL = 'http://example.org/solr'
API_URL = BASE_URL + '/admin/collections'
STACK_NAME = 'test'
IMAGE_VERSION = '0.0.0'
OAUTH_TOKEN = 'test0token'
CONFIG = 'test.yaml'
REPLICATION_FACTOR = 3

HTTP_CODE_OK = 200
HTTP_CODE_UNKNOWN = 111
HTTP_CODE_BAD_REQUEST = 400
HTTP_CODE_TIMEOUT = 504
HTTP_CODE_ERROR = 500
HTTP_CODE_UNKNOWN_ERROR = 555

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


class TestClusterDeploymentController(TestCase):

    __urlopen_mock = None
    __solr_collections_service = None

    def setUp(self):
        self.__solr_collections_service = SolrCollectionsService(base_url=BASE_URL,
                                                                 oauth_token=OAUTH_TOKEN,
                                                                 replication_factor=REPLICATION_FACTOR,
                                                                 sharding_level=-1)

    def test_should_return_current_cluster_state(self):
        urllib.request.urlopen = MagicMock(side_effect=self.__side_effect_return_cluster_state_old_nodes)
        cluster_state = self.__solr_collections_service.get_cluster_state()
        self.assertEqual(CLUSTER_OLD_NODES, cluster_state, 'Cluster state does not match test cluster')


    def test_should_return_failure_because_of_unknown_status_code_from_solr_when_requesting_cluster_state(self):
        urllib.request.urlopen = MagicMock(side_effect=self.__side_effect_unknown_http_code)
        with self.assertRaisesRegex(Exception, 'Received unexpected status code from Solr: \[{}\]'
                .format(str(HTTP_CODE_UNKNOWN))):
            self.__solr_collections_service.get_cluster_state()


    def test_should_return_failure_because_of_unknown_http_error_when_requesting_cluster_state(self):
        urllib.request.urlopen = MagicMock(side_effect=self.__side_effect_unknown_http_error)
        with self.assertRaisesRegex(Exception, 'Failed sending request to Solr \[{}\]: HTTP Error {}: .*'
                .format(API_URL + '[^\]]+', str(HTTP_CODE_UNKNOWN_ERROR))):
            self.__solr_collections_service.get_cluster_state()

    def __side_effect_return_cluster_state_old_nodes(self, value):
        response_mock = MagicMock()
        # return OK for all HTTP requests
        response_mock.getcode.return_value = HTTP_CODE_OK
        response_mock.read.return_value = bytes(json.dumps(CLUSTER_OLD_NODES), 'utf-8')
        return response_mock

    def __side_effect_unknown_http_code(self, value):
        self.assertIsNotNone(value)
        response_mock = MagicMock()
        response_mock.getcode.return_value = HTTP_CODE_UNKNOWN
        return response_mock

    def __side_effect_unknown_http_error(self, value):
        raise urllib.error.HTTPError(url=None, code=HTTP_CODE_UNKNOWN_ERROR, msg=None, hdrs=None, fp=None)
