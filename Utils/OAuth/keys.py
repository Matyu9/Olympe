from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from authlib.jose import JsonWebKey

from Utils.Database.config import get_config, set_config

OIDC_KEY_CONFIG_NAME = "oidc_private_key"
OIDC_KEY_ID = "olympe-oidc-1"


def get_signing_key(database):
    """Renvoie la clé privée RSA (PEM) utilisée pour signer les ID tokens,
    en la générant et en la stockant en base au premier appel."""
    pem = get_config(database, OIDC_KEY_CONFIG_NAME, default=None)
    if pem is None:
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode()
        set_config(database, OIDC_KEY_CONFIG_NAME, pem)
        database.commit()
    return pem


def get_jwks(database):
    """Renvoie le jeu de clés publiques (JWKS) correspondant à la clé de signature."""
    pem = get_signing_key(database)
    jwk = JsonWebKey.import_key(pem, {"kty": "RSA", "kid": OIDC_KEY_ID, "use": "sig", "alg": "RS256"})
    return {"keys": [jwk.as_dict(is_private=False)]}
