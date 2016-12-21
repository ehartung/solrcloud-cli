#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os.path
import sys
import yaml

from solrcloud_cli.controllers.cluster_bootstrap_controller import ClusterBootstrapController
from solrcloud_cli.controllers.cluster_delete_controller import ClusterDeleteController
from solrcloud_cli.controllers.cluster_deployment_controller import ClusterDeploymentController
from solrcloud_cli.services.senza_deployment_service import SenzaDeploymentService
from solrcloud_cli.services.kubectl_deployment_service import KubectlDeploymentService
from solrcloud_cli.services.solr_collections_service import SolrCollectionsService

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
    parser.add_argument('-t', '--token', default='', help='OAuth token for connecting to the Solr cloud API')
    parser.add_argument('-f', '--config-file', help='Path to config file. (default: %s)' % DEFAULT_CONF_FILE,
                        dest='config')
    parser.add_argument('--region', help='AWS region in which SolrCloud should be installed')
    parser.add_argument('-d', '--deployment-mode', default='stups',
                        help='Deployment mode, supported modes are stups, k8s')
    return parser


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

    if args.deployment_mode == 'stups':
        deployment_service = SenzaDeploymentService(args.senza_configuration)
    elif args.deployment_mode == 'k8s':
        deployment_service = KubectlDeploymentService()
    else:
        print('Unknown deployment mode: [{}]. Supported modes are stups, k8s.', args.command)
        parser.print_usage()
        return

    solr_collections_service = SolrCollectionsService(base_url=settings['SolrBaseUrl'],
                                                      oauth_token=args.token,
                                                      replication_factor=args.replication_level,
                                                      sharding_level=args.sharding_level)

    if args.region:
        deployment_service.set_region(args.region)

    for key, value in settings.items():
        deployment_service.add_parameter(key, value)

    if args.command in ['bootstrap']:
        controller = ClusterBootstrapController(stack_name=settings['ApplicationId'],
                                                sharding_level=args.sharding_level,
                                                replication_factor=args.replication_level,
                                                image_version=args.image_version,
                                                solr_collections_service=solr_collections_service,
                                                deployment_service=deployment_service)
    elif args.command in ['deploy', 'create-new-cluster', 'delete-old-cluster', 'add-new-nodes', 'delete-old-nodes',
                          'switch']:
        controller = ClusterDeploymentController(stack_name=settings['ApplicationId'],
                                                 image_version=args.image_version,
                                                 solr_collections_service=solr_collections_service,
                                                 deployment_service=deployment_service)
    elif args.command in ['delete']:
        controller = ClusterDeleteController(stack_name=settings['ApplicationId'],
                                             solr_collections_service=solr_collections_service,
                                             deployment_service=deployment_service)
    else:
        print('Unknown command:', args.command)
        parser.print_usage()
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


def main():
    solrcloud_cli(sys.argv[1:])


if __name__ == '__main__':
    main()
