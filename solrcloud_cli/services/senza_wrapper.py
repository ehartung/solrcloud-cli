#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import subprocess
import sys
import time

SENZA = 'senza'
DEFAULT_REGION = 'eu-west-1'
FIRST_STACK_VERSION = 'blue'
SECOND_STACK_VERSION = 'green'

DEFAULT_STACK_CREATION_RETRY_WAIT = 10
DEFAULT_STACK_CREATION_RETRY_TIMEOUT = 900

DEFAULT_RETRY_WAIT = 1


class SenzaWrapper:

    __config_file_name = ''
    __retry_wait = DEFAULT_RETRY_WAIT
    __stack_creation_retry_wait = DEFAULT_STACK_CREATION_RETRY_WAIT
    __stack_creation_retry_timeout = DEFAULT_STACK_CREATION_RETRY_TIMEOUT
    __region = DEFAULT_REGION

    __parameters = None

    def __init__(self, config_file_name: str):
        self.__config_file_name = config_file_name
        self.__parameters = dict()

    def set_retry_wait(self, retry_wait: int):
        self.__retry_wait = retry_wait

    def set_stack_creation_retry_wait(self, retry_wait: int):
        self.__stack_creation_retry_wait = retry_wait

    def set_stack_creation_retry_timeout(self, retry_timeout: int):
        self.__stack_creation_retry_timeout = retry_timeout

    def set_region(self, region: str):
        self.__region = region

    def add_parameter(self, key: str, value):
        if key and value:
            self.__parameters[key] = value

    def delete_stack_version(self, stack_name: str, stack_version: str):
        # Delete stack version
        logging.info("Deleting [{0}] on [{1}].".format(stack_name, stack_version))
        self.__execute_senza('delete', stack_name, stack_version)

        # Wait until deletion is complete
        delete_complete = False
        while not delete_complete:
            list_output = self.__execute_senza('list', stack_name, stack_version)
            if not list_output:
                delete_complete = True
                logging.info("[{0}] on [{1}] has been deleted.".format(stack_name, stack_version))
            time.sleep(self.__retry_wait)
            sys.stdout.write('.')
            sys.stdout.flush()

    def get_stack_instances(self, stack_name: str, stack_version: str):
        instances = self.__execute_senza('instances', stack_name, stack_version)
        return list(map(lambda x: x['private_ip'], instances))

    def get_active_stack_version(self, stack_name: str):
        active_versions = list(filter(lambda x: x['weight%'] == float(100), self.get_all_stack_versions(stack_name)))
        if active_versions:
            active_version = active_versions[0]['version']
        else:
            active_version = None
        return active_version

    def get_passive_stack_version(self, stack_name: str):
        passive_versions = list(filter(lambda x: x['weight%'] == float(0), self.get_all_stack_versions(stack_name)))
        if passive_versions:
            passive_version = passive_versions[0]['version']
        else:
            passive_version = None
        return passive_version

    def get_all_stack_versions(self, stack_name: str):
        return self.__execute_senza('traffic', stack_name)

    def create_stack(self, stack_name: str, stack_version: str, image_version: str):
        senza_parameters = list()
        senza_parameters.append('ImageVersion=' + image_version)
        for key, value in self.__parameters.items():
            senza_parameters.append(key + '=' + str(value))

        result = self.__execute_senza('create', '--disable-rollback', self.__config_file_name, stack_version,
                                      *senza_parameters)
        if result != 0:
            raise Exception('Failed to create new cluster with error code [{}]'.format(result))
        timer = 0
        while timer < self.__stack_creation_retry_timeout:
            events = sorted(self.get_events(stack_name, stack_version), key=lambda k: k['event_time'])
            if events:
                last_event = events[-1]
                if last_event['ResourceStatus'] == 'CREATE_COMPLETE' and \
                        last_event['resource_type'] == 'CloudFormation::Stack':
                    return
                elif last_event['ResourceStatus'] in ['CREATE_FAILED', 'ROLLBACK_IN_PROGRESS', 'DELETE_IN_PROGRESS',
                                                      'DELETE_COMPLETE', 'ROLLBACK_COMPLETE']:
                    raise Exception('Creation of stack [{}] version [{}] with image version [{}] failed'
                                    .format(stack_name, stack_version, image_version))

            time.sleep(self.__stack_creation_retry_wait)
            timer += self.__stack_creation_retry_wait
            sys.stdout.write('.')
            sys.stdout.flush()
        else:
            raise Exception('Timeout while creating new stack version')

    def get_events(self, stack_name: str, stack_version: str):
        return self.__execute_senza('events', stack_name, stack_version)

    def switch_traffic(self, stack_name: str, stack_version: str, weight: int):
        traffic_output = self.__execute_senza('traffic', stack_name, stack_version, str(weight))
        if traffic_output and isinstance(traffic_output, list):
            for traffic_element in traffic_output:
                if (traffic_element['stack_name'] == stack_name and traffic_element['version'] == stack_version and
                        traffic_element['new_weight%'] != weight):

                    raise Exception('Switching of [{}]% traffic to stack [{}] version [{}] failed'
                                    .format(weight, stack_name, stack_version))
                elif (traffic_element['stack_name'] == stack_name and traffic_element['version'] == stack_version and
                        traffic_element['new_weight%'] == traffic_element['old_weight%']):

                    raise Exception('Traffic weight did not change, traffic for stack [{}] version [{}] is still at '
                                    '[{}]%'.format(stack_name, stack_version, weight))
        elif traffic_output is None:
            return
        else:
            raise Exception('Unexpected output: [{}]'.format(traffic_output))

    def __execute_senza(self, command: str, *args):
        senza_command = [SENZA, command, '--region', self.__region]

        if command in ['create', 'delete']:
            senza_command += list(args)
            result = subprocess.call(senza_command)
        else:
            senza_command += ['--output', 'json']
            senza_command += list(args)
            output = subprocess.check_output(senza_command)
            if output and isinstance(output, bytes):
                result = json.loads(output.decode(encoding='utf-8'))
            else:
                result = None
        return result
