from flask import Flask


class Environ:
    app: Flask = None
    program_path: str
    config_path: str
    data_path: str
