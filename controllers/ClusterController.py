import json
import urllib.request

from abc import ABCMeta


class ClusterController(metaclass=ABCMeta):

    _api_url = ''
    _senza = None
    _stack_name = ''
    _oauth_token = ''

    def set_senza_wrapper(self, senza_wrapper):
        self._senza = senza_wrapper

    def get_cluster_state(self):
        url = self._api_url + '?action=CLUSTERSTATUS&wt=json'
        try:
            headers = dict()
            headers['Authorization'] = 'Bearer ' + self._oauth_token
            request = urllib.request.Request(url, headers=headers)
            response = urllib.request.urlopen(request)
            code = response.getcode()
            content = response.readall().decode('utf-8')
            response.close()
            if code != 200:
                raise Exception('Received unexpected status code from Solr: [{}]'.format(code))
            return json.loads(content)
        except Exception as e:
            raise Exception('Failed sending request to Solr [{}]: {}'.format(url, e))
