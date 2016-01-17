import io

from mock import patch, MagicMock, Mock
from unittest import TestCase

from solrcloud_cli.controllers.cluster_delete_controller import ClusterDeleteController

from solrcloud_cli.controllers.cluster_deployment_controller import ClusterDeploymentController

from solrcloud_cli.controllers.cluster_bootstrap_controller import ClusterBootstrapController

from solrcloud_cli.cli import solrcloud_cli, execute_command


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

    def test_should_execute_bootstrap_command(self):
        mock_controller = MagicMock(spec=ClusterBootstrapController)
        mock_method = mock_controller.bootstrap_cluster = MagicMock()
        execute_command(mock_controller, 'bootstrap')
        mock_method.assert_called_once_with()

    def test_should_execute_deploy_command(self):
        mock_controller = MagicMock(spec=ClusterDeploymentController)
        mock_method = mock_controller.deploy_new_version = MagicMock()
        execute_command(mock_controller, 'deploy')
        mock_method.assert_called_once_with()

    def test_should_execute_create_new_cluster_command(self):
        mock_controller = MagicMock(spec=ClusterDeploymentController)
        mock_method = mock_controller.create_cluster = MagicMock()
        execute_command(mock_controller, 'create-new-cluster')
        mock_method.assert_called_once_with()

    def test_should_execute_delete_old_cluster_command(self):
        mock_controller = MagicMock(spec=ClusterDeploymentController)
        mock_method = mock_controller.delete_cluster = MagicMock()
        execute_command(mock_controller, 'delete-old-cluster')
        mock_method.assert_called_once_with()

    def test_should_execute_add_new_nodes_command(self):
        mock_controller = MagicMock(spec=ClusterDeploymentController)
        mock_method = mock_controller.add_new_nodes_to_cluster = MagicMock()
        execute_command(mock_controller, 'add-new-nodes')
        mock_method.assert_called_once_with()

    def test_should_execute_delete_old_nodes_command(self):
        mock_controller = MagicMock(spec=ClusterDeploymentController)
        mock_method = mock_controller.delete_old_nodes_from_cluster = MagicMock()
        execute_command(mock_controller, 'delete-old-nodes')
        mock_method.assert_called_once_with()

    def test_should_execute_switch_command(self):
        mock_controller = MagicMock(spec=ClusterDeploymentController)
        mock_method = mock_controller.switch_traffic = MagicMock()
        execute_command(mock_controller, 'switch')
        mock_method.assert_called_once_with()

    def test_should_execute_delete_command(self):
        mock_controller = MagicMock(spec=ClusterDeleteController)
        mock_method = mock_controller.delete_cluster = MagicMock()
        execute_command(mock_controller, 'delete')
        mock_method.assert_called_once_with()
