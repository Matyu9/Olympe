from Utils.Administration.Modules.Installation.credentials_crypto import encrypt_json, decrypt_json


def test_encrypt_decrypt_round_trip(db_session):
    data = {"ssh-url": "1.2.3.4", "ssh-port": "22", "ssh-username": "root", "ssh-password": "hunter2"}

    encrypted = encrypt_json(db_session, data)

    assert encrypted != data  # bien chiffré, pas stocké tel quel
    assert "hunter2" not in encrypted

    assert decrypt_json(db_session, encrypted) == data


def test_encrypting_twice_reuses_the_same_key(db_session):
    """La clé de chiffrement doit être générée une seule fois et réutilisée (comme la clé de
    signature OIDC), pas régénérée à chaque appel — sinon un jeton chiffré plus tôt deviendrait
    illisible."""
    first = encrypt_json(db_session, {"a": "1"})
    second = encrypt_json(db_session, {"a": "1"})

    # Fernet ajoute un nonce/timestamp donc les deux chiffrés diffèrent, mais les deux doivent
    # rester déchiffrables avec la clé actuelle.
    assert decrypt_json(db_session, first) == {"a": "1"}
    assert decrypt_json(db_session, second) == {"a": "1"}
