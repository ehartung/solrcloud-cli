#!/usr/bin/env python
# -*- coding: utf-8 -*-
from unittest import TestCase
from solrcloud_cli.services.deployment_service import DeploymentService


class TestDeploymentService(TestCase):

    __deployment_service = None

    def setUp(self):
        self.__deployment_service = DeploymentService()

    def test_should_raise_not_implemented_exception_whe_required_method_is_not_implemented(self):
        with self.assertRaisesRegex(Exception, 'Method needs to be implemented'):
            self.__deployment_service.create_node_set('', '', '')

        with self.assertRaisesRegex(Exception, 'Method needs to be implemented'):
            self.__deployment_service.delete_node_set('', '')

        with self.assertRaisesRegex(Exception, 'Method needs to be implemented'):
            self.__deployment_service.switch_traffic('', '', 0)

        with self.assertRaisesRegex(Exception, 'Method needs to be implemented'):
            self.__deployment_service.get_all_node_sets('')

