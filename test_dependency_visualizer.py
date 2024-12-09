import unittest
from unittest.mock import patch, mock_open, MagicMock
from dependency_visualizer import DependencyVisualizer
import os

class TestDependencyVisualizer(unittest.TestCase):
    def setUp(self):
        # Создаем тестовые данные
        self.mock_config = {
            'Paths': {
                'GraphvizPath': '/usr/bin/dot',
                'RepoPath': '/test/repo',
                'OutputPath': '/test/output/graph.dot',
            },
            'Settings': {
                'TargetFile': 'test_file.py',
            }
        }
        self.config_path = 'config.ini'

    @patch('os.chdir')
    def test_change_directory_success(self, mock_chdir):
        visualizer = DependencyVisualizer(self.config_path)
        visualizer.config = self.mock_config['Paths'] | {'target_file': self.mock_config['Settings']['TargetFile']}
        try:
            visualizer.get_commit_dependencies()
            mock_chdir.assert_called_once_with('/test/repo')
        except Exception:
            self.fail("os.chdir вызвал исключение при правильной конфигурации.")

    @patch('os.chdir')
    @patch('subprocess.check_output')
    def test_get_commit_dependencies(self, mock_subprocess, mock_chdir):
        mock_subprocess.return_value = b"commit1\ncommit2\ncommit3"
        visualizer = DependencyVisualizer(self.config_path)
        visualizer.config = self.mock_config['Paths'] | {'target_file': self.mock_config['Settings']['TargetFile']}
        commits = visualizer.get_commit_dependencies()
        self.assertEqual(commits, ["commit1", "commit2", "commit3"])

    def test_read_config_missing_section(self, mock_getitem, mock_read):
        # Проверка, если отсутствует секция в конфиге
        mock_getitem.side_effect = KeyError("Paths")
        with self.assertRaises(KeyError):
            DependencyVisualizer(self.config_path)

    @patch('builtins.open', new_callable=mock_open)
    def test_save_graph_file_error(self, mock_file):
        # Проверяем обработку ошибок при сохранении файла
        mock_file.side_effect = IOError("Failed to open file")
        visualizer = DependencyVisualizer(self.config_path)
        graph_mock = MagicMock()
        graph_mock.source = "graph content"
        visualizer.config = {'output_path': '/test/output/graph.dot'}
        with self.assertRaises(IOError):
            visualizer.save_graph(graph_mock)

    @patch('subprocess.check_output')
    @patch('os.chdir')
    @patch('builtins.open', new_callable=mock_open)
    def test_visualize_empty_commits(self, mock_file, mock_chdir, mock_subprocess):
        # Проверяем поведение visualize с пустым списком коммитов
        mock_subprocess.return_value = b""
        visualizer = DependencyVisualizer(self.config_path)
        visualizer.config = self.mock_config['Paths'] | {'target_file': self.mock_config['Settings']['TargetFile']}
        visualizer.visualize()
        mock_file.assert_called()
        written_content = mock_file().write.call_args[0][0]
        self.assertEqual(written_content, "// Commit Dependency Graph\n")

    def test_generate_graph_edge_cases(self):
        # Тестируем граф с одним коммитом
        visualizer = DependencyVisualizer(self.config_path)
        commits = ["commit1"]
        graph = visualizer.generate_graph(commits)
        self.assertIn("commit1", graph.source)
        self.assertNotIn("->", graph.source)  # Нет зависимостей, т.к. один коммит

    @patch('configparser.ConfigParser.read')
    @patch('configparser.ConfigParser.__getitem__')
    def test_read_config(self, mock_getitem, mock_read):
        # Мокаем значения конфигурации
        mock_getitem.side_effect = lambda key: self.mock_config[key]
        visualizer = DependencyVisualizer(self.config_path)
        self.assertEqual(visualizer.config['repo_path'], self.mock_config['Paths']['RepoPath'])
        self.assertEqual(visualizer.config['target_file'], self.mock_config['Settings']['TargetFile'])

    @patch('os.chdir')
    @patch('subprocess.check_output')
    def test_get_commit_dependencies(self, mock_subprocess, mock_chdir):
        mock_subprocess.return_value = b"commit1\ncommit2\ncommit3"
        visualizer = DependencyVisualizer(self.config_path)
        visualizer.config = self.mock_config['Paths'] | {'target_file': self.mock_config['Settings']['TargetFile']}
        commits = visualizer.get_commit_dependencies()
        self.assertEqual(commits, ["commit1", "commit2", "commit3"])

    @patch('os.chdir')
    @patch('subprocess.check_output')
    def test_get_commit_dependencies_empty(self, mock_subprocess, mock_chdir):
        mock_subprocess.return_value = b""
        visualizer = DependencyVisualizer(self.config_path)
        visualizer.config = self.mock_config['Paths'] | {'target_file': self.mock_config['Settings']['TargetFile']}
        commits = visualizer.get_commit_dependencies()
        self.assertEqual(commits, [])

    def test_generate_graph(self):
        visualizer = DependencyVisualizer(self.config_path)
        commits = ["commit1", "commit2", "commit3"]
        graph = visualizer.generate_graph(commits)
        self.assertIn("commit1", graph.source)
        self.assertIn("commit2 -> commit1", graph.source)
        self.assertIn("commit3 -> commit2", graph.source)

    def test_generate_graph_empty(self):
        visualizer = DependencyVisualizer(self.config_path)
        commits = []
        graph = visualizer.generate_graph(commits)
        self.assertEqual(graph.source, '// Commit Dependency Graph\n')

    @patch("builtins.open", new_callable=mock_open)
    def test_save_graph(self, mock_file):
        visualizer = DependencyVisualizer(self.config_path)
        graph_mock = MagicMock()
        graph_mock.source = "graph content"
        visualizer.config = {'output_path': '/test/output/graph.dot'}
        visualizer.save_graph(graph_mock)
        mock_file.assert_called_once_with('/test/output/graph.dot', 'w')
        mock_file().write.assert_called_once_with("graph content")

    @patch('os.chdir', side_effect=OSError("Failed to change directory"))
    def test_change_directory_failure(self, mock_chdir):
        visualizer = DependencyVisualizer(self.config_path)
        visualizer.config = self.mock_config['Paths'] | {'target_file': self.mock_config['Settings']['TargetFile']}
        with self.assertRaises(OSError):
            visualizer.get_commit_dependencies()

    @patch('subprocess.check_output')
    def test_git_log_command_success(self, mock_subprocess):
        mock_subprocess.return_value = b"commit1\ncommit2\ncommit3"
        visualizer = DependencyVisualizer(self.config_path)
        visualizer.config = self.mock_config['Paths'] | {'target_file': self.mock_config['Settings']['TargetFile']}
        commits = visualizer.get_commit_dependencies()
        mock_subprocess.assert_called_once_with(
            'git log --pretty=format:"%H" -- test_file.py', shell=True
        )
        self.assertEqual(commits, ["commit1", "commit2", "commit3"])

    @patch('subprocess.check_output')
    @patch('os.chdir')
    @patch('builtins.open', new_callable=mock_open)
    def test_visualize(self, mock_file, mock_chdir, mock_subprocess):
        mock_subprocess.return_value = b"commit1\ncommit2\ncommit3"
        visualizer = DependencyVisualizer(self.config_path)
        visualizer.config = self.mock_config['Paths'] | {'target_file': self.mock_config['Settings']['TargetFile']}
        visualizer.visualize()
        mock_file().write.assert_called()
        written_content = mock_file().write.call_args[0][0]
        self.assertIn("commit1", written_content)
        self.assertIn("commit2 -> commit1", written_content)

    @patch('configparser.ConfigParser.read')
    @patch('configparser.ConfigParser.__getitem__')
    def test_missing_key_in_config(self, mock_getitem, mock_read):
        # Проверяем, что выбрасывается ошибка KeyError
        mock_getitem.side_effect = lambda key: self.mock_config[key] if key in self.mock_config else KeyError(key)
        with self.assertRaises(KeyError) as context:
            DependencyVisualizer(self.config_path)
        self.assertIn("TargetFile", str(context.exception))

if __name__ == "__main__":
    unittest.main()
