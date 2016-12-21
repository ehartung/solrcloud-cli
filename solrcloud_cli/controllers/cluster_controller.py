from abc import ABCMeta


class ClusterController(metaclass=ABCMeta):

    _api_url = ''
    _deployment_service = None
    _stack_name = ''
    _oauth_token = ''
    _solr_collections_service = None

    def set_deployment_service(self, deployment_service):
        self._deployment_service = deployment_service

    def set_solr_collections_service(self, solr_collections_service):
        self._solr_collections_service = solr_collections_service
