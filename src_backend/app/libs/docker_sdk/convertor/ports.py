class PortsConvertor:
    @staticmethod
    def from_docker(ports: dict):
        result = []
        if ports:
            for k in ports:
                port, protocol = k.split('/')
                result.append(dict(
                    port=int(port), protocol=protocol
                ))

        return result
