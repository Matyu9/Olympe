from smtplib import SMTP_SSL
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import request
from random import randint

from Utils.Database.config import Config
from Utils.Database.user import User


def send_verification_email(database):
    try:
        conn_url = database.query(Config.content).filter(Config.name == "SMTP_URL").first()[0]
        conn_port = database.query(Config.content).filter(Config.name == "SMTP_PORT").first()[0]
        conn_email = database.query(Config.content).filter(Config.name == "SMTP_EMAIL").first()[0]
        conn_passwd = database.query(Config.content).filter(Config.name == "SMTP_PASSWORD").first()[0]

        subject = database.query(Config.content).filter(Config.name == "MAIL_VERIFICATION_SUJET").first()[0]
        message = database.query(Config.content).filter(Config.name == "MAIL_VERIFICATION_CONTENU").first()[0]

        destinataire = database.query(User).filter(User.token == request.cookies.get('token')).first()

    except TypeError:
        return 'error1: Configuration incomplète ou inexistante'

    if destinataire.email_verified:
        return 'already_check'

    if destinataire.email_verification_code is None or destinataire.email_verification_code == 'reset':
        code = get_rand_num_for_email_verif()
        database.query(User).filter(User.token == request.cookies.get("token")).update(
            {"email_verification_code": code}
        )
        database.commit()
    else:
        code = destinataire.email_verification_code

    if conn_url is None or conn_port is None or conn_email is None:
        return 'error1: Configuration incomplète ou inexistante.'

    if subject is None or message is None or subject == "" or message == "" or "{}" not in message:
        return 'error2: Message prédéfinis incomplet ou inexistant'

    mail = MIMEMultipart()
    mail['From'] = conn_email
    mail['To'] = destinataire.email
    mail['Subject'] = subject
    try:
        content = MIMEText(message.format(code).encode('utf-8'), 'plain', 'utf-8')
        mail.attach(content)

        smtp_server = SMTP_SSL(conn_url, int(conn_port))
        smtp_server.ehlo()
        smtp_server.login(conn_email, conn_passwd)

        smtp_server.sendmail(conn_email, destinataire.email, mail.as_string())
        smtp_server.close()

        return 'success'
    except ValueError:
        return 'error1: Configuration incomplète ou inexistante'


def send_test_email(database):
    try:
        conn_url = database.select('''SELECT content FROM cantina_administration.config WHERE name='SMTP_URL' ''', None,
                                   number_of_data=1)[0]
        conn_port = database.select('''SELECT content FROM cantina_administration.config WHERE name='SMTP_PORT' ''',
                                    None, number_of_data=1)[0]
        conn_email = database.select('''SELECT content FROM cantina_administration.config WHERE name='SMTP_EMAIL' ''',
                                     None, number_of_data=1)[0]
        conn_passwd = database.select('''SELECT content FROM cantina_administration.config 
        WHERE name='SMTP_PASSWORD' ''', None, number_of_data=1)[0]

        subject = database.select('''SELECT content FROM cantina_administration.config WHERE 
        name='MAIL_VERIFICATION_SUJET' ''', None, number_of_data=1)[0]
        message = database.select('''SELECT content FROM cantina_administration.config WHERE 
        name='MAIL_VERIFICATION_CONTENU' ''', None, number_of_data=1)[0]
        destinataire = database.select('''SELECT email, email_verified FROM cantina_administration.user 
        WHERE token = %s''', (request.cookies.get('token')), number_of_data=1)[0]


    except TypeError:
        return 'error1: Configuration incomplète ou inexistante'

    if conn_url is None or conn_port is None or conn_email is None:
        return 'error1: Configuration incomplète ou inexistante.'

    if subject is None or message is None or subject == "" or message == "" or "{}" not in message:
        return 'error2: Message prédéfinis incomplet ou inexistant'

    mail = MIMEMultipart()
    mail['From'] = conn_email
    mail['To'] = destinataire
    mail['Subject'] = subject
    try:
        content = MIMEText(message.format("000000").encode('utf-8'), 'plain', 'utf-8')
        mail.attach(content)

        smtp_server = SMTP_SSL(conn_url, int(conn_port))
        smtp_server.ehlo()
        smtp_server.login(conn_email, conn_passwd)

        smtp_server.sendmail(conn_email, destinataire, mail.as_string())
        smtp_server.close()

        return 'success'
    except ValueError:
        return 'error1: Configuration incomplète ou inexistante'


def get_rand_num_for_email_verif():
    code = ''
    for i in range(0, 6):
        code = code + str(randint(0, 9))

    return code
