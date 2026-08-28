class ModuleConfigValidationError(Exception):
    def __init__(self, errors: list):
        self.errors = errors
        super().__init__("; ".join(errors))


# 'url-repo' peut être une URL (https/git/ssh/file) OU un chemin de dépôt local brut (cas de
# l'installation 'local') : on ne peut donc pas se limiter à une whitelist de schémas. On bloque
# uniquement les deux vecteurs concrets d'exécution de commande / injection dans `git clone` :
#  - la syntaxe des "remote helpers" git (`<transport>::<adresse>`), notamment `ext::` qui
#    exécute une commande shell arbitraire au moment du clone ;
#  - toute valeur commençant par '-', qui serait interprétée comme une option de la commande
#    plutôt que comme l'URL/chemin à cloner.
def _validate_url_repo(url_repo, errors):
    if not isinstance(url_repo, str) or not url_repo:
        errors.append("Paramètre invalide : 'url-repo' doit être une URL ou un chemin non vide")
        return

    if url_repo.startswith('-'):
        errors.append("Paramètre invalide : 'url-repo' ne peut pas commencer par '-'")
        return

    if '::' in url_repo:
        errors.append("Paramètre invalide : 'url-repo' ne peut pas utiliser la syntaxe d'un remote helper git ('::')")


def _validate_install_script(install_script, errors):
    if not isinstance(install_script, str) or not install_script:
        errors.append("Paramètre invalide : 'install-script' doit être un chemin de fichier non vide")
        return

    # Doit rester un chemin relatif interne au dépôt cloné : pas de chemin absolu, pas de
    # remontée de répertoire ('..'), pas de valeur pouvant être interprétée comme une option.
    if install_script.startswith(('/', '-')) or '..' in install_script:
        errors.append("Paramètre invalide : 'install-script' doit être un chemin relatif sans '..'")


# Vérifie que le manifeste d'un module contient tout ce qui décrit le module lui-même
# (jamais son infrastructure de déploiement : ça, c'est saisi par l'admin à l'installation)
def check_config_parameters(config_file: dict):
    errors = []

    if "name" not in config_file:
        errors.append("Paramètre manquant : 'name' n'est pas défini")

    if "url-repo" not in config_file:
        errors.append("Paramètre manquant : 'url-repo' n'est pas défini")
    else:
        _validate_url_repo(config_file['url-repo'], errors)

    if "guidelines" not in config_file:
        errors.append("Paramètre manquant : 'guidelines' n'est pas défini")

    if "beta" not in config_file:
        errors.append("Paramètre manquant : 'beta' n'est pas défini")

    if "configuration" not in config_file:
        errors.append("Paramètre manquant : 'configuration' n'est pas défini")
    else:
        if "html-input" not in config_file['configuration']:
            errors.append("Paramètre manquant : 'html-input' n'est pas défini dans 'configuration'")

        if "install-script" not in config_file['configuration']:
            errors.append("Paramètre manquant : 'install-script' n'est pas défini dans 'configuration'")
        else:
            _validate_install_script(config_file['configuration']['install-script'], errors)

    if errors:
        raise ModuleConfigValidationError(errors)
