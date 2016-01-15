import io

from mock import patch
from unittest import TestCase

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
        solrcloud_cli(['test-name', 'unknown'])
        output = out.getvalue()

        self.assertIn('Unknown command: unknown', output)
        self.assertIn('usage: ', output)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_should_return_error_message_and_usage_page_if_config_file_does_not_exist(self, out):
        solrcloud_cli(['-f', 'unknown.file', 'test-name', 'unknown'])
        output = out.getvalue()

        self.assertIn('Configuration file does not exist: unknown.file', output)
        self.assertIn('usage: ', output)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_should_run_bootstrapping_of_cluster(self, out):
        solrcloud_cli(['test-name', 'bootstrap'])
        output = out.getvalue()

        self.assertIn('Configuration file does not exist: unknown.file', output)
        self.assertIn('usage: ', output)
