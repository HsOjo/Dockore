from typing import List, Dict


class PortMapping:
    @staticmethod
    def to_docker_py(ports):
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
    def from_docker_py(ports):
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