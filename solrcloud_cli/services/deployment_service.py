from abc import ABCMeta


class DeploymentService(metaclass=ABCMeta):

    def delete_node_set(self, name: str, version: str):
        raise(NotImplementedError("Method needs to be implemented"))

    def get_nodes_of_node_set(self, name: str, version: str):
        raise(NotImplementedError("Method needs to be implemented"))

    def get_active_node_set(self, name: str):
        raise(NotImplementedError("Method needs to be implemented"))

    def get_passive_node_set(self, name: str):
        raise(NotImplementedError("Method needs to be implemented"))

    def get_all_node_sets(self, name: str):
        raise(NotImplementedError("Method needs to be implemented"))

    def create_node_set(self, name: str, version: str, image_version: str):
        raise(NotImplementedError("Method needs to be implemented"))

    def get_events(self, name: str, version: str):
        raise(NotImplementedError("Method needs to be implemented"))

    def switch_traffic(self, name: str, version: str, weight: int):
        raise(NotImplementedError("Method needs to be implemented"))
