def install_module(config_file: dict):
    """
    :param config_file: list
    :return: integer
    """
    if not isinstance(config_file, dict):  # Vérification du paramètre rentré, si pas correcte => exit
        exit('config_file: type error')

    # Vérification de si tout les éléments sont requis sont présent

    return 0


print(install_module({'name': 'eee'}))
