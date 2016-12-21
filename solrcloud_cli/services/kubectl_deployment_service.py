import json
import subprocess

from solrcloud_cli.services.deployment_service import DeploymentService

KUBECTL = 'kubectl'
DEFAULT_REGION = 'eu-west-1'


class KubectlDeploymentService(DeploymentService):

    __region = DEFAULT_REGION

    def delete_node_set(self, name: str, version: str):
        pass

    def get_nodes_of_node_set(self, name: str, version: str):
        pass

    def get_active_node_set(self, name: str):
        pass

    def get_passive_node_set(self, name: str):
        pass

    def get_all_node_sets(self, name: str):
        pass

    def create_node_set(self, name: str, version: str, image_version: str):
        pass

    def get_events(self, name: str, version: str):
        pass

    def switch_traffic(self, name: str, version: str, weight: int):
        pass

    @staticmethod
    def __execute_kubectl(command: str, *args):
        kubectl_command = [KUBECTL, command]

        if command in ['create', 'delete']:
            kubectl_command += list(args)
            if command == 'create':
                kubectl_command += ['--record']
            result = subprocess.call(kubectl_command)
        else:
            kubectl_command += ['--output', 'json']
            kubectl_command += list(args)
            output = subprocess.check_output(kubectl_command)
            if output and isinstance(output, bytes):
                result = json.loads(output.decode(encoding='utf-8'))
            else:
                result = None
        return result
