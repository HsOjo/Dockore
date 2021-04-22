from typing import List, Dict


class PortMappingConvertor:
    @staticmethod
    def to_docker(ports: list):
        if ports is None:
            return None

        result = {}

        for port in ports:
            key = '%(port)d/%(protocol)s' % port
            if key not in result:
                result[key] = (port['listen_ip'], port['listen_port'])
            else:
                if isinstance(result[key], tuple):
                    result[key] = [result[key][1], port['listen_port']]
                elif isinstance(result[key], list):
                    result[key].append(port['listen_port'])

        return result

    @staticmethod
    def from_docker(ports: dict):
        if ports is None:
            return None

        result = []
        for inner, host in ports.items():
            inner: str
            host: List[Dict]
            port, protocol = inner.split('/')
            for i in host:
                listen_ip, listen_port = i['HostIp'], i['HostPort']
                result.append(dict(
                    port=int(port), protocol=protocol,
                    listen_ip=listen_ip, listen_port=int(listen_port)
                ))

        return result
