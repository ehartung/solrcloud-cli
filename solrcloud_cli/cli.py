#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import yaml
import os.path

from solrcloud_cli.controllers.cluster_bootstrap_controller import ClusterBootstrapController
from solrcloud_cli.controllers.cluster_delete_controller import ClusterDeleteController
from solrcloud_cli.controllers.cluster_deployment_controller import ClusterDeploymentController
from solrcloud_cli.services.senza_wrapper import SenzaWrapper

from argparse import ArgumentParser

DEFAULT_CONF_FILE = 'example.yaml'


def main():
    parser = ArgumentParser(description='SolrCloud CLI')
    parser.add_argument('name', help='Stack name of the Solr cloud cluster')
    parser.add_argument('command', help='Available commands: bootstrap, deploy, delete, create-new-cluster, '
                                        'delete-old-cluster, add-new-nodes, delete-old-nodes, switch')
    parser.add_argument('-i', '--image-version', help='Docker image version of Solr cloud instances')
    parser.add_argument('-b', '--base-url', default='http://localhost:8983/solr/',
                        help='Base URL of Solr administration API.')
    parser.add_argument('-s', '--sharding-level', default=1, help='Number of shards per collection')
    parser.add_argument('-r', '--replication-level', default=3, help='Number of replications per shard')
    parser.add_argument('-c', '--senza-configuration', default='solrcloud-appliance.yaml',
                        help='Senza configuration file for Solr cluster on AWS with STUPS')
    parser.add_argument('-t', '--token', help='OAuth token for connecting to the Solr cloud API')
    parser.add_argument('-f', '--config-file', help='Path to config file. (default: %s)' % DEFAULT_CONF_FILE,
                        dest='config')

    args = parser.parse_args()

    if not args.config:
        args.config = os.path.expanduser(DEFAULT_CONF_FILE)
        if not os.path.exists(args.config):
            print('Configuration file missing:', DEFAULT_CONF_FILE)
            parser.print_help()
            return

    if not args.command:
        print('No command given')
        parser.print_help()
        return

    if not args.name:
        print('No stack name given')
        parser.print_help()
        return

    with open(args.config, 'rb') as fd:
        settings = yaml.load(fd)

    senza_wrapper = SenzaWrapper(args.senza_configuration)
    for key, value in settings:
        senza_wrapper.add_parameter(key, value)

    if args.command in ['bootstrap']:
        controller = ClusterBootstrapController(base_url=args.base_url,
                                                stack_name=args.name,
                                                sharding_level=args.sharding_level,
                                                replication_factor=args.replication_level,
                                                image_version=args.image_version,
                                                oauth_token=args.token,
                                                senza_wrapper=senza_wrapper)
    elif args.command in ['deploy', 'create-new-cluster', 'delete-old-cluster', 'add-new-nodes', 'delete-old-nodes',
                          'switch']:
        controller = ClusterDeploymentController(base_url=args.base_url,
                                                 stack_name=args.name,
                                                 image_version=args.image_version,
                                                 oauth_token=args.token,
                                                 senza_wrapper=senza_wrapper)
    elif args.command in ['delete']:
        controller = ClusterDeleteController(base_url=args.base_url,
                                             stack_name=args.name,
                                             oauth_token=args.token,
                                             senza_wrapper=senza_wrapper)
    else:
        print('Unknown command')
        parser.print_help()
        return

    if args.command == 'bootstrap':
        controller.bootstrap_cluster()
    elif args.command == 'deploy':
        controller.deploy_new_version()
    elif args.command == 'delete':
        controller.delete_cluster()
    elif args.command == 'create-new-cluster':
        controller.create_cluster()
    elif args.command == 'delete-old-cluster':
        controller.delete_cluster()
    elif args.command == 'add-new-nodes':
        controller.add_new_nodes_to_cluster()
    elif args.command == 'delete-old-nodes':
        controller.delete_old_nodes_from_cluster()
    elif args.command == 'switch':
        controller.switch_traffic()
    else:
        print('Unknown command')
        parser.print_help()
        return

if __name__ == '__main__':
    main()
