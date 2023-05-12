from docker.models.networks import NetworkCollection, Network
from docker.types import IPAMConfig, IPAMPool

from .collection import CollectionAdapter
from ..convertor import NetworkConvertor, OptionConvertor


class NetworkAdapter(CollectionAdapter):
    _c: NetworkCollection

    def _item(self, id):
        item = self._c.get(id)  # type: Network
        return item

    @staticmethod
    def convert(obj, verbose=False):
        return NetworkConvertor.from_docker(obj, verbose)

    def remove(self, id):
        self._item(id).remove()

    def create(self, name, driver, attachable=True, options=None, subnet=None, gateway=None, ip_range=None):
        ipam_config = None
        if subnet:
            ipam_config = IPAMConfig(pool_configs=[IPAMPool(
                subnet=subnet,
                gateway=gateway,
                iprange=ip_range,
            )])
        item = self._c.create(name, driver,
                              attachable=attachable, options=OptionConvertor.to(options), ipam=ipam_config)
        return self.convert(item, verbose=True)

    def connect(self, id, container_id, ipv4_address=None):
        self._item(id).connect(container_id, ipv4_address=ipv4_address)

    def disconnect(self, id, container_id, force=False):
        self._item(id).disconnect(container_id, force=force)
