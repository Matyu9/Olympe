from uuid import uuid3, uuid1
from argon2 import PasswordHasher
from flask import request

from Utils.Database.user import User
from Utils.Database.permission import Permission
from Utils.Database.modules import Module

def create_user(database):
    token = str(uuid3(uuid1(), str(uuid1())))  # Génération d'un token unique
    hashed_password = PasswordHasher().hash(request.form['password1'])  # Hashage des mots de passe

    # Création de l'utilisateur dans la base de données
    database.add(
        User(
            token=token,
            username=request.form['username'],
            password=hashed_password,
            email=request.form['email'],
            theme=request.form['theme']
        )
    )
    # Création des permissions de l'utilisateur dans la base de données
    database.add(Permission(user_token=token))

    database.commit()  # Toujours commit après un INSERT

    return token
