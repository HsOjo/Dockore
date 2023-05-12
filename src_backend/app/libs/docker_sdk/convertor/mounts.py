from typing import List


class MountsConvertor:
    @staticmethod
    def from_docker(mounts: List[dict]):
        result = []
        for mount in mounts:
            result.append(dict(
                name=mount.get('Name'), type=mount['Type'], driver=mount.get('Driver'),
                mode=mount['Mode'], src=mount['Source'], dest=mount['Destination']
            ))
        return result
