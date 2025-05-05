import json
from check_config_parameters import check_config_parameters


def install_module(config_file: dict):
    """
    :param config_file: list
    :return: integer
    """
    if not isinstance(config_file, dict):  # Vérification du paramètre rentré, si pas correcte → exit
        exit('config_file: type error')

    # Vérification de si tous les éléments sont requis sont présents
    check_config_parameters(config_file)

    return 0


f = open('Example/example-installation.json')
data = json.load(f)

print(install_module(data))
