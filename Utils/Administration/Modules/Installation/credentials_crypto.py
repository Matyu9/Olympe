from json import dumps, loads
from cryptography.fernet import Fernet

from Utils.Database.config import get_config, set_config

INSTALL_ENCRYPTION_KEY_CONFIG_NAME = "module_install_encryption_key"


def get_encryption_key(database) -> bytes:
    """Renvoie la clé Fernet utilisée pour chiffrer les identifiants SSH saisis à l'installation,
    en la générant et en la stockant en base au premier appel."""
    key = get_config(database, INSTALL_ENCRYPTION_KEY_CONFIG_NAME, default=None)
    if key is None:
        key = Fernet.generate_key().decode()
        set_config(database, INSTALL_ENCRYPTION_KEY_CONFIG_NAME, key)
        database.commit()
    return key.encode()


def encrypt_json(database, data: dict) -> str:
    fernet = Fernet(get_encryption_key(database))
    return fernet.encrypt(dumps(data).encode()).decode()


def decrypt_json(database, token: str) -> dict:
    fernet = Fernet(get_encryption_key(database))
    return loads(fernet.decrypt(token.encode()).decode())
