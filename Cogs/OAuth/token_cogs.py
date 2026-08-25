from Utils.OAuth.server import authorization_server


def oauth_token_cogs():
    return authorization_server.create_token_response()
