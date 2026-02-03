from hashlib import sha256
from json import dumps
from os import system, getuid
from platform import uname
from uuid import uuid1, uuid3
from argon2 import PasswordHasher
from pymysql import connect


deprecated = """
  $$$$$$$\                                                              $$\                     $$\ 
  $$  __$$\                                                             $$ |                    $$ |
  $$ |  $$ | $$$$$$\   $$$$$$\   $$$$$$\   $$$$$$\   $$$$$$$\ $$$$$$\ $$$$$$\    $$$$$$\   $$$$$$$ |
  $$ |  $$ |$$  __$$\ $$  __$$\ $$  __$$\ $$  __$$\ $$  _____|\____$$\\_$$  _|  $$  __$$\ $$  __$$ |
  $$ |  $$ |$$$$$$$$ |$$ /  $$ |$$ |  \__|$$$$$$$$ |$$ /      $$$$$$$ | $$ |    $$$$$$$$ |$$ /  $$ |
  $$ |  $$ |$$   ____|$$ |  $$ |$$ |      $$   ____|$$ |     $$  __$$ | $$ |$$\ $$   ____|$$ |  $$ |
  $$$$$$$  |\$$$$$$$\ $$$$$$$  |$$ |      \$$$$$$$\ \$$$$$$$\\$$$$$$$ | \$$$$  |\$$$$$$$\ \$$$$$$$ |
  \_______/  \_______|$$  ____/ \__|       \_______| \_______|\_______|  \____/  \_______| \_______|
                      $$ |                                                                          
                      $$ |                                                                          
                      \__|                                                                          
"""

def create_user():
    token = str(uuid3(uuid1(), str(uuid1())))  # Génération d'un token unique
    hashed_password = PasswordHasher().hash(password)  # Hashage des mots de passe

    # Création de l'utilisateur dans la base de données
    cursor.execute("""INSERT INTO cantina_administration.user(token, username, password, email) 
    VALUES (%s, %s, %s, %s)""", (token, username, hashed_password, ""))

    # Création des permissions de l'utilisateur dans la base de données
    cursor.execute("""INSERT INTO cantina_administration.permission(user_token, show_log, edit_username, edit_email, 
    edit_password, edit_profile_picture, edit_A2F, edit_theme, show_specific_account, edit_username_admin, 
    edit_email_admin, edit_password_admin, edit_profile_picture_admin, allow_edit_username, allow_edit_email, 
    allow_edit_password, allow_edit_profile_picture, allow_edit_A2F, create_user, delete_account, desactivate_account, 
    edit_permission, show_all_modules, on_off_modules, on_off_maintenance, delete_modules, add_modules, 
    edit_name_module, edit_url_module, edit_socket_url, edit_smtp_config, admin) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s, %s, %s)""",
                   (token, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1))

    con.commit()
    return token


def create_config():
    token = str(uuid3(uuid1(), str(uuid1())))  # Génération d'un token unique
    secret_token = sha256(PasswordHasher().hash(token).encode())
    cursor.execute("""INSERT INTO cantina_administration.config(name, content) VALUES (%s, %s)""",
                   ("secret_token", secret_token))
    perm_list = ["edit_username", "edit_password", "edit_email", "edit_profile_picture", "edit_a2f", "SMTP_URL",
                 "SMTP_PORT", "SMTP_EMAIL", "SMTP_PASSWORD", "MAIL_VERIFICATION_SUJET", "MAIL_VERIFICATION_CONTENU"]
    for element in perm_list:
        cursor.execute("""INSERT INTO cantina_administration.config(name, content) VALUES (%s, %s)""",
                       (element, 0))


CRED = '\033[91m'
CEND = '\033[0m'
CWAR = '\033[93m'
based_on = None
os_info = uname()
database = [False, False]
ph = PasswordHasher()

exit(deprecated)

if getuid() != 0:
    exit("L'installation doit être faite avec les permissions d'administrateur!")
elif os_info.system != "Linux":
    exit("L'installation doit être faire sur une système linux!")

print("Bienvenue dans l'installation de Cantina Olympe!")

if "Debian" in os_info.version:
    print("Système Debian détecté.")
    system("sudo adduser cantina --system")
    system("sudo addgroup cantina")
    system("sudo apt install python3-venv")
else:
    distrib_check = input(
        "Votre système est:\n     1: Basé sur Debian\n     2: Basé sur Arch\n     3: Basé sur Red Hat\n")
    while distrib_check not in ["1", "2", "3"]:
        print("Merci de répondre uniquement par 1, 2 ou 3!")
        distrib_check = input(
            "Votre système est:\n     1: Basé sur Debian\n     2: Basé sur Arch\n     3: Basé sur Red Hat\n")

    if distrib_check == "1" or distrib_check == "3":
        system("sudo adduser cantina --system")
        system("sudo addgroup cantina")
    elif distrib_check == "2":
        system("sudo useradd cantina")
        system("sudo groupadd cantina")
    else:
        exit("Vous avez cassé notre système :/")

system("sudo usermod -a -G cantina cantina")
system("git clone https://github.com/Cantina-Org/Olympe /home/cantina/Olympe")
system("python3 -m venv /home/cantina/Olympe/venv")
system('/home/cantina/Olympe/venv/bin/pip install -r /home/cantina/Olympe/requirements.txt')
system('sudo mkdir /home/cantina/Olympe/static/ProfilePicture')

print(CRED +
      "----------------------------------------------------------------------------------------------------------------"
      "--------------------------------------------------------" + CEND
      )

print("Identifiants de connexion aux bases de données: ")
database_username = input("    Nom d'utilisateur: ")
database_password = input("    Mots de passe: ")
database_host = input("     Adresse: ")
database_port = input("     Port: ")

while database_password == '' or database_username == '' or database_host == '' or database_port == '':
    print("Merci de rentrer des valeurs!")
    database_username = input("    Nom d'utilisateur: ")
    database_password = input("    Mots de passe: ")
    database_host = input("    Adresse: ")
    database_port = input("    Port: ")

try:
    con = connect(user=database_username, password=database_password, host=database_host, port=int(database_port))
    cursor = con.cursor()

except Exception as e:
    exit("Un problème est survenue lors de la connexion à Mariadb: " + str(e))

cursor.execute("""SHOW DATABASES""")
data = cursor.fetchall()

for i in data:
    if i[0] == 'cantina_administration':
        database[0] = True

if not database[0]:
    cursor.execute("CREATE DATABASE cantina_administration")

cursor.execute("USE cantina_administration")

cursor.execute("""CREATE TABLE IF NOT EXISTS cantina_administration.user(id INT PRIMARY KEY AUTO_INCREMENT, 
token TEXT NOT NULL,  username TEXT NOT NULL, password TEXT NOT NULL, email TEXT NOT NULL, 
email_verified BOOL DEFAULT FALSE, email_verification_code TEXT, picture BOOL DEFAULT false, 
A2F BOOL DEFAULT FALSE, A2F_secret TEXT, last_connection DATE, 
desactivated BOOL DEFAULT FALSE, theme TEXT DEFAULT 'light', super_admin BOOL DEFAULT FALSE)""", None)
cursor.execute("""CREATE TABLE IF NOT EXISTS cantina_administration.config(id INT PRIMARY KEY AUTO_INCREMENT, 
name TEXT, content TEXT)""", None)
cursor.execute("""CREATE TABLE IF NOT EXISTS cantina_administration.modules(id INT PRIMARY KEY AUTO_INCREMENT, 
token TEXT, name TEXT, fqdn TEXT, maintenance BOOL default FALSE, status INTEGER DEFAULT 0, 
socket_url TEXT DEFAULT '/socket/', last_heartbeat INT)""", None)
cursor.execute("""CREATE TABLE IF NOT EXISTS cantina_administration.permission(id INT PRIMARY KEY AUTO_INCREMENT,
user_token TEXT NOT NULL, show_log BOOL DEFAULT FALSE, edit_username BOOL DEFAULT FALSE, edit_email BOOL DEFAULT FALSE, 
edit_password BOOL DEFAULT FALSE, edit_profile_picture BOOL DEFAULT FALSE, edit_A2F BOOL DEFAULT FALSE, 
edit_theme BOOL DEFAULT FALSE, show_specific_account BOOL DEFAULT FALSE, edit_username_admin BOOL DEFAULT FALSE,
edit_email_admin BOOL DEFAULT FALSE, edit_password_admin BOOL DEFAULT FALSE, 
edit_profile_picture_admin BOOl DEFAULT FALSE, allow_edit_username BOOL DEFAULT FALSE, 
allow_edit_email BOOL DEFAULT FALSE, allow_edit_password BOOL DEFAULT FALSE,
allow_edit_profile_picture BOOL DEFAULT FALSE, allow_edit_A2F BOOL DEFAULT FALSE, create_user BOOL DEFAULT FALSE, 
delete_account BOOL DEFAULT FALSE, desactivate_account BOOL DEFAULT FALSE, edit_permission BOOL DEFAULT FALSE, 
show_all_modules BOOL DEFAULT FALSE, on_off_modules BOOL DEFAULT FALSE, on_off_maintenance BOOL DEFAULT FALSE, 
delete_modules BOOL DEFAULT FALSE, add_modules BOOL DEFAULT FALSE, edit_name_module BOOL DEFAULT FALSE, 
edit_url_module BOOL DEFAULT FALSE, edit_socket_url BOOL DEFAULT FALSE, edit_smtp_config BOOL DEFAULT FALSE, admin BOOL DEFAULT FALSE)""", None)
cursor.execute("""CREATE TABLE IF NOT EXISTS cantina_administration.log(id INT PRIMARY KEY AUTO_INCREMENT, 
    action_name TEXT, user_ip TEXT, user_token TEXT, details TEXT, log_level INT)""", None)
print("Nous allons donc créer un premier compte administrateur.")

username = input("    Nom d'utilisateur: ")
password = input("    Mots de passe: ")
email = input("    Email: ")

create_user()
create_config()

print(CRED +
      "----------------------------------------------------------------------------------------------------------------"
      "--------------------------------------------------------" + CEND
      )

con.commit()

print(CRED +
      "----------------------------------------------------------------------------------------------------------------"
      "--------------------------------------------------------" + CEND
      )

print("Sur quel port local souhaitez-vous utiliser Cantina Olympe ?")
port = input("Port : ")
print("Sur quel domaine internet souhaitez-vous utiliser Cantina Olympe ?")
domain = input("Domaine internet : ")

print(CRED +
      "----------------------------------------------------------------------------------------------------------------"
      "--------------------------------------------------------" + CEND
      )


cursor.execute('''INSERT INTO cantina_administration.modules(token, name, fqdn) VALUES (%s, 'olympe', %s)''',
               (str(uuid3(uuid1(), str(uuid1()))), domain))
con.commit()

json_data = {
    "database": [{
        "username": database_username,
        "password": database_password,
        "address": database_host,
        "port": int(database_port)
    }],
    "modules": [{
        "name": "olympe",
        "port": port,
        "maintenance": False,
        "debug_mode": False
    }]
}

with open("/home/cantina/Olympe/config.json", "w") as outfile:
    outfile.write(dumps(json_data, indent=4))

launch_startup = input("Voullez vous lancez Cantina Olympe au lancement de votre serveur? ")
system("touch /etc/systemd/system/cantina_olympe.service")
system(f"""echo '[Unit]
Description=Cantina Olympe
[Service]
User=cantina
WorkingDirectory=/home/cantina/Olympe
ExecStart=/home/cantina/Olympe/venv/bin/python app.py
[Install]
WantedBy=multi-user.target' >> /etc/systemd/system/cantina_olympe.service""")
system('chown cantina:cantina /home/cantina/*/*/*')
system("systemctl enable cantina_olympe")
system("systemctl start cantina_olympe")
print(CRED +
      "----------------------------------------------------------------------------------------------------------------"
      "--------------------------------------------------------" + CEND
      )

print("Nous venons de finir l'instalation de Cantina! Vous pouvez maintenant configurer votre serveur web pour qu'il " +
      f"pointe sur l'ip 127.0.0.1:{port}!")
