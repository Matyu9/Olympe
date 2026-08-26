from sqlalchemy import MetaData
from sqlalchemy.orm import declarative_base
from flask import g

# Si vous utilisez un schéma spécifique
metadata = MetaData(schema='cantina_administration')
Base = declarative_base(metadata=metadata)

# Gestion propre d'une session par requête
def get_db(session_local):
    if "db" not in g:
        g.db = session_local()  # 🔥 Nouvelle session pour chaque requête
    return g.db
