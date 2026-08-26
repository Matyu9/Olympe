class ModuleConfigValidationError(Exception):
    def __init__(self, errors: list):
        self.errors = errors
        super().__init__("; ".join(errors))


# Vérifie que le manifeste d'un module contient tout ce qui décrit le module lui-même
# (jamais son infrastructure de déploiement : ça, c'est saisi par l'admin à l'installation)
def check_config_parameters(config_file: dict):
    errors = []

    if "name" not in config_file:
        errors.append("parameter missing: 'name' is not defined")

    if "url-repo" not in config_file:
        errors.append("parameter missing: 'url-repo' is not defined")

    if "guidelines" not in config_file:
        errors.append("parameter missing: 'guidelines' is not defined")

    if "beta" not in config_file:
        errors.append("parameter missing: 'beta' is not defined")

    if "configuration" not in config_file:
        errors.append("parameter missing: 'configuration' is not defined")
    else:
        if "html-input" not in config_file['configuration']:
            errors.append("parameter missing: 'html-input' is not defined in 'configuration'")

        if "install-script" not in config_file['configuration']:
            errors.append("parameter missing: 'install-script' is not defined in 'configuration'")

    if errors:
        raise ModuleConfigValidationError(errors)
