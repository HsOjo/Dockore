from typing import Dict, List


class OptionConvertor:
    @staticmethod
    def to(obj: List[Dict]):
        result = {}
        for i in obj:
            result[i['key']] = i['value']
        return result
