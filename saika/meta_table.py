_mt = {}


class MetaTable:
    @staticmethod
    def _item(i):
        if i not in _mt:
            _mt[i] = {}
        return _mt[i]

    @staticmethod
    def set(i, k, v):
        data = MetaTable._item(i)
        data[k] = v

    @staticmethod
    def get(i, k, d=None):
        data = MetaTable._item(i)
        if k not in data and d is not None:
            data[k] = d
        return data.get(k, d)

    @staticmethod
    def all(i):
        return _mt.get(i)

    @staticmethod
    def dump():
        return _mt.copy()
