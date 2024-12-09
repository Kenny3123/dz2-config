import os
import configparser
import subprocess
from graphviz import Digraph


config = configparser.ConfigParser()
config.read('config.ini')

# Получение значений из секции [Paths]
try:
    graphviz_path = config['Paths']['GraphvizPath']
    repo_path = config['Paths']['RepoPath']
    output_path = config['Paths']['OutputPath']
except KeyError as e:
    print(f"Ошибка: отсутствует ключ {e} в секции 'Paths'. Проверьте config.ini.")
    raise

class DependencyVisualizer:
    def __init__(self, config_path):
        self.config = self._read_config(config_path)

    def _read_config(self, config_path):
        config = configparser.ConfigParser()
        config.read(config_path)
        return {
            'graphviz_path': config['Paths']['GraphvizPath'],
            'repo_path': config['Paths']['RepoPath'],
            'output_path': config['Paths']['OutputPath'],
            'target_file': config['Settings']['TargetFile']
        }

    def get_commit_dependencies(self):
        repo_path = self.config['repo_path']
        target_file = self.config['target_file']
        os.chdir(repo_path)

        # Получение списка коммитов, где изменялся указанный файл
        command = f'git log --pretty=format:"%H" -- {target_file}'
        result = subprocess.check_output(command, shell=True).decode('utf-8')
        return result.strip().split('\n')

    def generate_graph(self, commits):
        graph = Digraph(comment="Commit Dependency Graph")
        for commit in commits:
            graph.node(commit, commit)

        # Добавляем зависимости (порядок коммитов из git log):
        for i in range(len(commits) - 1):
            graph.edge(commits[i + 1], commits[i])

        return graph

    def save_graph(self, graph):
        output_path = self.config['output_path']
        with open(output_path, 'w') as file:
            file.write(graph.source)

    def visualize(self):
        commits = self.get_commit_dependencies()
        graph = self.generate_graph(commits)
        self.save_graph(graph)
        print(graph.source)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Dependency Visualizer")
    parser.add_argument("--config", required=True, help="Path to the configuration file")

    args = parser.parse_args()

    visualizer = DependencyVisualizer(args.config)
    visualizer.visualize()