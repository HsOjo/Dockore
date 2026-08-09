from app.services.docker.convertors import (
    ContainerConvertor,
    HistoriesConvertor,
    ImageConvertor,
    MountsConvertor,
    NetworkConvertor,
    OptionConvertor,
    PortMappingConvertor,
    PortsConvertor,
    VolumeConvertor,
    VolumesMappingConvertor,
    dict_to_lower,
    remove_empty_obj,
)
from tests.fakes import (
    make_container_obj,
    make_image_obj,
    make_network_obj,
    make_volume_obj,
)


def test_dict_to_lower():
    assert dict_to_lower({"FooBar": [{"BAZ": 1}]}) == {"foo_bar": [{"baz": 1}]}


def test_remove_empty_obj():
    assert remove_empty_obj({"a": 1, "b": "", "c": False, "d": []}) == {
        "a": 1,
        "c": False,
    }


def test_container_convertor_verbose():
    item = ContainerConvertor.from_docker(make_container_obj(), verbose=True)
    assert item["id"] == "abcdef1234"
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


def test_container_convertor_not_verbose():
    item = ContainerConvertor.from_docker(make_container_obj())
    assert set(item.keys()) == {"id", "name", "image", "create_time", "status"}


def test_image_convertor_verbose():
    item = ImageConvertor.from_docker(make_image_obj(), verbose=True)
    assert item["id"] == "0123456789ab"
    assert item["tags"] == ["nginx:latest"]
    assert item["command"] == "nginx -g daemon off;"
    assert item["architecture"] == "amd64"
    assert item["os"] == "linux"
    assert item["ports"] == [{"port": 80, "protocol": "tcp"}]


def test_network_convertor_verbose():
    item = NetworkConvertor.from_docker(
        make_network_obj(containers=[make_container_obj()]), verbose=True
    )
    assert item["id"] == "net1234abc"
    assert item["container_num"] == 1
    assert item["subnet"] == "172.17.0.0/16"
    assert item["gateway"] == "172.17.0.1"
    assert item["ipam_driver"] == "default"
    assert item["attachable"] is True
    assert item["containers"][0]["name"] == "web"


def test_volume_convertor():
    item = VolumeConvertor.from_docker(make_volume_obj(), verbose=True)
    assert item["name"] == "data"
    assert item["mount_point"] == "/var/lib/docker/volumes/data/_data"
    assert item["driver_opts"] == {}


def test_histories_convertor():
    histories = HistoriesConvertor.from_docker([
        {
            "Id": "sha256:0123456789abcdef",
            "Created": 1704067200,
            "CreatedBy": "/bin/sh -c #(nop) CMD",
            "Tags": None,
            "Size": 0,
            "Comment": "",
        },
    ])
    assert histories[0]["id"] == "0123456789"
    assert histories[0]["created_by"] == "/bin/sh -c #(nop) CMD"
    assert histories[0]["created_time"].endswith("Z")


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


def test_option_convertor():
    assert OptionConvertor.to([{"key": "a", "value": "1"}]) == {"a": "1"}


def test_ports_convertor():
    assert PortsConvertor.from_docker({"80/tcp": {}, "53/udp": {}}) == [
        {"port": 80, "protocol": "tcp"},
        {"port": 53, "protocol": "udp"},
    ]
    assert PortsConvertor.from_docker(None) == []


def test_port_mapping_convertor_to_docker():
    result = PortMappingConvertor.to_docker([
        {"port": 80, "protocol": "tcp", "listen_ip": "0.0.0.0", "listen_port": 8080},
        {"port": 80, "protocol": "tcp", "listen_ip": "0.0.0.0", "listen_port": 8081},
    ])
    assert result == {"80/tcp": [8080, 8081]}
    assert PortMappingConvertor.to_docker(None) is None


def test_port_mapping_convertor_from_docker():
    result = PortMappingConvertor.from_docker({
        "80/tcp": [{"HostIp": "0.0.0.0", "HostPort": "8080"}],
    })
    assert result == [
        {"port": 80, "protocol": "tcp", "listen_ip": "0.0.0.0", "listen_port": 8080}
    ]
    assert PortMappingConvertor.from_docker(None) is None


def test_volumes_mapping_convertor():
    volumes = [{"path": "data", "bind": "/data", "mode": "ro"}]
    assert VolumesMappingConvertor.to_docker(volumes) == {
        "data": {"bind": "/data", "mode": "ro"},
    }
    # input must not be mutated
    assert volumes[0]["path"] == "data"


from types import SimpleNamespace


def test_image_convertor_missing_attrs():
    obj = SimpleNamespace(
        short_id="sha256:0123456789ab",
        tags=[],
        attrs={"Created": "2024-01-01T00:00:00Z", "Size": 100},
    )
    item = ImageConvertor.from_docker(obj)
    assert item["author"] == ""
    verbose = ImageConvertor.from_docker(obj, verbose=True)
    assert verbose["architecture"] is None
    assert verbose["ports"] == []


def test_container_convertor_host_network_mode():
    obj = make_container_obj()
    obj.attrs["NetworkSettings"] = {}
    obj.attrs["HostConfig"] = {}
    item = ContainerConvertor.from_docker(obj, verbose=True)
    assert item["network"]["ip"] is None
    assert item["network"]["prefix"] is None
    assert item["network"]["ports"] is None


def test_container_convertor_missing_config():
    obj = make_container_obj()
    del obj.attrs["Config"]
    obj.attrs["NetworkSettings"] = {}
    obj.attrs["HostConfig"] = {}
    obj.attrs["Mounts"] = []
    item = ContainerConvertor.from_docker(obj, verbose=True)
    assert "command" not in item
    assert item["tty"] is None


def test_network_convertor_missing_ipam():
    obj = make_network_obj()
    obj.attrs["IPAM"] = {}
    item = NetworkConvertor.from_docker(obj, verbose=True)
    assert item["ipam_driver"] is None
    assert "subnet" not in item


def test_volume_convertor_missing_options():
    obj = make_volume_obj()
    del obj.attrs["Options"]
    item = VolumeConvertor.from_docker(obj, verbose=True)
    assert item["driver_opts"] == {}


def test_mounts_convertor_missing_fields():
    result = MountsConvertor.from_docker([{"Source": "/a", "Destination": "/b"}])
    assert result[0]["type"] is None
    assert result[0]["mode"] is None
    assert result[0]["src"] == "/a"
