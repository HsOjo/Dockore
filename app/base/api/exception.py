class APIErrorException(Exception):
    def __init__(self, code, msg, data=None):
        super().__init__()
        self.code = code
        self.msg = msg
        self.data = data if data is not None else {}
