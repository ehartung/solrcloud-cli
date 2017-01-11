#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import subprocess

from mock import MagicMock
from unittest import TestCase
from solrcloud_cli.services.kubectl_deployment_service import KubectlDeploymentService


class TestKubectlDeploymentService(TestCase):

    __deployment_service = None

    def setUp(self):
        self.__deployment_service = KubectlDeploymentService()

    def test_should_return_all_instances_of_one_stack_version(self):
        get_deployments_output = {
            'items': [{'metadata': {'labels': {'release': '1'}}}, {'metadata': {'labels': {'release': '2'}}}]
        }
        get_pods_output_for_release_1 = {
            'items': [{'status': {'podIP': '1.1.1.1'}}, {'status': {'podIP': '1.1.1.2'}}]
        }
        get_pods_output_for_release_2 = {
            'items': [{'status': {'podIP': '2.1.1.1'}}, {'status': {'podIP': '2.1.1.2'}}]
        }
        side_effect_kubectl_outputs = [
            bytes(json.dumps(get_deployments_output), encoding='utf-8'),
            bytes(json.dumps(get_pods_output_for_release_1), encoding='utf-8'),
            bytes(json.dumps(get_pods_output_for_release_2), encoding='utf-8')
        ]
        kubectl_get_mock = MagicMock(side_effect=side_effect_kubectl_outputs)
        subprocess.check_output = kubectl_get_mock

        result = self.__deployment_service.get_all_node_sets('test-application')

        expected_result = [
            {'name': '1', 'nodes': ['1.1.1.1', '1.1.1.2'], 'weight': '100'},
            {'name': '2', 'nodes': ['2.1.1.1', '2.1.1.2'], 'weight': '100'}
        ]

        self.assertListEqual(expected_result, result, "Getting all node sets failed.")
        kubectl_get_mock.assert_any_call([
            'kubectl', 'get', '--namespace=diamond', '--output=json', 'deployments',
            '--selector="application=test-application"'
        ])
        kubectl_get_mock.assert_any_call([
            'kubectl', 'get', '--namespace=diamond', '--output=json', 'pods',
            '--selector="application=test-application, release=1"'
        ])
        kubectl_get_mock.assert_any_call([
            'kubectl', 'get', '--namespace=diamond', '--output=json', 'pods',
            '--selector="application=test-application, release=2"'
        ])

    def test_should_return_success_after_creating_new_node_set(self):
        get_deployments_output = {
            'items': [{'metadata': {'labels': {'release': '1'}}}, {'metadata': {'labels': {'release': '2'}}}]
        }
        kubectl_create_mock = MagicMock(return_value='deployment "test-application-2" created')
        subprocess.call = kubectl_create_mock

        kubectl_get_mock = MagicMock(return_value=bytes(json.dumps(get_deployments_output), encoding='utf-8'))
        subprocess.check_output = kubectl_get_mock

        result = self.__deployment_service.create_node_set('test-application', '2', '0.0.0')

        self.assertEquals(None, result, 'Unexpected output')

        kubectl_create_mock.assert_called_once_with(['kubectl', 'create', '--namespace=diamond', '-f',
                                                     'test-application-deployment.yaml', '--record'])
        kubectl_get_mock.assert_called_once_with(['kubectl', 'get', '--namespace=diamond', '--output=json',
                                                  'deployments', '--selector="application=test-application"'])

    def test_should_wait_until_success_event_comes_when_creating_a_new_node_set(self):
        pass

    def test_should_raise_exception_if_kubectl_execution_failed_on_creating_a_new_node_set(self):
        get_deployments_output = {
            'items': [{'metadata': {'labels': {'release': '1'}}}, {'metadata': {'labels': {'release': '2'}}}]
        }
        kubectl_create_mock = MagicMock(return_value='deployment "test-application-UNKNOWN" failed')
        subprocess.call = kubectl_create_mock

        kubectl_get_mock = MagicMock(return_value=bytes(json.dumps(get_deployments_output), encoding='utf-8'))
        subprocess.check_output = kubectl_get_mock

        with self.assertRaisesRegex(Exception, 'Failed to create new node set \[UNKNOWN\] for application \[test-application\]'):
            self.__deployment_service.create_node_set('test-application', 'UNKNOWN', '0.0.0')

        kubectl_create_mock.assert_called_once_with(['kubectl', 'create', '--namespace=diamond', '-f',
                                                     'test-application-deployment.yaml', '--record'])
        kubectl_get_mock.assert_called_once_with(['kubectl', 'get', '--namespace=diamond', '--output=json',
                                                  'deployments', '--selector="application=test-application"'])

    def test_should_raise_exception_if_creation_of_new_node_set_failed(self):
        pass

    def test_should_raise_exception_if_node_set_creation_lasts_longer_than_timeout(self):
        pass

    def test_should_create_node_set_with_additional_kubectl_parameter(self):
        pass

    def test_should_return_success_after_deleting_node_set(self):
        pass