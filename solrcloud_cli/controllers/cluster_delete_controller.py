#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import urllib.error
import urllib.request

from solrcloud_cli.controllers.cluster_controller import ClusterController
from solrcloud_cli.services.senza_wrapper import SenzaWrapper

COLLECTIONS_API_PATH = '/admin/collections'


class ClusterDeleteController(ClusterController):

    def __init__(self, base_url: str, stack_name: str, oauth_token: str, senza_wrapper: SenzaWrapper):
        self._api_url = base_url.strip('/') + COLLECTIONS_API_PATH
        self._oauth_token = oauth_token
        self._stack_name = stack_name
        self._senza = senza_wrapper

    def delete_cluster(self):
        stack_versions = self._senza.get_all_stack_versions(self._stack_name)
        if not stack_versions:
            raise Exception('No active stack version found')
        self.delete_all_collections_in_cluster()
        for version in stack_versions:
            self.switch_off_traffic(version['version'])
            self.delete_cluster_version(version['version'])

    def delete_cluster_version(self, stack_version: str):
        self._senza.delete_stack_version(self._stack_name, stack_version)

    def switch_off_traffic(self, stack_version: str):
        try:
            self._senza.switch_traffic(self._stack_name, stack_version, 0)
        except Exception as e:
            if str(e).startswith("Traffic weight did not change"):
                logging.info('Traffic was not switched, it was already off for stack version [{}]'
                             .format(stack_version))
            else:
                raise e

    def delete_all_collections_in_cluster(self):
        cluster_state = self.get_cluster_state()
        for collection in cluster_state['cluster']['collections'].keys():
            try:
                self.delete_collection_in_cluster(collection)
            except Exception as e:
                logging.warning('Could not delete collection [{}] in cluster: [{}]'.format(collection, e))
        return 0

    def delete_collection_in_cluster(self, collection_name: str):
        url = self._api_url + '?action=DELETE&name=' + collection_name
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
