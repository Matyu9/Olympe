# Guide : créer un module externe pour Olympe/Cantina

Ce guide s'adresse à quiconque souhaite développer un module pour la suite Cantina — c'est-à-dire
une application externe qui délègue son authentification à Olympe via OpenID Connect. Il résume
le protocole de fédération OIDC à implémenter côté module, ainsi que les conventions de code du
dépôt Olympe, utiles si vous voulez garder un style cohérent avec le reste de l'écosystème
Cantina. Le fichier est autonome : vous pouvez le copier dans votre propre projet sans avoir à
revenir dans le dépôt Olympe.

## 1. Ce qu'est un "module" pour Olympe

Un module = une application externe qui délègue l'authentification à Olympe via OpenID
Connect. Olympe stocke chaque module comme une ligne `Module` (`Utils/Database/modules.py`) :
un `client_id` (= `token`, un UUID), un `client_secret` (hashé argon2), un `fqdn`, et des
options (`require_consent`, `restricted_access`, `maintenance`, ...).

Deux façons de faire connaître un module à Olympe aujourd'hui :

* **Manuel (fonctionne déjà)** — un admin va dans Administration > Modules > Ajouter
  (`Cogs/Administration/Modules/add_modules.py`), saisit un nom + un fqdn ; Olympe génère le
  `client_id`/`client_secret` et les affiche une seule fois (`client_secret_shown.html`). C'est
  le chemin le plus rapide pour tester une intégration OIDC dès maintenant.
* **Installateur de modules (🚧 en cours, mais fonctionnel)** — le module fournit un manifeste
  JSON, Olympe clone son dépôt (local ou SSH), écrit un fichier de config à la racine du clone
  avec les identifiants OIDC, puis lance un script d'installation. Détaillé en section 3.

## 2. Federation OIDC — ce que le module doit implémenter côté client

Olympe est un serveur OIDC standard (`authlib`), avec discovery :

```
GET https://<olympe>/.well-known/openid-configuration
GET https://<olympe>/oauth/jwks.json
```

Endpoints exposés (`Blueprints/oauth.py`) :

| Endpoint | Rôle |
|---|---|
| `GET/POST /oauth/authorize` | Authorization endpoint (écran de consentement si `require_consent=true` sur le module) |
| `POST /oauth/token` | Token endpoint |
| `GET/POST /oauth/userinfo` | Userinfo endpoint |
| `GET /oauth/jwks.json` | Clé publique RS256 pour vérifier l'id_token |

Détails à connaître pour l'implémentation côté module (`Utils/Database/modules.py`,
`Utils/OAuth/server.py`) :

* **`response_type` supporté :** `code` uniquement.
* **`grant_type` supportés :** `authorization_code` et `refresh_token`.
* **Auth du client au token endpoint :** `client_secret_post` uniquement — `client_id` +
  `client_secret` envoyés dans le corps du POST, pas de Basic Auth.
* **Scopes supportés :** `openid`, `profile`, `email`. `profile` ajoute
  `preferred_username` (le `username` Olympe), `email` ajoute `email` + `email_verified`.
  `sub` = le `token` (UUID) de l'utilisateur Olympe, stable et unique.
* **`redirect_uri` :** **pas configurable**, elle est dérivée automatiquement du `fqdn` du
  module enregistré : `<fqdn>/callback`. Le module doit donc exposer sa route de callback à
  exactement `<fqdn>/callback`, sans slash final sur le fqdn stocké côté Olympe.
* **PKCE :** supporté mais pas obligatoire (`CodeChallenge(required=False)`).
* **`nonce` :** pas obligatoire (`require_nonce=False`), mais le module peut en envoyer un.
* **id_token :** signé RS256, clé récupérable via `jwks_uri`.
* **`require_consent`** (option du module côté Olympe) : si activé, l'utilisateur voit un
  écran de consentement avant la redirection ; sinon, redirection immédiate.
* **`restricted_access`** (option du module côté Olympe) : si activé, seuls les
  utilisateurs/groupes explicitement autorisés peuvent se connecter à ce module — sinon
  `module_access_denied.html` (403). Non pertinent à implémenter côté module, c'est géré
  entièrement côté Olympe.

Flow classique côté module (standard authorization_code + PKCE recommandé même si non requis) :
1. Rediriger l'utilisateur vers `authorization_endpoint` avec `client_id`, `redirect_uri`
   (= `<fqdn>/callback`), `response_type=code`, `scope=openid profile email`, `state`, et
   idéalement `code_challenge`/`code_challenge_method=S256`.
2. Sur `/callback`, échanger le `code` contre un token à `token_endpoint` (POST,
   `client_secret_post`).
3. Utiliser l'`access_token` sur `userinfo_endpoint` (ou décoder l'`id_token` avec la clé de
   `jwks_uri`) pour récupérer `sub`/`preferred_username`/`email`.
4. Pour rafraîchir, utiliser le `refresh_token` (`grant_type=refresh_token`).

## 3. Passer par l'installateur de modules plutôt qu'un enregistrement manuel

Le manifeste attendu (voir `Example/example-installation.json` dans le dépôt Olympe) :

```json
{
  "name": "mon-module",
  "url-repo": "https://forge.example/mon-module.git",
  "guidelines": "https://forge.example/mon-module/README.md",
  "beta": false,
  "configuration": {
    "html-input": {
      "un_champ": {"type": "url", "default-value": "https://exemple.org"},
      "autre_champ": {"type": "checkbox", "default-value": "true"}
    },
    "install-script": "install.sh"
  }
}
```

Contraintes validées par Olympe (`check_config_parameters.py`) :
* `url-repo` : pas de syntaxe "remote helper" git (`::`, notamment `ext::`), ne doit pas
  commencer par `-`.
* `install-script` : chemin relatif interne au dépôt cloné, pas de `..`, pas de `-` en tête.
* `html-input` décrit un formulaire que l'admin Olympe remplira à l'installation (valeurs
  transmises telles quelles dans le fichier de config généré, voir plus bas) — pas
  d'exécution ni de validation de schéma au-delà de la présence des clés.

Ce que fait Olympe à l'installation (`Utils/Administration/Modules/Installation/installer.py`) :
1. Clone `url-repo` dans `path_to_clone` (local ou SSH, choisi par l'admin, jamais dans le
   manifeste).
2. Crée la ligne `Module` (génère `client_id`/`client_secret`) avec le `fqdn` saisi par
   l'admin dans le formulaire de déploiement (pas dans le manifeste).
3. Écrit **`<nom-slugifié>-config.json` à la racine du clone** (`config_injection.py`) :
   ```json
   {
     "module_name": "...",
     "client_id": "...",
     "client_secret": "...",
     "module_fqdn": "...",
     "socket_url": "...",
     "settings": { "...": "valeurs saisies via html-input" }
   }
   ```
   ⚠️ Piège repéré dans le code actuel : le champ `socket_url` de ce fichier reçoit en réalité
   l'URL d'Olympe (`olympe_url`/issuer), pas une URL de socket.io — mismatch de nommage entre
   l'appelant (`installer.py`, variable `olympe_url`) et le paramètre (`config_injection.py`,
   paramètre `socket_url`). Vérifiez la valeur réelle plutôt que de vous fier au nom du champ.
4. Lance `install-script` (local ou SSH) et log en direct via socket.io
   (`module_install_progress`), termine sur `module_install_done`/`module_install_error`.

Le module lit donc son `client_id`/`client_secret`/`module_fqdn` directement dans ce fichier
JSON généré à sa racine plutôt que de les recevoir en variables d'environnement.

## 4. Heartbeat (optionnel mais attendu par l'admin Olympe)

Le tableau de bord Administration > Modules affiche un statut (`last_heartbeat`, `status`) par
module. Pour l'alimenter, le module doit se connecter en Socket.IO à Olympe et émettre
périodiquement :

```
event: 'heartbeat'
payload: { "token": "<client_id du module>", "fqdn": "<fqdn du module>", "date": <unix_ts> }
```

Côté serveur (`Cogs/Socket/heart_beat_cogs.py`) : vérifie que `token` + `fqdn` correspondent à
la ligne `Module`, met à jour `last_heartbeat`/`status`, répond `response-heartbeat`
(`{"receive-at": ...}`) ou `error-response` si `token`/`fqdn` ne correspondent pas.

## 5. Convention de structure du dépôt Olympe (à reproduire si vous voulez un style cohérent)

Résumé de `CONTRIBUTING.md` — architecture "Cogs" :

* **`app.py`** assemble l'appli et enregistre les blueprints, ne déclare aucune route.
* **`Blueprints/<domaine>.py`** — un fichier par domaine, déclare les routes Flask, reste fin,
  délègue tout de suite à un cogs. Accède DB/config via `flask.current_app`, pas par closure :
  ```python
  @admin_bp.route('/user/edit_permission/', methods=['POST'])
  def edit_permission_user():
      return edit_user_permission_cogs(get_db(current_app.config['SESSION_FACTORY']))
  ```
* **`Cogs/<Domaine>/<action>_cogs.py`** — la logique d'une route. `*_cogs()` reçoit la session
  DB (+ dépendances éventuelles), renvoie directement une réponse Flask.
* **`Utils/Database/*`** — modèles SQLAlchemy, un fichier par table.
* **`Utils/<Domaine>/*`** — logique métier réutilisable, si possible sans dépendance à Flask
  (`request`, cookies) pour rester testable sans serveur ni base (cf.
  `Utils/Administration/Modules/Installation/check_config_parameters.py`).

Garde de connexion standard en tête d'un cogs protégé :
```python
if verify_login(database) and verify_login(database) != 'desactivated':
    ...
elif verify_login(database) == 'desactivated':
    return redirect(url_for('sso.sso_login', error='2'))
else:
    return redirect(url_for('sso.sso_login'))
```

Modèle de permissions : `Permission` (un booléen par action précise + un booléen `admin` qui
contourne tout) :
```python
if not user_permission.<action_specifique> and not user_permission.admin:
    return redirect(...)
```

Sécurité à ne pas oublier si un module reprend ces patterns :
* Jamais un nom de champ client utilisé tel quel dans un `update()`/`set_config()` SQLAlchemy —
  whitelister les clés acceptées.
* Cookies de session : `httponly`, `samesite`, `secure` (sauf en debug).
* Toute donnée d'un manifeste/formulaire qui finit dans une commande shell doit être validée
  avant usage (schéma d'URL, absence de `..`, pas de préfixe `-`).

Tests (pour un module qui reprend `pytest`) : tests HTTP réels contre un serveur déjà lancé (pas
de mocks), un fichier par fonctionnalité sous `Test/<Domaine>/test_*.py`, logique testable sans
serveur directement testée dans `Utils/`.

Commits : titre + description en français (sans accents dans le message de commit — convention
du dépôt Olympe pour rester safe sur tous les terminaux), puis titre + description traduits en
anglais, jamais de ligne `Co-Authored-By`.
