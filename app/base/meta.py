_meta = {}


class MetaTable:
    @staticmethod
    def set(i, k, v):
        if i not in _meta:
            _meta[i] = {}
        data = _meta[i]  # type: dict
        data[k] = v

    @staticmethod
    def get(i, k, d=None):
        if i in _meta.keys():
            data = _meta[i]  # type: dict
            if k not in data and d is not None:
                data[k] = d
            return data.get(k, d)

    @staticmethod
    def all(i):
        return _meta.get(i)

    @staticmethod
    def dump():
        return _meta.copy()
