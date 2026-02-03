from flask import request, url_for, redirect
from os import path


def get_profile_picture_cogs(upload_path):
    if request.args.get("token"):
        token = request.args.get("token")
    else:
        token = request.cookies.get('token')

    for extension in ['png', 'jpg', 'jpeg', 'heic']:
        filepath = path.join(upload_path, f"{token}.{extension}")
        if path.exists(filepath):
            return redirect(url_for('static', filename=f'ProfilePicture/{token}.{extension}'))

    # Retourner une image par défaut si aucune n'est trouvée
    return redirect(url_for('static', filename='ProfilePicture/general-logo.png'))