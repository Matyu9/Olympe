# Olympe

> **Note aux visiteurs :** Olympe sort d'une phase de refonte majeure (UI, Base de données, Architecture). Le cœur est stable, mais le projet est désormais en phase de **Bêta active**.

Olympe est l'outil d'administration centralisé et le futur fournisseur d'identité (SSO) de la suite logicielle Open Source **Cantina**.

Il est conçu pour être **léger**, **simple à déployer** et **compréhensible**, loin des usines à gaz habituelles du marché.

## 🚀 État du projet

* ✅ **Refonte UI :** Terminée
* ✅ **Refonte Base de données :** Terminée
* ✅ **Architecture technique :** Terminée (Python/Flask)
* 🚧 **SSO (Single Sign On) :** En cours d'implémentation (Cibles : OIDC & SAML)

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

## 🤝 Contribuer

Olympe se veut simple et accessible. La stack technique est basée sur **Python** et **Flask**.
Nous cherchons actuellement de l'aide sur :
* L'implémentation des protocoles **OpenID Connect (OIDC)**.
* L'implémentation du protocole **SAML**.

N'hésitez pas à ouvrir une Issue ou une Pull Request !

---

**Cantina Org**
