from app.services.cli.container import (
    container_item_from_inspect,
    image_item_from_inspect as container_image_item,
)
from app.services.cli.convertors import (
    MountsConvertor,
    OptionConvertor,
    PortMappingConvertor,
    PortsConvertor,
    VolumesMappingConvertor,
    dict_to_lower,
    remove_empty_obj,
)
from app.services.cli.image import image_item_from_inspect
from app.services.cli.network import network_item_from_inspect
from app.services.cli.volume import volume_item_from_inspect
from tests.fakes import (
    make_container_attrs,
    make_image_attrs,
    make_network_attrs,
    make_volume_attrs,
)


def test_dict_to_lower():
    assert dict_to_lower({"FooBar": [{"BAZ": 1}]}) == {"foo_bar": [{"baz": 1}]}


def test_remove_empty_obj():
    assert remove_empty_obj({"a": 1, "b": "", "c": False, "d": []}) == {
        "a": 1,
        "c": False,
    }


def test_container_item_verbose():
    image = container_image_item(make_image_attrs())
    item = container_item_from_inspect(make_container_attrs(), image, verbose=True)
    assert item["id"] == "abcdef123456"
    assert item["name"] == "web"
    assert item["status"] == "running"
    assert item["command"] == "nginx"
    assert item["tty"] is True
    assert item["interactive"] is True
    assert item["network"]["ip"] == "172.17.0.2"
    assert item["network"]["ports"] == [
        {"port": 80, "protocol": "tcp", "listen_ip": "0.0.0.0", "listen_port": 8080}
    ]
    assert item["mounts"][0]["dest"] == "/data"
    assert item["image"]["id"] == "0123456789ab"


def test_container_item_not_verbose():
    item = container_item_from_inspect(make_container_attrs(), {})
    assert set(item.keys()) == {"id", "name", "image", "create_time", "status"}


def test_container_item_host_network_mode():
    attrs = make_container_attrs()
    attrs["NetworkSettings"] = {}
    attrs["HostConfig"] = {}
    item = container_item_from_inspect(attrs, {}, verbose=True)
    assert item["network"]["ip"] is None
    assert item["network"]["prefix"] is None
    assert item["network"]["ports"] is None


def test_container_item_missing_config():
    attrs = make_container_attrs()
    del attrs["Config"]
    attrs["NetworkSettings"] = {}
    attrs["HostConfig"] = {}
    attrs["Mounts"] = []
    item = container_item_from_inspect(attrs, {}, verbose=True)
    assert "command" not in item
    assert item["tty"] is None


def test_container_item_networks_only_fields():
    # Docker API >= 1.44: 顶层无 IPAddress/Gateway, 信息在 Networks 内
    attrs = make_container_attrs()
    attrs["NetworkSettings"] = {
        "Networks": {
            "bridge": {
                "IPAddress": "192.168.215.2",
                "IPPrefixLen": 24,
                "Gateway": "192.168.215.1",
                "MacAddress": "92:8e:95:a5:77:a9",
            },
        },
    }
    item = container_item_from_inspect(attrs, {}, verbose=True)
    net = item["network"]
    assert net["ip"] == "192.168.215.2"
    assert net["prefix"] == 24
    assert net["gateway"] == "192.168.215.1"
    assert net["mac_address"] == "92:8e:95:a5:77:a9"


def test_image_item_verbose():
    item = image_item_from_inspect(make_image_attrs(), verbose=True)
    assert item["id"] == "0123456789ab"
    assert item["tags"] == ["nginx:latest"]
    assert item["command"] == "nginx -g daemon off;"
    assert item["architecture"] == "amd64"
    assert item["os"] == "linux"
    assert item["ports"] == [{"port": 80, "protocol": "tcp"}]


def test_image_item_filters_none_tags():
    attrs = make_image_attrs()
    attrs["RepoTags"] = ["<none>:<none>"]
    item = image_item_from_inspect(attrs)
    assert item["tags"] == []


def test_image_item_missing_attrs():
    attrs = {"Created": "2024-01-01T00:00:00Z", "Size": 100}
    item = image_item_from_inspect(attrs)
    assert item["author"] == ""
    verbose = image_item_from_inspect(attrs, verbose=True)
    assert verbose["architecture"] is None
    assert verbose["ports"] == []


def test_network_item_verbose():
    containers = {
        "a" * 64: {"Name": "web", "IPv4Address": "172.17.0.2/16"},
    }
    item = network_item_from_inspect(make_network_attrs(containers), verbose=True)
    assert item["id"] == "net1234abcde"
    assert item["container_num"] == 1
    assert item["subnet"] == "172.17.0.0/16"
    assert item["gateway"] == "172.17.0.1"
    assert item["ipam_driver"] == "default"
    assert item["attachable"] is True
    assert item["containers"][0]["name"] == "web"
    assert item["containers"][0]["network"]["ip"] == "172.17.0.2"
    assert item["containers"][0]["network"]["prefix"] == 16


def test_network_item_missing_ipam():
    attrs = make_network_attrs()
    attrs["IPAM"] = {}
    item = network_item_from_inspect(attrs, verbose=True)
    assert item["ipam_driver"] is None
    assert "subnet" not in item


def test_volume_item():
    item = volume_item_from_inspect(make_volume_attrs(), verbose=True)
    assert item["id"] == "data"
    assert item["name"] == "data"
    assert item["mount_point"] == "/var/lib/docker/volumes/data/_data"
    assert item["driver_opts"] == {}


def test_volume_item_missing_options():
    attrs = make_volume_attrs()
    del attrs["Options"]
    item = volume_item_from_inspect(attrs, verbose=True)
    assert item["driver_opts"] == {}


def test_mounts_convertor():
    result = MountsConvertor.from_docker([
        {
            "Name": "data",
            "Type": "volume",
            "Driver": "local",
            "Mode": "rw",
            "Source": "/src",
            "Destination": "/dest",
        },
    ])
    assert result == [
        {
            "name": "data",
            "type": "volume",
            "driver": "local",
            "mode": "rw",
            "src": "/src",
            "dest": "/dest",
        },
    ]


def test_mounts_convertor_missing_fields():
    result = MountsConvertor.from_docker([{"Source": "/a", "Destination": "/b"}])
    assert result[0]["type"] is None
    assert result[0]["mode"] is None
    assert result[0]["src"] == "/a"


def test_option_convertor():
    assert OptionConvertor.to([{"key": "a", "value": "1"}]) == {"a": "1"}


def test_ports_convertor():
    assert PortsConvertor.from_docker({"80/tcp": {}, "53/udp": {}}) == [
        {"port": 80, "protocol": "tcp"},
        {"port": 53, "protocol": "udp"},
    ]
    assert PortsConvertor.from_docker(None) == []


def test_port_mapping_convertor_from_docker():
    result = PortMappingConvertor.from_docker({
        "80/tcp": [{"HostIp": "0.0.0.0", "HostPort": "8080"}],
    })
    assert result == [
        {"port": 80, "protocol": "tcp", "listen_ip": "0.0.0.0", "listen_port": 8080}
    ]
    assert PortMappingConvertor.from_docker(None) is None


def test_port_mapping_convertor_to_cli_args():
    args = PortMappingConvertor.to_cli_args([
        {"port": 80, "protocol": "tcp", "listen_ip": "0.0.0.0", "listen_port": 8080},
        {"port": 53, "protocol": "udp", "listen_port": 5353},
        {"port": 443},
    ])
    assert args == [
        "-p", "0.0.0.0:8080:80/tcp",
        "-p", "5353:53/udp",
        "-p", "443/tcp",
    ]
    assert PortMappingConvertor.to_cli_args(None) == []


def test_volumes_mapping_convertor_to_cli_args():
    volumes = [{"path": "data", "bind": "/data", "mode": "ro"}]
    assert VolumesMappingConvertor.to_cli_args(volumes) == ["-v", "/data:data:ro"]
    # input must not be mutated
    assert volumes[0]["path"] == "data"
    assert VolumesMappingConvertor.to_cli_args(None) == []
