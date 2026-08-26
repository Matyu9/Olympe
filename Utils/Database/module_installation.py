from sqlalchemy import Column, Integer, Text, Boolean
from Utils.Database.base import Base


class ModuleInstallation(Base):
    __tablename__ = 'module_installations'

    id = Column(Integer, primary_key=True)
    module_token = Column(Text, nullable=True)  # rempli une fois le Module OIDC créé (étape 'registering')

    # --- Copié depuis le manifeste du module, pour l'historique ---
    name = Column(Text)
    url_repo = Column(Text)
    guidelines = Column(Text)
    beta = Column(Boolean, default=False)
    install_script = Column(Text)
    html_input_schema = Column(Text)  # JSON du schéma html-input tel qu'uploadé
    html_input_values = Column(Text)  # JSON des valeurs saisies par l'admin

    # --- Saisi par l'admin dans le formulaire de déploiement, jamais lu depuis le manifeste ---
    install_target = Column(Text)  # 'local' ou 'remote'
    path_to_clone = Column(Text)
    module_fqdn = Column(Text)
    credentials_saved = Column(Boolean, default=False)
    ssh_config_encrypted = Column(Text, nullable=True)  # Fernet, seulement si install_target='remote' et credentials_saved

    status = Column(Text, default='pending')
    status_message = Column(Text, nullable=True)
    created_at = Column(Integer, default=0)
    updated_at = Column(Integer, default=0)
