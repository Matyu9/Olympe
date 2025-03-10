from sqlalchemy import Column, Integer, Text, Boolean
from Utils.Database.base import Base


class Permission(Base):
    __tablename__ = 'permission'

    id = Column(Integer, primary_key=True)
    user_token = Column(Text, nullable=False)

    # User self-management permissions
    show_log = Column(Boolean, default=False)
    edit_username = Column(Boolean, default=False)
    edit_email = Column(Boolean, default=False)
    edit_password = Column(Boolean, default=False)
    edit_profile_picture = Column(Boolean, default=False)
    edit_A2F = Column(Boolean, default=False)
    edit_ergo = Column(Boolean, default=False)

    # User administration permissions
    show_specific_account = Column(Boolean, default=False)
    edit_username_admin = Column(Boolean, default=False)
    edit_email_admin = Column(Boolean, default=False)
    edit_password_admin = Column(Boolean, default=False)
    edit_profile_picture_admin = Column(Boolean, default=False)

    # Permission management
    allow_edit_username = Column(Boolean, default=False)
    allow_edit_email = Column(Boolean, default=False)
    allow_edit_password = Column(Boolean, default=False)
    allow_edit_profile_picture = Column(Boolean, default=False)
    allow_edit_A2F = Column(Boolean, default=False)

    # User management
    create_user = Column(Boolean, default=False)
    delete_account = Column(Boolean, default=False)
    desactivate_account = Column(Boolean, default=False)
    edit_permission = Column(Boolean, default=False)

    # Module management
    show_all_modules = Column(Boolean, default=False)
    on_off_modules = Column(Boolean, default=False)
    on_off_maintenance = Column(Boolean, default=False)
    delete_modules = Column(Boolean, default=False)
    add_modules = Column(Boolean, default=False)
    edit_name_module = Column(Boolean, default=False)
    edit_url_module = Column(Boolean, default=False)
    edit_socket_url = Column(Boolean, default=False)

    # Configuration
    edit_smtp_config = Column(Boolean, default=False)

    # Super admin
    admin = Column(Boolean, default=False)
