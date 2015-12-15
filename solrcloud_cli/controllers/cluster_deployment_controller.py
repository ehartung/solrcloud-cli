#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys
import time
import urllib.error
import urllib.request

from solrcloud_cli.controllers.cluster_controller import ClusterController
from solrcloud_cli.services.senza_wrapper import SenzaWrapper

DEFAULT_LEADER_CHECK_RETRY_COUNT = 30
DEFAULT_LEADER_CHECK_RETRY_WAIT = 1
DEFAULT_ADD_NODE_RETRY_COUNT = 30
DEFAULT_ADD_NODE_RETRY_WAIT = 10
DEFAULT_ADD_NODE_TIMEOUT = 900
DEFAULT_CREATE_CLUSTER_RETRY_WAIT = 10
DEFAULT_CREATE_CLUSTER_TIMEOUT = 120
COLLECTIONS_API_PATH = '/admin/collections'

BLUE_GREEN_DEPLOYMENT_VERSIONS = ['blue', 'green']


class ClusterDeploymentController(ClusterController):

    __image_version = None
    __sharding_level = 0
    __replication_factor = 0
    __stack_version = ''

    __leader_check_retry_count = DEFAULT_LEADER_CHECK_RETRY_COUNT
    __leader_check_retry_wait = DEFAULT_LEADER_CHECK_RETRY_WAIT
    __add_node_retry_count = DEFAULT_ADD_NODE_RETRY_COUNT
    __add_node_retry_wait = DEFAULT_ADD_NODE_RETRY_WAIT
    __add_node_timeout = DEFAULT_ADD_NODE_TIMEOUT
    __create_cluster_retry_wait = DEFAULT_CREATE_CLUSTER_RETRY_WAIT
    __create_cluster_timeout = DEFAULT_CREATE_CLUSTER_TIMEOUT

    def __init__(self, base_url: str, stack_name: str, image_version: str, oauth_token: str,
                 senza_wrapper: SenzaWrapper):

        self._api_url = base_url.strip('/') + COLLECTIONS_API_PATH
        self._oauth_token = oauth_token
        self._stack_name = stack_name
        self.__image_version = image_version
        self._senza = senza_wrapper
        cluster_state = self.get_cluster_state()
        if cluster_state and cluster_state['cluster']['collections'].keys():
            first_collection = list(cluster_state['cluster']['collections'].keys())[0]
            self.__replication_factor = \
                int(cluster_state['cluster']['collections'][first_collection]['replicationFactor'])
            self.__sharding_level = \
                len(list(cluster_state['cluster']['collections'][first_collection]['shards'].keys()))

    def deploy_new_version(self):
        """
        Deploy a new version of the Solr cloud cluster using blue/green deployment strategy.
        """
        self.create_cluster()
        self.add_new_nodes_to_cluster()
        self.switch_traffic()
        self.delete_old_nodes_from_cluster()
        self.delete_cluster()

    def set_leader_check_retry_count(self, retry_count: int):
        self.__leader_check_retry_count = retry_count

    def set_leader_check_retry_wait(self, retry_wait: int):
        self.__leader_check_retry_wait = retry_wait

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

    def get_passive_stack_version(self):
        passive_stack_version = self._senza.get_passive_stack_version(self._stack_name)
        if not passive_stack_version:
            current_version = self._senza.get_active_stack_version(self._stack_name)
            passive_stack_version = list(filter(lambda x: x != current_version, BLUE_GREEN_DEPLOYMENT_VERSIONS))[0]
        return passive_stack_version

    def create_cluster(self):
        self._senza.create_stack(self._stack_name, self.get_passive_stack_version(), self.__image_version)

        # Wait for all nodes being registered in cluster
        nodes = self.get_cluster_nodes(self._stack_name, self.get_passive_stack_version())
        timer = 0
        all_nodes_added = False
        while not all_nodes_added and timer < self.__create_cluster_timeout:
            cluster_state = self.get_cluster_state()
            all_nodes_added = True
            for node in nodes:
                node_name = node + ':8983_solr'
                if node_name not in cluster_state['cluster']['live_nodes']:
                    all_nodes_added = False
                    break
            if not all_nodes_added:
                time.sleep(self.__create_cluster_retry_wait)
                timer += self.__create_cluster_retry_wait
                sys.stdout.write('.')
                sys.stdout.flush()
        if timer >= self.__create_cluster_timeout:
            raise Exception('Timeout while creating new cluster, not all new nodes have been registered in time')

    def delete_cluster(self):
        old_stack_version = self.get_passive_stack_version()
        self._senza.delete_stack_version(self._stack_name, old_stack_version)

    def add_new_nodes_to_cluster(self):
        nodes = self.get_cluster_nodes(self._stack_name, self.get_passive_stack_version())
        cluster_state = self.get_cluster_state()

        if len(nodes) < self.__sharding_level * self.__replication_factor:
            raise Exception('Not enough instances for current cluster layout: [{}]<[{}]'.format(
                len(nodes), self.__sharding_level * self.__replication_factor))

        # Add nodes to cluster
        for collection_name, collection_values in cluster_state['cluster']['collections'].items():
            shard_counter = 0
            for shard_name, shard_values in collection_values['shards'].items():
                for replica_counter in range(self.__replication_factor):
                    node_index = shard_counter + replica_counter * self.__sharding_level
                    node_name = nodes[node_index] + ':8983_solr'
                    if len(list(filter(lambda replica: replica[1]['node_name'] == node_name,
                                shard_values['replicas'].items()))) == 0:

                        logging.info('Adding replica for collection [{}], shard [{}] on node [{}]'.format(
                            collection_name, shard_name, node_name))
                        self.add_replica_to_cluster(collection_name, shard_name, node_name)

                shard_counter += 1

        # Wait for all replicas being active in cluster
        timer = 0
        all_replicas_active = False
        while not all_replicas_active and timer < self.__add_node_timeout:
            cluster_state = self.get_cluster_state()
            all_replicas_active = True
            for collection_name, collection_values in cluster_state['cluster']['collections'].items():
                for shard_name, shard_values in collection_values['shards'].items():
                    for replica_name, replica_values in shard_values['replicas'].items():
                        if replica_values['state'] != 'active':
                            all_replicas_active = False
                            break
            if not all_replicas_active:
                time.sleep(self.__add_node_retry_wait)
                timer += self.__add_node_retry_wait
                sys.stdout.write('.')
                sys.stdout.flush()
        if timer >= self.__add_node_timeout:
            raise Exception('Timeout while adding new nodes to cluster')

    def delete_old_nodes_from_cluster(self):
        nodes = self.get_cluster_nodes(self._stack_name, self.get_passive_stack_version())
        cluster_state = self.get_cluster_state()

        for collection_name, collection_values in cluster_state['cluster']['collections'].items():
            for shard_name, shard_values in collection_values['shards'].items():
                for replica_name, replica_values in shard_values['replicas'].items():
                    node_ip = replica_values['node_name'].replace(':8983_solr', '')
                    if node_ip in nodes:
                        # Check whether shard has an active leader and at least two active nodes before going on
                        logging.info('Checking for active nodes and leader in shard [{}] of collection [{}]'.format(
                            shard_name, collection_name))
                        shard_has_active_leader = False
                        active_nodes_in_shard = 0
                        retries = 0
                        while ((not shard_has_active_leader or active_nodes_in_shard < 2) and
                                retries <= self.__leader_check_retry_count):
                            current_cluster_state = self.get_cluster_state()
                            shard_has_active_leader = self.has_active_leader(current_cluster_state, collection_name,
                                                                             shard_name)
                            active_nodes_in_shard = self.get_number_of_active_nodes(current_cluster_state,
                                                                                    collection_name, shard_name)
                            time.sleep(self.__leader_check_retry_wait)
                            retries += 1

                        if not shard_has_active_leader:
                            raise Exception('Shard [{}] of collection [{}] has no active leader'.format(
                                shard_name, collection_name))

                        if active_nodes_in_shard < 2:
                            raise Exception('Shard [{}] of collection [{}] has not enough active nodes: [{}]'.format(
                                shard_name, collection_name, active_nodes_in_shard))

                        logging.info('INFO Deleting replica [{}] for collection [{}] and shard [{}]'.format(
                            replica_name, collection_name, shard_name))
                        self.delete_replica_from_cluster(collection_name, shard_name, replica_name)

    def add_replica_to_cluster(self, collection_name: str, shard_name: str, node_name: str):
        url = self._api_url + '?action=ADDREPLICA'
        url += '&collection=' + collection_name
        url += '&shard=' + shard_name
        url += '&node=' + node_name
        retry = True
        retry_count = 0
        while retry and retry_count <= self.__add_node_retry_count:
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
            headers = dict()
            headers['Authorization'] = 'Bearer ' + self._oauth_token
            request = urllib.request.Request(url, headers=headers)
            response = urllib.request.urlopen(request)
            code = response.getcode()
            response.close()
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

    def get_cluster_nodes(self, stack_name, stack_version):
        return sorted(self._senza.get_stack_instances(stack_name, stack_version))

    def switch_traffic(self):
        self._senza.switch_traffic(self._stack_name, self.get_passive_stack_version(), 100)

    @staticmethod
    def has_active_leader(cluster: dict, collection: str, shard: str):
        shard_state = cluster['cluster']['collections'][collection]['shards'][shard]['state']
        shard_replicas = cluster['cluster']['collections'][collection]['shards'][shard]['replicas']
        if shard_state == 'active':
            for name, replica in shard_replicas.items():
                replica_state = replica['state']
                replica_is_leader = 'leader' in replica.keys() and replica['leader']
                if replica_state == 'active' and replica_is_leader:
                    logging.info('Active leader of shard [{}] in collection [{}] is [{}]'.format(
                        shard, collection, name))
                    return True
        else:
            logging.warning('Shard [{}] of collection [{}] is not active (state=[{}])'.format(shard, collection,
                                                                                              shard_state))
        return False

    @staticmethod
    def get_number_of_active_nodes(cluster: dict, collection: str, shard: str):
        shard_replicas = cluster['cluster']['collections'][collection]['shards'][shard]['replicas']
        if shard_replicas:
            number_of_active_nodes = len(list(filter(lambda x: x['state'] == 'active', shard_replicas.values())))
            logging.info('Number of active nodes in shard [{}] of collection [{}] is [{}]'
                         .format(shard, collection, number_of_active_nodes))
            return number_of_active_nodes
        else:
            return 0
