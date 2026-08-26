from Utils.Administration.Modules.Installation.check_config_parameters import check_config_parameters, ModuleConfigValidationError


def install_module(config_file: dict):
    """
    :param config_file: list
    :return: integer
    """
    if not isinstance(config_file, dict):
        raise ModuleConfigValidationError(["config_file: type error"])

    # Vérification de si tous les éléments sont requis sont présents
    check_config_parameters(config_file)

    return 0
