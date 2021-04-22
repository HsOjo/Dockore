from datetime import datetime
from typing import List, Dict


class HistoriesConvertor:
    @staticmethod
    def from_docker(histories):
        histories: List[Dict]
        result = []

        if histories:
            for history in histories:
                item = {k.lower(): v for k, v in history.items()}
                if 'sha256:' in item['id']:
                    item['id'] = item['id'][7:17]
                item['created_by'] = item.pop('createdby')
                item['created_time'] = datetime.fromtimestamp(item.pop('created')).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                result.append(item)

        return result
