from abc import ABCMeta


class DeploymentService(metaclass=ABCMeta):

    def create_node_set(self, application: str, node_set: str, image_version: str):
        """
        Create node set for an application

        @param application: Name of application
        @param node_set: Name of the node set
        @param image_version: Docker image version
        @return:
        """
        raise(NotImplementedError("Method needs to be implemented"))

    def delete_node_set(self, application: str, node_set: str):
        """
        Delete node set of an application

        @param application: Name of application
        @param node_set: Name of node set
        @return:
        """
        raise(NotImplementedError("Method needs to be implemented"))

    def switch_traffic(self, application: str, node_set: str, weight: int):
        raise(NotImplementedError("Method needs to be implemented"))

    def get_all_node_sets(self, application: str):
        """
        Return list of node sets.
        For each node set the IP address of its nodes and the traffic weight are also included.

        Example:
        [
            {
                'name': 'blue',
                'nodes': [
                    '1.2.3.4',
                    '5.6.7.8'
                ],
                'weight': '100'
            },
            {
                'name': 'green',
                'nodes': [
                    '2.3.4.5',
                    '6.7.8.9'
                ],
                'weight': '0'
            }
        ]
        @param application: Name of application
        @return: json
        """
        raise(NotImplementedError("Method needs to be implemented"))
