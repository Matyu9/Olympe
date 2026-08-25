from uuid import uuid3, uuid1
from argon2 import PasswordHasher

from Utils.Database.user import User
from Utils.Database.permission import Permission


def create_user(database, username, password, email, email_verified, admin):
    token = str(uuid3(uuid1(), str(uuid1())))
    hashed_password = PasswordHasher().hash(password)

    database.add(User(token=token, username=username, password=hashed_password, email=email,
                       email_verified=email_verified, super_admin=admin))
    database.add(Permission(user_token=token, admin=admin))
    database.commit()

    return token
