#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import subprocess

from mock import MagicMock
from unittest import TestCase
from solrcloud_cli.services.senza_wrapper import SenzaWrapper

NO_TRAFFIC = 0.0
ALL_TRAFFIC = 100.0

TEST_CONFIG = 'test.yaml'


class TestSenzaWrapper(TestCase):

    __senza_wrapper = None

    def setup_method(self, method):
        self.__senza_wrapper = SenzaWrapper(TEST_CONFIG)
        self.__senza_wrapper.set_retry_wait(0)
        self.__senza_wrapper.set_stack_creation_retry_timeout(1)
        self.__senza_wrapper.set_stack_creation_retry_wait(0)

    def test_should_return_success_when_deleting_stack_version_with_one_retry(self):
        delete_mock = MagicMock(return_value=0)

        list_output_side_effects = [
            bytes(json.dumps({'output': 'test'}), encoding='utf-8'),
            None
        ]
        list_mock = MagicMock(side_effect=list_output_side_effects)

        subprocess.call = delete_mock
        subprocess.check_output = list_mock

        self.__senza_wrapper.delete_stack_version('test', 'test')

        delete_mock.assert_called_once_with(['senza', 'delete', '--region', 'eu-west-1', 'test', 'test'])
        list_mock.assert_called_with(['senza', 'list', '--region', 'eu-west-1', '--output', 'json', 'test', 'test'])
        self.assertEquals(2, len(list_mock.call_args_list), 'Unexpected number of senza list calls')

    def test_should_return_all_instances_of_one_stack_version(self):
        instances = [
            {'stack_name': 'test-stack', 'stack_version': 'test-version', 'private_ip': '0.0.0.0'},
            {'stack_name': 'test-stack', 'stack_version': 'test-version', 'private_ip': '1.1.1.1'}
        ]
        instances_mock = MagicMock(return_value=bytes(json.dumps(instances), encoding='utf-8'))
        subprocess.check_output = instances_mock

        result = self.__senza_wrapper.get_stack_instances('test-stack', 'test-version')
        self.assertListEqual(['0.0.0.0', '1.1.1.1'], result, "Getting stack instances failed.")
        instances_mock.assert_called_once_with([
            'senza', 'instances', '--region', 'eu-west-1', '--output', 'json', 'test-stack', 'test-version'
        ])

    def test_should_return_active_stack_version(self):
        active_version = 'active'
        passive_version = 'passive'
        stack_versions = [
            {
                'identifier': 'test-' + passive_version,
                'stack_name': 'test',
                'version': passive_version,
                'weight%': NO_TRAFFIC
            },
            {
                'identifier': 'test-' + active_version,
                'stack_name': 'test',
                'version': active_version,
                'weight%': ALL_TRAFFIC}
        ]
        versions_mock = MagicMock(return_value=bytes(json.dumps(stack_versions), encoding='utf-8'))
        subprocess.check_output = versions_mock

        result = self.__senza_wrapper.get_active_stack_version('test')
        self.assertEquals(active_version, result, 'Result is not the active stack version')
        versions_mock.assert_called_once_with([
            'senza', 'traffic', '--region', 'eu-west-1', '--output', 'json', 'test'
        ])

    def test_should_return_active_stack_version_when_only_one_version_exists(self):
        active_version = 'active'
        stack_versions = [
            {
                'identifier': 'test-' + active_version,
                'stack_name': 'test',
                'version': active_version,
                'weight%': ALL_TRAFFIC
            }
        ]
        versions_mock = MagicMock(return_value=bytes(json.dumps(stack_versions), encoding='utf-8'))
        subprocess.check_output = versions_mock

        result = self.__senza_wrapper.get_active_stack_version('test')
        self.assertEquals(active_version, result, 'Result is not the active stack version')
        versions_mock.assert_called_once_with([
            'senza', 'traffic', '--region', 'eu-west-1', '--output', 'json', 'test'
        ])

    def test_should_return_none_if_no_active_version_exists(self):
        passive_version = 'passive'
        stack_versions = [
            {'identifier': 'test-' + passive_version, 'stack_name': 'test', 'version': passive_version, 'weight%': 0.0}
        ]
        versions_mock = MagicMock(return_value=bytes(json.dumps(stack_versions), encoding='utf-8'))
        subprocess.check_output = versions_mock

        result = self.__senza_wrapper.get_active_stack_version('test')
        self.assertIsNone(result, 'Active stack version returned although there is none')
        versions_mock.assert_called_once_with([
            'senza', 'traffic', '--region', 'eu-west-1', '--output', 'json', 'test'
        ])

    def test_should_return_passive_stack_version(self):
        active_version = 'active'
        passive_version = 'passive'
        stack_versions = [
            {
                'identifier': 'test-' + passive_version,
                'stack_name': 'test',
                'version': passive_version,
                'weight%': NO_TRAFFIC
            },
            {
                'identifier': 'test-' + active_version,
                'stack_name': 'test',
                'version': active_version,
                'weight%': ALL_TRAFFIC
            }
        ]
        versions_mock = MagicMock(return_value=bytes(json.dumps(stack_versions), encoding='utf-8'))
        subprocess.check_output = versions_mock

        result = self.__senza_wrapper.get_passive_stack_version('test')
        self.assertEquals(passive_version, result, 'Result is not the passive stack version')
        versions_mock.assert_called_once_with([
            'senza', 'traffic', '--region', 'eu-west-1', '--output', 'json', 'test'
        ])

    def test_should_return_passive_stack_version_when_only_one_version_exists(self):
        passive_version = 'passive'
        stack_versions = [
            {
                'identifier': 'test-' + passive_version,
                'stack_name': 'test',
                'version': passive_version,
                'weight%': NO_TRAFFIC
            }
        ]
        versions_mock = MagicMock(return_value=bytes(json.dumps(stack_versions), encoding='utf-8'))
        subprocess.check_output = versions_mock

        result = self.__senza_wrapper.get_passive_stack_version('test')
        self.assertEquals(passive_version, result, 'Result is not the passive stack version')
        versions_mock.assert_called_once_with([
            'senza', 'traffic', '--region', 'eu-west-1', '--output', 'json', 'test'
        ])

    def test_should_return_none_if_no_passive_version_exists(self):
        active_version = 'active'
        stack_versions = [
            {
                'identifier': 'test-' + active_version,
                'stack_name': 'test',
                'version': active_version,
                'weight%': ALL_TRAFFIC
            }
        ]
        versions_mock = MagicMock(return_value=bytes(json.dumps(stack_versions), encoding='utf-8'))
        subprocess.check_output = versions_mock

        result = self.__senza_wrapper.get_passive_stack_version('test')
        self.assertIsNone(result, 'Passive stack version returned although there is none')
        versions_mock.assert_called_once_with([
            'senza', 'traffic', '--region', 'eu-west-1', '--output', 'json', 'test'
        ])

    def test_should_return_all_events_for_stack_version(self):
        stack_name = 'test-stack'
        stack_version_name = 'test-version'

        events = [
            {'stack_name': stack_name, 'version': stack_version_name, 'resource_type': 'test-event1'},
            {'stack_name': stack_name, 'version': stack_version_name, 'resource_type': 'test-event2'}
        ]
        events_mock = MagicMock(return_value=bytes(json.dumps(events), encoding='utf-8'))
        subprocess.check_output = events_mock

        result = self.__senza_wrapper.get_events(stack_name, stack_version_name)
        self.assertListEqual(events, result, 'Received unexpected list of events')
        events_mock.assert_called_once_with([
            'senza', 'events', '--region', 'eu-west-1', '--output', 'json', stack_name, stack_version_name
        ])

    def test_should_switch_traffic_between_versions(self):
        stack_name = 'test'
        active_version = 'active'
        passive_version = 'passive'
        switch_result = [
            {
                'identifier': stack_name + '-' + passive_version,
                'stack_name': stack_name,
                'version': passive_version,
                'old_weight%': NO_TRAFFIC,
                'new_weight%': ALL_TRAFFIC
            },
            {
                'identifier': stack_name + '-' + active_version,
                'stack_name': stack_name,
                'version': active_version,
                'old_weight%': ALL_TRAFFIC,
                'new_weight%': NO_TRAFFIC
            }
        ]
        switch_mock = MagicMock(return_value=bytes(json.dumps(switch_result), encoding='utf-8'))
        subprocess.check_output = switch_mock

        self.__senza_wrapper.switch_traffic(stack_name, passive_version, int(ALL_TRAFFIC))
        switch_mock.assert_called_once_with([
            'senza', 'traffic', '--region', 'eu-west-1', '--output', 'json', stack_name, passive_version,
            str(int(ALL_TRAFFIC))
        ])

    def test_should_raise_exception_if_new_weight_equals_old_weight_after_switching_traffic_between_versions(self):
        stack_name = 'test'
        active_version = 'active'
        passive_version = 'passive'
        switch_result = [
            {
                'identifier': stack_name + '-' + passive_version,
                'stack_name': stack_name,
                'version': passive_version,
                'old_weight%': NO_TRAFFIC,
                'new_weight%': NO_TRAFFIC
            },
            {
                'identifier': stack_name + '-' + active_version,
                'stack_name': stack_name,
                'version': active_version,
                'old_weight%': ALL_TRAFFIC,
                'new_weight%': ALL_TRAFFIC
            }
        ]
        switch_mock = MagicMock(return_value=bytes(json.dumps(switch_result), encoding='utf-8'))
        subprocess.check_output = switch_mock

        with self.assertRaisesRegex(Exception, 'Switching of \[{}\]% traffic to stack \[{}\] version \[{}\] failed'
                                               .format('100', stack_name, passive_version)):
            self.__senza_wrapper.switch_traffic(stack_name, passive_version, int(ALL_TRAFFIC))
        switch_mock.assert_called_once_with([
            'senza', 'traffic', '--region', 'eu-west-1', '--output', 'json', stack_name, passive_version,
            str(int(ALL_TRAFFIC))
        ])

    def test_should_raise_exception_if_weight_was_already_new_weight_before_switching_traffic_between_versions(self):
        stack_name = 'test'
        active_version = 'active'
        passive_version = 'passive'
        switch_result = [
            {
                'identifier': stack_name + '-' + passive_version,
                'stack_name': stack_name,
                'version': passive_version,
                'old_weight%': ALL_TRAFFIC,
                'new_weight%': ALL_TRAFFIC
            },
            {
                'identifier': stack_name + '-' + active_version,
                'stack_name': stack_name,
                'version': active_version,
                'old_weight%': NO_TRAFFIC,
                'new_weight%': NO_TRAFFIC
            }
        ]
        switch_mock = MagicMock(return_value=bytes(json.dumps(switch_result), encoding='utf-8'))
        subprocess.check_output = switch_mock

        with self.assertRaisesRegex(Exception, 'Traffic weight did not change, traffic for stack \[{}\] version \[{}\] '
                                               'is still at \[{}\]%'.format(stack_name, passive_version, '100')):
            self.__senza_wrapper.switch_traffic(stack_name, passive_version, int(ALL_TRAFFIC))
        switch_mock.assert_called_once_with([
            'senza', 'traffic', '--region', 'eu-west-1', '--output', 'json', stack_name, passive_version,
            str(int(ALL_TRAFFIC))
        ])

    def test_should_raise_exception_if_new_weight_is_unexpected_after_switching_traffic_between_versions(self):
        stack_name = 'test'
        active_version = 'active'
        passive_version = 'passive'
        switch_result = [
            {
                'identifier': stack_name + '-' + passive_version,
                'stack_name': stack_name,
                'version': passive_version,
                'old_weight%': NO_TRAFFIC,
                'new_weight%': ALL_TRAFFIC - 1
            },
            {
                'identifier': stack_name + '-' + active_version,
                'stack_name': stack_name,
                'version': active_version,
                'old_weight%': ALL_TRAFFIC,
                'new_weight%': NO_TRAFFIC + 1
            }
        ]
        switch_mock = MagicMock(return_value=bytes(json.dumps(switch_result), encoding='utf-8'))
        subprocess.check_output = switch_mock

        with self.assertRaisesRegex(Exception, 'Switching of \[{}\]% traffic to stack \[{}\] version \[{}\] failed'
                                               .format('100', stack_name, passive_version)):
            self.__senza_wrapper.switch_traffic(stack_name, passive_version, int(ALL_TRAFFIC))
        switch_mock.assert_called_once_with([
            'senza', 'traffic', '--region', 'eu-west-1', '--output', 'json', stack_name, passive_version,
            str(int(ALL_TRAFFIC))
        ])

    def test_should_succeed_if_switching_traffic_between_versions_returns_no_output(self):
        stack_name = 'test'
        passive_version = 'passive'
        switch_mock = MagicMock(return_value=None)
        subprocess.check_output = switch_mock

        self.__senza_wrapper.switch_traffic(stack_name, passive_version, int(ALL_TRAFFIC))

        switch_mock.assert_called_once_with([
            'senza', 'traffic', '--region', 'eu-west-1', '--output', 'json', stack_name, passive_version,
            str(int(ALL_TRAFFIC))
        ])

    def test_should_raise_exception_if_switching_traffic_between_versions_returns_error_code(self):
        stack_name = 'test'
        version = 'unknown'
        switch_mock = MagicMock(side_effect=subprocess.CalledProcessError(cmd='test', returncode=2))
        subprocess.check_output = switch_mock

        with self.assertRaises(subprocess.CalledProcessError):
            self.__senza_wrapper.switch_traffic(stack_name, version, int(ALL_TRAFFIC))

        switch_mock.assert_called_once_with([
            'senza', 'traffic', '--region', 'eu-west-1', '--output', 'json', stack_name, version,
            str(int(ALL_TRAFFIC))
        ])

    def test_should_raise_exception_if_switching_traffic_between_versions_returns_no_list(self):
        stack_name = 'test'
        version = 'unknown'
        switch_result = 'test output'
        switch_mock = MagicMock(return_value=bytes(json.dumps(switch_result), encoding='utf-8'))
        subprocess.check_output = switch_mock

        with self.assertRaisesRegex(Exception, 'Unexpected output: \[{}\]'.format(switch_result)):
            self.__senza_wrapper.switch_traffic(stack_name, version, int(ALL_TRAFFIC))

        switch_mock.assert_called_once_with([
            'senza', 'traffic', '--region', 'eu-west-1', '--output', 'json', stack_name, version,
            str(int(ALL_TRAFFIC))
        ])

    def test_should_create_new_stack_version(self):
        stack_name = 'test-stack'
        stack_version = 'test-version'
        image_version = '0.0.0'

        create_mock = MagicMock(return_value=0)
        subprocess.call = create_mock

        events = [
            {
                'stack_name': stack_name,
                'version': stack_version,
                'resource_type': 'CloudFormation::Stack',
                'event_time': '0',
                'ResourceStatus': 'CREATE_COMPLETE'
            }
        ]
        events_mock = MagicMock(return_value=bytes(json.dumps(events), encoding='utf-8'))
        subprocess.check_output = events_mock

        self.__senza_wrapper.create_stack(stack_name, stack_version, image_version)

        create_mock.assert_called_once_with([
            'senza', 'create', '--region', 'eu-west-1', '--disable-rollback', TEST_CONFIG, stack_version,
            'ImageVersion=' + image_version
        ])
        events_mock.assert_called_once_with([
            'senza', 'events', '--region', 'eu-west-1', '--output', 'json', stack_name, stack_version
        ])

    def test_should_wait_until_success_event_comes_when_creating_a_new_stack_version(self):
        stack_name = 'test-stack'
        stack_version = 'test-version'
        image_version = '0.0.0'

        create_mock = MagicMock(return_value=0)
        subprocess.call = create_mock

        success_event = {
            'stack_name': stack_name,
            'version': stack_version,
            'resource_type': 'CloudFormation::Stack',
            'event_time': '1',
            'ResourceStatus': 'CREATE_COMPLETE'
        }

        other_event = {
            'stack_name': stack_name,
            'version': stack_version,
            'resource_type': 'Other',
            'event_time': '0',
            'ResourceStatus': 'Other'
        }

        side_effect_events = [
            bytes(json.dumps([other_event]), encoding='utf-8'),
            bytes(json.dumps([other_event, success_event]), encoding='utf-8'),
        ]
        events_mock = MagicMock(side_effect=side_effect_events)
        subprocess.check_output = events_mock

        self.__senza_wrapper.create_stack(stack_name, stack_version, image_version)

        create_mock.assert_called_once_with([
            'senza', 'create', '--region', 'eu-west-1', '--disable-rollback', TEST_CONFIG, stack_version,
            'ImageVersion=' + image_version
        ])
        events_mock.assert_called_with([
            'senza', 'events', '--region', 'eu-west-1', '--output', 'json', stack_name, stack_version
        ])
        self.assertEquals(2, len(events_mock.call_args_list), 'Unexpected number of calls for senza events')

    def test_should_raise_exception_if_senza_execution_failed_on_creating_a_new_stack_version(self):
        stack_name = 'test-stack'
        stack_version = 'test-version'
        image_version = '0.0.0'
        error_code = 1

        create_mock = MagicMock(return_value=error_code)
        subprocess.call = create_mock

        with self.assertRaisesRegex(Exception, 'Failed to create new cluster with error code \[{}\]'
                                               .format(str(error_code))):

            self.__senza_wrapper.create_stack(stack_name, stack_version, image_version)

        create_mock.assert_called_once_with([
            'senza', 'create', '--region', 'eu-west-1', '--disable-rollback', TEST_CONFIG, stack_version,
            'ImageVersion=' + image_version
        ])

    def test_should_raise_exception_if_creation_of_new_stack_version_failed(self):
        stack_name = 'test-stack'
        stack_version = 'test-version'
        image_version = '0.0.0'

        create_mock = MagicMock(return_value=0)
        subprocess.call = create_mock

        events = [
            {
                'stack_name': stack_name,
                'version': stack_version,
                'resource_type': 'CloudFormation::Stack',
                'event_time': '0',
                'ResourceStatus': 'CREATE_FAILED'
            }
        ]
        events_mock = MagicMock(return_value=bytes(json.dumps(events), encoding='utf-8'))
        subprocess.check_output = events_mock

        with self.assertRaisesRegex(Exception, 'Creation of stack \[{}\] version \[{}\] with image version \[{}\] '
                                               'failed'.format(stack_name, stack_version, image_version)):

            self.__senza_wrapper.create_stack(stack_name, stack_version, image_version)

        create_mock.assert_called_once_with([
            'senza', 'create', '--region', 'eu-west-1', '--disable-rollback', TEST_CONFIG, stack_version,
            'ImageVersion=' + image_version
        ])
        events_mock.assert_called_once_with([
            'senza', 'events', '--region', 'eu-west-1', '--output', 'json', stack_name, stack_version
        ])

    def test_should_raise_exception_if_stack_creation_lasts_longer_than_timeout(self):
        stack_name = 'test-stack'
        stack_version = 'test-version'
        image_version = '0.0.0'
        timeout = 0

        senza_wrapper = SenzaWrapper(TEST_CONFIG)
        senza_wrapper.set_stack_creation_retry_timeout(timeout)

        create_mock = MagicMock(return_value=0)
        subprocess.call = create_mock

        events_mock = MagicMock()
        subprocess.check_output = events_mock

        with self.assertRaisesRegex(Exception, 'Timeout while creating new stack version'):
            senza_wrapper.create_stack(stack_name, stack_version, image_version)

        create_mock.assert_called_once_with([
            'senza', 'create', '--region', 'eu-west-1', '--disable-rollback', TEST_CONFIG, stack_version,
            'ImageVersion=' + image_version
        ])

        events_mock.assert_not_called()

    def test_should_create_stack_with_additional_senza_parameter(self):
        stack_name = 'test-stack'
        stack_version = 'test-version'
        image_version = '0.0.0'
        timeout = 1

        senza_wrapper = SenzaWrapper(TEST_CONFIG)
        senza_wrapper.set_stack_creation_retry_timeout(timeout)

        senza_wrapper.add_parameter("test-key", "test-value")

        create_mock = MagicMock(return_value=0)
        subprocess.call = create_mock

        events = [
            {
                'stack_name': stack_name,
                'version': stack_version,
                'resource_type': 'CloudFormation::Stack',
                'event_time': '0',
                'ResourceStatus': 'CREATE_COMPLETE'
            }
        ]
        events_mock = MagicMock(return_value=bytes(json.dumps(events), encoding='utf-8'))
        subprocess.check_output = events_mock

        senza_wrapper.create_stack(stack_name, stack_version, image_version)

        create_mock.assert_called_once_with([
            'senza', 'create', '--region', 'eu-west-1', '--disable-rollback', TEST_CONFIG, stack_version,
            'ImageVersion=' + image_version, 'test-key=test-value'
        ])
        events_mock.assert_called_once_with([
            'senza', 'events', '--region', 'eu-west-1', '--output', 'json', stack_name, stack_version
        ])
