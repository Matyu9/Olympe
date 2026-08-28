# Olympe

> **Note aux visiteurs :** Olympe sort d'une phase de refonte majeure (UI, Base de données, Architecture). Le cœur est stable, mais le projet est désormais en phase de **Bêta active**.

Olympe est l'outil d'administration centralisé et le futur fournisseur d'identité (SSO) de la suite logicielle Open Source **Cantina**.

Il est conçu pour être **léger**, **simple à déployer** et **compréhensible**, loin des usines à gaz habituelles du marché.

## 🚀 État du projet

* ✅ **Refonte UI :** Terminée
* ✅ **Refonte Base de données :** Terminée
* ✅ **Architecture technique :** Terminée (Python/Flask)
* ✅ **SSO — OpenID Connect (OIDC) :** Implémenté (discovery, JWKS, grants `authorization_code` et `refresh_token`, support PKCE)
* 📋 **SSO — SAML :** Pas encore commencé
* 🚧 **Installateur de modules :** Déploiement d'un module (local ou via SSH) depuis son manifeste, avec fédération OIDC automatique auprès d'Olympe

> [!WARNING]
> Bien que la base soit stable, Olympe est en développement actif. L'utilisation en production critique est pour l'instant déconseillée sans audit préalable.

---

## 🛠️ Installation & Développement

Si vous souhaitez tester Olympe ou contribuer au développement des protocoles SSO, suivez ces étapes.

### Prérequis
* Python 3.x
* Une base de données MySQL ou MariaDB

### 1. Cloner le projet
Clonez le dépôt (ou votre fork) sur votre machine :
```bash
git clone https://github.com/Cantina-Org/Olympe.git
cd Olympe
```

### 2. Installation des dépendances
Il est recommandé d'utiliser un environnement virtuel :
```bash
pip install -r requirements.txt
```

### 3. Configuration
Créez un fichier `config.json` à la racine du projet. Copiez-y la structure suivante et adaptez les identifiants de votre base de données locale :

```json
{
  "database": [{
    "username": "votre_user_db",
    "password": "votre_password_db",
    "address": "localhost",
    "port": 3306
  }],
  "modules": [{
    "name": "Olympe",
    "port": 3000,
    "maintenance": false,
    "debug_mode": true,
    "secret_key": "",
    "global_domain": "127.0.0.1:3000"
  }]
}
```


### 4. Lancement
Lancez l'application via le point d'entrée principal :

```bash
python app.py
```

### 5. Accès
Ouvrez votre navigateur et rendez-vous sur :
`http://localhost:3000/` (ou le port configuré).

---

## 🧪 Tests

Les tests (`Test/`) envoient de vraies requêtes HTTP au serveur Olympe : il faut donc que le serveur tourne déjà avant de les lancer (pas de serveur dédié aux tests).

### 1. Environnement virtuel

Si ce n'est pas déjà fait (voir section Installation ci-dessus) :

```bash
python -m venv venv
```

Activation — Windows (PowerShell) :
```powershell
venv\Scripts\Activate.ps1
```

Activation — macOS/Linux :
```bash
source venv/bin/activate
```

### 2. Dépendances de test

```bash
pip install -r requirements-dev.txt
```

Ce fichier installe `requirements.txt` (les dépendances de l'app) plus `pytest` et `requests`, utilisés uniquement pour les tests.

### 3. Lancer le serveur

Dans un premier terminal, venv activé, avec un `config.json` valide déjà en place (voir section Configuration) :

```bash
python app.py
```

Laissez ce terminal ouvert pendant toute la durée des tests.

### 4. Lancer les tests

Dans un second terminal, venv activé, depuis la racine du projet :

```bash
pytest
```

Pour plus de détail sur chaque test :

```bash
pytest -v
```

`pytest` seul ne lance pas `Test/AccessControl/` (garde connexion/permission vérifiée route par
route, répétitif et volumineux) — voir plus bas.

### Bon à savoir

* **Comptes de test** : chaque test qui a besoin d'un utilisateur crée un compte jetable directement en base (préfixé `_pytest_`, mot de passe fixe défini dans `Test/conftest.py`) et le supprime automatiquement à la fin — même si le test échoue.
* **Serveur non lancé** : si `python app.py` n'a pas été démarré, `pytest` échoue immédiatement avec un message explicite plutôt qu'un timeout confus.
* **`Test/Socket/unit/test_socket.py`** : seule suite qui ne suit pas le pattern « serveur HTTP externe » — elle instancie sa propre app en mémoire (`socketio.test_client`) et gère elle-même le `Module` de test dont `heartbeat` a besoin.
* **`Test/AccessControl/`** : vérifie route par route que chaque page admin redirige sans la bonne permission et répond `200`/`success` avec — marqué `access_control` et exclu du run `pytest` par défaut (`addopts` dans `pytest.ini`) pour ne pas noyer le run classique dans des dizaines de tests répétitifs. Lancer explicitement avec `pytest -m access_control` ou `pytest Test/AccessControl`.

### Ajouter un test

* Un fichier par fonctionnalité, sous `Test/<Domaine>/test_*.py` (ex : `Test/SSO/test_login.py`).
* Les fixtures partagées (`base_url`, `make_user`, `login_as`, ...) sont définies dans `Test/conftest.py`.

---

## 🤝 Contribuer

Olympe se veut simple et accessible. La stack technique est basée sur **Python** et **Flask**.
Nous cherchons actuellement de l'aide sur :
* L'implémentation du protocole **SAML**.
* Le durcissement et les tests de l'installateur de modules (déploiement local/SSH, fédération OIDC).

N'hésitez pas à ouvrir une Issue ou une Pull Request ! Voir [CONTRIBUTING.md](CONTRIBUTING.md)
pour l'architecture du projet, les conventions de code/commit et le détail du process.

---

**Cantina Org**
