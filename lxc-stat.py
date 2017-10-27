#!/usr/bin/env python3

import argparse
import os

cgroup = '/sys/fs/cgroup'


class Containers(object):
    def __init__(self, glob_dir: str = 'devices/lxc') -> None:
        self.containers = []
        for name in filter(lambda d: os.path.isdir(os.path.join(cgroup, glob_dir, d)),
                           os.listdir(os.path.join(cgroup, glob_dir))):
            self.containers.append(Container(name))

    def cpu_usage(self) -> float:
        """Get sum of all containers cpu usage"""
        return sum(map(lambda c: c.get_cpu, self.containers))

    def print_stats(self, args: object) -> None:
        """Print container usage statistics"""

        def sort_by(method: str) -> callable:
            if method in ('name', 'cpu', 'memory', 'percent', 'procs'):
                return lambda c: getattr(c, 'get_{0}'.format(method))
            return lambda c: c.get_cpu

        cpu_usage = self.cpu_usage()
        print('{0:26} {1:18} {2:5} {3} {4}'.format('name ', 'memory', 'cpu', 'cpu%', 'procs'))
        print('-' * 62)
        template = '{0.get_name:20} {0.get_memory:10.2f} M {0.get_cpu:15.2f} {1:6.2f} {0.get_procs}'
        sort = getattr(args, 'sort')
        for container in sorted(self.containers, key=sort_by(sort), reverse=(sort != 'name')):
            print(template.format(container, container.get_percent(cpu_usage)))


class Container(object):
    """Define a container object with its related properties"""

    def __init__(self, name: str) -> None:
        """Class constructor"""
        self.name = name
        self._cache = {}

    @property
    def get_name(self) -> str:
        return self.name

    @property
    def get_memory(self) -> float:
        """Return memory usage in bytes"""
        if 'memory' not in self._cache:
            with open(os.path.join(cgroup, 'memory/lxc', self.name, 'memory.usage_in_bytes'), 'r') as fh:
                self._cache['memory'] = round(int(fh.read().strip()) / 1024 / 1024, 2)
        return self._cache.get('memory')

    @property
    def get_cpu(self) -> float:
        """Return cpu usage in seconds"""
        if 'cpu' not in self._cache:
            with open(os.path.join(cgroup, 'cpu,cpuacct/lxc', self.name, 'cpuacct.usage'), 'r') as fh:
                self._cache['cpu'] = round(int(fh.read().strip()) / 10 ** 9, 2)
        return self._cache.get('cpu')

    def get_percent(self, total: float = 0.0) -> float:
        """Get cpu usage in percent"""
        if 'percent' not in self._cache:
            self._cache['percent'] = round(self.get_cpu * 100 / total, 2)
        return self._cache.get('percent')

    @property
    def get_procs(self) -> int:
        """Get number of processes"""
        if 'procs' not in self._cache:
            with open(os.path.join(cgroup, 'pids/lxc', self.name, 'pids.current'), 'r') as fh:
                self._cache['procs'] = int(fh.read().strip())
        return self._cache.get('procs')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='LXC 2.0 Statistics utility')
    parser.add_argument('--sort', type=str, default='cpu', help='Sort column (could be name, cpu, memory or procs)')

    Containers().print_stats(parser.parse_args())
