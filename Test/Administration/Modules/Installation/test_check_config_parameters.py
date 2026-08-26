import pytest

from Utils.Administration.Modules.Installation.check_config_parameters import (
    check_config_parameters,
    ModuleConfigValidationError,
)


def _valid_manifest():
    return {
        "name": "test",
        "url-repo": "https://example.invalid/repo.git",
        "guidelines": "#",
        "beta": False,
        "configuration": {
            "html-input": {
                "input1": {"type": "url", "default-value": "https://example.invalid"},
            },
            "install-script": "install.sh",
        },
    }


def test_valid_manifest_passes():
    check_config_parameters(_valid_manifest())  # ne doit pas lever


@pytest.mark.parametrize("key", ["name", "url-repo", "guidelines", "beta", "configuration"])
def test_missing_top_level_key_raises(key):
    manifest = _valid_manifest()
    del manifest[key]

    with pytest.raises(ModuleConfigValidationError) as excinfo:
        check_config_parameters(manifest)

    assert any(key in error for error in excinfo.value.errors)


@pytest.mark.parametrize("key", ["html-input", "install-script"])
def test_missing_configuration_key_raises(key):
    manifest = _valid_manifest()
    del manifest["configuration"][key]

    with pytest.raises(ModuleConfigValidationError) as excinfo:
        check_config_parameters(manifest)

    assert any(key in error for error in excinfo.value.errors)


def test_multiple_missing_keys_are_all_reported():
    manifest = _valid_manifest()
    del manifest["name"]
    del manifest["guidelines"]

    with pytest.raises(ModuleConfigValidationError) as excinfo:
        check_config_parameters(manifest)

    assert len(excinfo.value.errors) == 2


def test_old_schema_fields_are_ignored_not_required():
    """Le manifeste ne doit plus jamais exiger d'infos d'infra (SSH/DB) — un ancien fichier
    qui en contient encore ne doit pas planter, elles sont simplement ignorées."""
    manifest = _valid_manifest()
    manifest["configuration"]["database"] = {"connection": {"url": "", "port": 3306}}
    manifest["configuration"]["global"] = {"installation": {"ssh-url": ""}}

    check_config_parameters(manifest)  # ne doit pas lever
