from typing import List, Dict


class VolumesMappingConvertor:
    @staticmethod
    def to_docker(volumes: List[Dict]):
        result = {}
        for volume in volumes:
            result[volume.pop('path')] = volume
        return result
