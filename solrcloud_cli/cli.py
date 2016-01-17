#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os.path
import sys
import yaml

from solrcloud_cli.controllers.cluster_bootstrap_controller import ClusterBootstrapController
from solrcloud_cli.controllers.cluster_delete_controller import ClusterDeleteController
from solrcloud_cli.controllers.cluster_deployment_controller import ClusterDeploymentController
from solrcloud_cli.services.senza_wrapper import SenzaWrapper

from argparse import ArgumentParser

DEFAULT_CONF_FILE = 'example.yaml'


def build_args_parser():
    parser = ArgumentParser(description='SolrCloud CLI')
    parser.add_argument('command', help='Available commands: bootstrap, deploy, delete, create-new-cluster, '
                                        'delete-old-cluster, add-new-nodes, delete-old-nodes, switch')
    parser.add_argument('-i', '--image-version', help='Docker image version of Solr cloud instances')
    parser.add_argument('-s', '--sharding-level', default=1, help='Number of shards per collection')
    parser.add_argument('-r', '--replication-level', default=3, help='Number of replications per shard')
    parser.add_argument('-c', '--senza-configuration', default='solrcloud-appliance.yaml',
                        help='Senza configuration file for Solr cluster on AWS with STUPS')
    parser.add_argument('-t', '--token', help='OAuth token for connecting to the Solr cloud API')
    parser.add_argument('-f', '--config-file', help='Path to config file. (default: %s)' % DEFAULT_CONF_FILE,
                        dest='config')
    return parser


def execute_command(controller, command):
    if not controller:
        return False

    if command == 'bootstrap':
        controller.bootstrap_cluster()
    elif command == 'deploy':
        controller.deploy_new_version()
    elif command == 'delete':
        controller.delete_cluster()
    elif command == 'create-new-cluster':
        controller.create_cluster()
    elif command == 'delete-old-cluster':
        controller.delete_cluster()
    elif command == 'add-new-nodes':
        controller.add_new_nodes_to_cluster()
    elif command == 'delete-old-nodes':
        controller.delete_old_nodes_from_cluster()
    elif command == 'switch':
        controller.switch_traffic()
    else:
        return False

    return True

def solrcloud_cli(cli_args):
    parser = build_args_parser()
    args = parser.parse_args(cli_args)

    if not args.config:
        args.config = os.path.expanduser(DEFAULT_CONF_FILE)

    if not os.path.exists(args.config):
        print('Configuration file does not exist:', args.config)
        parser.print_usage()
        return

    with open(args.config, 'rb') as fd:
        settings = yaml.load(fd)

    senza_wrapper = SenzaWrapper(args.senza_configuration)
    for key, value in settings.items():
        senza_wrapper.add_parameter(key, value)

    if args.command in ['bootstrap']:
        controller = ClusterBootstrapController(base_url=settings['SolrBaseUrl'],
                                                stack_name=settings['ApplicationId'],
                                                sharding_level=args.sharding_level,
                                                replication_factor=args.replication_level,
                                                image_version=args.image_version,
                                                oauth_token=args.token,
                                                senza_wrapper=senza_wrapper)
    elif args.command in ['deploy', 'create-new-cluster', 'delete-old-cluster', 'add-new-nodes', 'delete-old-nodes',
                          'switch']:
        controller = ClusterDeploymentController(base_url=settings['SolrBaseUrl'],
                                                 stack_name=settings['ApplicationId'],
                                                 image_version=args.image_version,
                                                 oauth_token=args.token,
                                                 senza_wrapper=senza_wrapper)
    elif args.command in ['delete']:
        controller = ClusterDeleteController(base_url=settings['SolrBaseUrl'],
                                             stack_name=settings['ApplicationId'],
                                             oauth_token=args.token,
                                             senza_wrapper=senza_wrapper)
    else:
        controller = None

    if not execute_command(controller, args.command):
        print('Unknown command:', args.command)
        parser.print_usage()
        return


def main():
    solrcloud_cli(sys.argv[1:])

if __name__ == '__main__':
    main()
