import json

from . import hard_code

_config = {}
_processes = []


class Config:
    @staticmethod
    def load(path):
        global _config
        with open(path, 'r') as io:
            _config = json.load(io)

    @staticmethod
    def section(key) -> dict:
        return _config.get(key)

    @staticmethod
    def merge():
        config = {}

        for process in _processes:
            process(config)

        config.update(_config.get(hard_code.CK_CORE))
        return config

    @staticmethod
    def process(f):
        _processes.append(f)
        return f
