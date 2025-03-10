from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData

# Si vous utilisez un schéma spécifique
metadata = MetaData(schema='cantina_administration')
Base = declarative_base(metadata=metadata)
