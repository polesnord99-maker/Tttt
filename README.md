# Bot Discord d'entreprise (Python)

Bot français construit avec `discord.py` 2.6+, Components V2, SQLite/`aiosqlite` et commandes slash.

## État de cette livraison

Cette archive est une **première version fonctionnelle de base**, pas une certification de toutes les fonctionnalités du cahier des charges. Elle comprend le démarrage, le schéma SQLite, le panneau `/config`, les sélecteurs de salons/rôles, les arrivées/départs, le pointage de service, les demandes d'absence et une base de tickets. Les tests doivent être exécutés dans l'environnement cible et les interactions doivent être validées sur un serveur de test. Les réponses du staff vers les MP, transferts, notes/transcriptions, planificateur d'absences, sauvegardes automatiques et une partie de l'administration avancée restent à compléter.

## Prérequis

- Python 3.12+
- Une application/bot créé dans le [portail développeur Discord](https://discord.com/developers/applications)
- Un serveur de test où vous pouvez inviter le bot

## Installation

### Linux/VPS
```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```
Modifiez `.env` et renseignez `DISCORD_TOKEN`. Ne partagez jamais ce fichier. Vous pouvez renseigner `DEV_GUILD_ID` pour synchroniser rapidement les commandes sur un serveur de test.

### Portail Discord
1. Créez une application puis ajoutez un bot.
2. Copiez le token dans `.env` (ne le publiez jamais).
3. Dans **Bot > Privileged Gateway Intents**, activez **Server Members Intent** et **Message Content Intent**. Le second sert au relais des réponses en MP.
4. Dans OAuth2 > URL Generator, choisissez les scopes `bot` et `applications.commands`.
5. Autorisez au minimum View Channels, Send Messages, Read Message History, Manage Roles (si attribution de rôles nécessaire) et Use Application Commands. Évitez Administrator.
6. Invitez le bot sur le serveur de test.

### Lancement
```bash
python main.py
```
Les commandes apparaissent dans Discord après synchronisation. Les commandes globales peuvent mettre un peu de temps à se propager.

## Configuration dans Discord

1. Accordez au compte les permissions Administrateur ou définissez d'abord `admin_role_id` dans `guild_config` (une première configuration via SQLite est alors nécessaire).
2. Lancez `/config`.
3. Utilisez **Salons** et **Rôles** pour choisir les valeurs. Les changements sont persistés immédiatement.
4. Configurez `channel_ticket_staff`, `channel_service_logs`, `channel_absence` et les rôles de staff avant les essais.
5. Publiez les panneaux via `/ticket-panneau` et `/service-panneau`.

## Sécurité et données

- SQLite se trouve dans `data/entreprise_bot.sqlite3`.
- Sauvegarde à froid : arrêtez le bot puis copiez ce fichier et ses éventuels fichiers WAL/SHM.
- Stockage des dates : UTC; l'affichage local utilise `TIMEZONE`.
- Vérifiez la hiérarchie des rôles : le rôle du bot doit être placé au-dessus des rôles qu'il attribue/retire.
- Testez toutes les commandes dans un serveur de test avant utilisation professionnelle.

## Tests

```bash
python -m unittest discover -s tests -v
```

Cette commande teste les utilitaires et l'initialisation SQLite. Elle ne remplace pas des tests d'intégration sur un serveur Discord réel.


## Déploiement Railway depuis GitHub

Le fichier `railway.json` demande à Railway de lancer `python main.py`.
Dans Railway, configurez la variable `DISCORD_TOKEN` et, si vous utilisez un volume monté sur `/data`, ajoutez `DATABASE_PATH=/data/entreprise_bot.sqlite3`. Sans volume, les données locales peuvent ne pas survivre à un redéploiement.

Pour les commandes slash, vous pouvez définir `DEV_GUILD_ID` avec l'identifiant du serveur de test. Retirez-la ensuite si vous souhaitez la synchronisation globale.
