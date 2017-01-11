import io
import os.path
import yaml

from mock import patch, Mock
from unittest import TestCase

from solrcloud_cli.controllers.cluster_delete_controller import ClusterDeleteController

from solrcloud_cli.controllers.cluster_deployment_controller import ClusterDeploymentController

from solrcloud_cli.controllers.cluster_bootstrap_controller import ClusterBootstrapController

from solrcloud_cli.cli import solrcloud_cli


class TestCLI(TestCase):

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_should_return_help_page(self, out):
        with self.assertRaises(SystemExit) as ex:
            solrcloud_cli(['--help'])
        output = out.getvalue()

        self.assertEqual(ex.exception.code, 0)
        self.assertIn('SolrCloud CLI', output)
        self.assertIn('positional arguments:', output)
        self.assertIn('optional arguments:', output)

    def test_should_return_error_if_no_argument_given(self):
        with self.assertRaises(SystemExit) as ex:
            solrcloud_cli([])
        self.assertEqual(ex.exception.code, 2)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_should_return_error_message_and_usage_page_if_command_is_unknown(self, out):
        solrcloud_cli(['unknown'])
        output = out.getvalue()

        self.assertIn('Unknown command: unknown', output)
        self.assertIn('usage: ', output)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_should_return_error_message_and_usage_page_if_config_file_does_not_exist(self, out):
        solrcloud_cli(['-f', 'unknown.file', 'unknown'])
        output = out.getvalue()

        self.assertIn('Configuration file does not exist: unknown.file', output)
        self.assertIn('usage: ', output)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_should_return_error_message_and_usage_page_if_deployment_method_is_unknown(self, out):
        true_mock = Mock(return_value=True)
        os.path.exists = true_mock
        yaml_mock = Mock(return_value={})
        yaml.load = yaml_mock

        solrcloud_cli(['-f', '/dev/null', '-d', 'unknown.deployment.method', 'unknown'])
        output = out.getvalue()

        self.assertIn('Unknown deployment mode: [unknown.deployment.method]. Supported modes are stups, k8s.', output)
        self.assertIn('usage: ', output)

    @patch('solrcloud_cli.controllers.cluster_bootstrap_controller.ClusterBootstrapController.__init__',
           Mock(return_value=None))
    @patch.object(ClusterBootstrapController, 'bootstrap_cluster')
    def test_should_execute_bootstrap_command(self, mock_method):
        solrcloud_cli(['bootstrap'])
        mock_method.assert_called_once_with()

    @patch('solrcloud_cli.controllers.cluster_deployment_controller.ClusterDeploymentController.__init__',
           Mock(return_value=None))
    @patch.object(ClusterDeploymentController, 'deploy_new_version')
    def test_should_execute_deploy_command(self, mock_method):
        solrcloud_cli(['deploy'])
        mock_method.assert_called_once_with()

    @patch('solrcloud_cli.controllers.cluster_deployment_controller.ClusterDeploymentController.__init__',
           Mock(return_value=None))
    @patch.object(ClusterDeploymentController, 'create_cluster')
    def test_should_execute_create_new_cluster_command(self, mock_method):
        solrcloud_cli(['create-new-cluster'])
        mock_method.assert_called_once_with()

    @patch('solrcloud_cli.controllers.cluster_deployment_controller.ClusterDeploymentController.__init__',
           Mock(return_value=None))
    @patch.object(ClusterDeploymentController, 'delete_cluster')
    def test_should_execute_delete_old_cluster_command(self, mock_method):
        solrcloud_cli(['delete-old-cluster'])
        mock_method.assert_called_once_with()

    @patch('solrcloud_cli.controllers.cluster_deployment_controller.ClusterDeploymentController.__init__',
           Mock(return_value=None))
    @patch.object(ClusterDeploymentController, 'add_new_nodes_to_cluster')
    def test_should_execute_add_new_nodes_command(self, mock_method):
        solrcloud_cli(['add-new-nodes'])
        mock_method.assert_called_once_with()

    @patch('solrcloud_cli.controllers.cluster_deployment_controller.ClusterDeploymentController.__init__',
           Mock(return_value=None))
    @patch.object(ClusterDeploymentController, 'delete_old_nodes_from_cluster')
    def test_should_execute_delete_old_nodes_command(self, mock_method):
        solrcloud_cli(['delete-old-nodes'])
        mock_method.assert_called_once_with()

    @patch('solrcloud_cli.controllers.cluster_deployment_controller.ClusterDeploymentController.__init__',
           Mock(return_value=None))
    @patch.object(ClusterDeploymentController, 'switch_traffic')
    def test_should_execute_switch_command(self, mock_method):
        solrcloud_cli(['switch'])
        mock_method.assert_called_once_with()

    @patch('solrcloud_cli.controllers.cluster_delete_controller.ClusterDeleteController.__init__',
           Mock(return_value=None))
    @patch.object(ClusterDeleteController, 'delete_cluster')
    def test_should_execute_delete_command(self, mock_method):
        solrcloud_cli(['delete'])
        mock_method.assert_called_once_with()
