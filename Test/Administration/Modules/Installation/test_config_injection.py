import json

from Utils.Administration.Modules.Installation.config_injection import write_config, _slugify


def test_slugify_normalizes_name():
    assert _slugify("Mon Module Test") == "mon-module-test"
    assert _slugify("néphélées") == "nephelees"
    assert _slugify("   ") == "module"


def test_write_config_local_creates_named_file_with_expected_content(tmp_path):
    filename = write_config(
        install_target="local",
        ssh_config=None,
        path_to_clone=str(tmp_path),
        module_name="Mon Module",
        client_id="client-id-123",
        client_secret="secret-abc",
        module_fqdn="https://module.example.invalid",
        socket_url="http://olympe.example.invalid",
        settings={"input1": "value1"},
    )

    assert filename == "mon-module-config.json"

    written_path = tmp_path / filename
    assert written_path.exists()

    content = json.loads(written_path.read_text())
    assert content == {
        "module_name": "Mon Module",
        "client_id": "client-id-123",
        "client_secret": "secret-abc",
        "module_fqdn": "https://module.example.invalid",
        "socket_url": "http://olympe.example.invalid",
        "settings": {"input1": "value1"},
    }
