from abc import ABCMeta


class DeploymentService(metaclass=ABCMeta):

    def delete_stack_version(self, stack_name: str, stack_version: str):
        raise(NotImplementedError("Method needs to be implemented"))

    def get_stack_instances(self, stack_name: str, stack_version: str):
        raise(NotImplementedError("Method needs to be implemented"))

    def get_active_stack_version(self, stack_name: str):
        raise(NotImplementedError("Method needs to be implemented"))

    def get_passive_stack_version(self, stack_name: str):
        raise(NotImplementedError("Method needs to be implemented"))

    def get_all_stack_versions(self, stack_name: str):
        raise(NotImplementedError("Method needs to be implemented"))

    def create_stack(self, stack_name: str, stack_version: str, image_version: str):
        raise(NotImplementedError("Method needs to be implemented"))

    def get_events(self, stack_name: str, stack_version: str):
        raise(NotImplementedError("Method needs to be implemented"))

    def switch_traffic(self, stack_name: str, stack_version: str, weight: int):
        raise(NotImplementedError("Method needs to be implemented"))
