# Contribuer à Olympe

Merci de vouloir contribuer à Olympe ! Ce document explique comment le projet est organisé, les
conventions à suivre et comment proposer vos changements.

## 🛠️ Mise en place

Pour installer les dépendances, configurer `config.json` et lancer le serveur, suivez la section
« Installation & Développement » du [README](README.md). Pour lancer les tests, suivez la section
« Tests » du même fichier.

## 🏗️ Architecture — le pattern « Cogs »

Le code est organisé autour d'un pattern maison, les **Cogs** :

* **`app.py`** assemble l'application et enregistre les blueprints ; il ne déclare aucune route
  lui-même. **`Blueprints/<domaine>.py`** (un fichier par domaine, calqué sur `Cogs/<Domaine>/`)
  déclare les routes Flask et délègue à un cogs. Une route reste volontairement fine, et accède à
  la DB/config via `flask.current_app` plutôt que par closure (voir `Blueprints/administration.py`) :
  ```python
  @admin_bp.route('/user/edit_permission/', methods=['POST'])
  def edit_permission_user():
      return edit_user_permission_cogs(get_db(current_app.config['SESSION_FACTORY']))
  ```
* **`Cogs/<Domaine>/<action>_cogs.py`** contient la logique d'une route : la fonction
  `*_cogs()` reçoit la session DB (et parfois d'autres dépendances comme `upload_path`) et
  renvoie directement une réponse Flask (`redirect`, `render_template`, `jsonify`).
* **`Utils/Database/*`** contient les modèles SQLAlchemy, un fichier par table.
* **`Utils/<Domaine>/*`** contient la logique métier réutilisable, idéalement sans dépendance à
  Flask (`request`, cookies...) quand c'est possible — c'est ce qui permet de la tester
  directement, sans serveur ni base de données (voir par exemple
  `Utils/Administration/Modules/Installation/check_config_parameters.py`).

Convention observée dans la quasi-totalité des cogs protégés par une connexion : la même
structure de vérification en tête de fonction, à réutiliser telle quelle pour toute nouvelle
route protégée :

```python
if verify_login(database) and verify_login(database) != 'desactivated':
    ...  # logique de la route
elif verify_login(database) == 'desactivated':
    return redirect(url_for('sso.sso_login', error='2'))
else:
    return redirect(url_for('sso.sso_login'))
```

Notez que le hook global `verify_maintenance` (`app.before_request` dans `app.py`) intercepte déjà
les requêtes non authentifiées pour toute route en dehors de `/static/`, `/sso/`,
`/user_space/get_profile_picture`, `/oauth/` et `/.well-known/` — le `else` ci-dessus reste donc
une défense en profondeur plutôt que le seul rempart.

## 🔐 Modèle de permissions

`Permission` (`Utils/Database/permission.py`) est un ensemble de booléens, un par action précise
(`edit_smtp_config`, `add_modules`, `delete_account`, ...), plus un booléen `admin` qui contourne
toutes les vérifications. Le pattern de garde standard est :

```python
if not user_permission.<action_specifique> and not user_permission.admin:
    return redirect(...)
```

**`admin` doit toujours rester un cas à part.** Si vous ajoutez un endpoint qui modifie une
permission à partir d'un nom reçu du client (comme `edit_user_permission_cogs`), n'acceptez
jamais ce nom tel quel : whitelistez-le explicitement aux colonnes réelles de `Permission`, et
exigez `admin` spécifiquement pour toucher à la colonne `admin` elle-même. C'est exactement le bug
(élévation de privilèges) qui a été corrigé dans `Cogs/Administration/User/edit_user_permission.py`
— prenez ce fichier comme référence.

## 🛡️ Sécurité — points d'attention spécifiques à ce projet

* **Jamais de nom de champ client utilisé tel quel** dans un `update()`/`set_config()` SQLAlchemy
  (`request.form`, `request.json`) : whitelistez toujours les clés acceptées. Voir
  `Cogs/Administration/User/smtp_config.py` (whitelist `SMTP_KEYS`) comme exemple.
* **L'installateur de modules** (`Utils/Administration/Modules/Installation/`) exécute `git clone`
  et `bash <script>` à partir de champs d'un manifeste fourni par l'auteur d'un module. Toute
  nouvelle donnée du manifeste qui finit dans une commande shell doit être validée dans
  `check_config_parameters.py` avant d'être utilisée (schéma d'URL, absence de `..`, pas de
  préfixe `-` qui serait interprété comme une option, etc.).
* **Uploads de fichiers** (photo de profil, etc.) : l'extension sauvegardée doit toujours venir
  d'une whitelist explicite, jamais du nom de fichier envoyé par le client.
* **Cookies d'authentification** : tout nouveau cookie de session doit être posé avec `httponly`,
  `samesite` et `secure` (sauf en `debug_mode`), comme dans `Cogs/SSO/login.py`.

## 🧪 Tests

Les tests (`Test/`) envoient de vraies requêtes HTTP à un serveur `python app.py` déjà lancé, avec
une vraie base MySQL/MariaDB — pas de mocks. Les fixtures partagées (`base_url`, `make_user`,
`make_module`, `make_group`, `login_as`, `db_session`, ...) sont définies dans `Test/conftest.py` ;
chaque compte/module/groupe créé via ces fixtures est automatiquement nettoyé en fin de test.

* Un fichier par fonctionnalité, sous `Test/<Domaine>/test_*.py`.
* Toute logique testable sans serveur (validation, calculs, helpers dans `Utils/`) devrait avoir
  des tests unitaires directs à côté (voir `Test/Administration/Modules/Installation/` pour des
  exemples), plutôt que de tout faire passer par une requête HTTP.
* `Test/Socket/unit/test_socket.py` ne suit pas le pattern « serveur externe » : il instancie sa
  propre app en mémoire (`socketio.test_client`) plutôt que de parler HTTP à un `python app.py`
  déjà lancé.
* Les tests répétitifs par nature (même garde vérifiée route par route) vont dans
  `Test/AccessControl/`, marqués `access_control` et exclus du run `pytest` par défaut
  (`addopts` dans `pytest.ini`) — voir la section Tests du README.

## 📝 Convention de commit

Les messages de commit suivent ce format : un titre court et impératif en français, une
description détaillée en français, puis le même titre et la même description traduits en anglais.
Consultez `git log` pour des exemples concrets. Pas de ligne `Co-Authored-By`.

Fait notable en regardant l'historique : les messages en français n'utilisent pas d'accents
(« desormais », « etait », « acces »...), probablement pour rester safe sur tous les terminaux —
suivez cette convention plutôt que d'ajouter des accents.

```
Corrige la fuite de session au logout

Le cookie de session n'etait jamais reellement efface au logout car le
`domain=` ne correspondait pas a celui pose au login...

Fix session leak on logout

The session cookie was never actually cleared on logout because the
`domain=` didn't match the one set at login...
```

## 🤝 Process de contribution

* Pour un changement significatif, ouvrez d'abord une issue pour en discuter avant de coder.
* Forkez, créez une branche dédiée, puis ouvrez une Pull Request vers `main`.
* Assurez-vous que la suite de tests passe (`pytest`, voir la section Tests du README) avant de
  proposer votre PR.
* L'aide est particulièrement bienvenue sur l'implémentation du protocole **SAML** et sur le
  durcissement/les tests de l'**installateur de modules** (déploiement local/SSH, fédération
  OIDC) — voir la section « État du projet » du README pour le détail.
