import json
import subprocess

from solrcloud_cli.services.deployment_service import DeploymentService

KUBECTL = 'kubectl'


class KubectlDeploymentService(DeploymentService):

    def create_node_set(self, application: str, node_set: str, image_version: str):
        return self.__execute_kubectl('create', '-f', application + '-deployment.yaml', '--record')

    def delete_node_set(self, application: str, node_set: str):
        return self.__execute_kubectl('delete', 'deployment', application + '-' + node_set)

    def get_all_node_sets(self, application: str):
        releases = map(lambda x: x['metadata']['labels']['release'],
                       self.__execute_kubectl('get', 'deployments', '--selector="application=' + application + '"')
                       .get('items'))

        node_sets = list()
        for release in releases:
            node_set = dict()
            node_set['name'] = release
            node_set['nodes'] = list(map(lambda x: x['status']['podIP'],
                                         self.__execute_kubectl('get', 'pods', '--selector="application=' +
                                                                application + ', release=' + release + '"')
                                         .get('items')))
            node_set['weight'] = '100'
            node_sets.append(node_set)

        return node_sets

    def switch_traffic(self, application: str, node_set: str, weight: int):
        # nothing to do here
        pass

    @staticmethod
    def __execute_kubectl(command: str, *args):
        kubectl_command = [KUBECTL, command, '--namespace=diamond']

        if command in ['get', 'delete']:
            kubectl_command += ['--output', 'json']
            kubectl_command += list(args)
            output = subprocess.check_output(kubectl_command)
            if output and isinstance(output, bytes):
                result = json.loads(output.decode(encoding='utf-8'))
            else:
                result = None
        else:
            kubectl_command += list(args)
            result = subprocess.call(kubectl_command)
        return result
