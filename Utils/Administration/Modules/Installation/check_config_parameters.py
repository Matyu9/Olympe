class ModuleConfigValidationError(Exception):
    def __init__(self, errors: list):
        self.errors = errors
        super().__init__("; ".join(errors))


# Vérifie que le manifeste d'un module contient tout ce qui décrit le module lui-même
# (jamais son infrastructure de déploiement : ça, c'est saisi par l'admin à l'installation)
def check_config_parameters(config_file: dict):
    errors = []

    if "name" not in config_file:
        errors.append("Paramètre manquant : 'name' n'est pas défini")

    if "url-repo" not in config_file:
        errors.append("Paramètre manquant : 'url-repo' n'est pas défini")

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

    if errors:
        raise ModuleConfigValidationError(errors)
