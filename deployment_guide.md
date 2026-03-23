# Guide de Déploiement - GesImmeuble Cloud (Render + Supabase)

Ce guide vous explique comment passer de votre environnement local Windows vers un déploiement professionnel dans le Cloud.

## Étape 1 : Préparer GitHub
1. **Initialiser Git** (dans votre terminal) :
   ```powershell
   git init
   git add .
   git commit -m "Initial commit - Ready for Cloud"
   ```
2. **Lier à votre dépôt distant** :
   ```powershell
   git remote add origin https://github.com/hosniadilemp-a11y/block_e.git
   git branch -M main
   git push -u origin main
   ```
WHnKkcAotK9bMDQ2
## Étape 2 : Configurer la base de données sur Supabase
1. Créez un projet sur [Supabase](https://supabase.com/).
2. Allez dans **Project Settings > Database**.
3. Copiez la **Connection String** (format URI/Transaction Mode). Elle ressemble à :
   `postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres`
4. **Initialiser le schéma** :
   - Allez dans le **SQL Editor** de Supabase.
   - Copiez-collez le contenu de votre fichier `schema_postgres.sql` local et exécutez-le.

## Étape 3 : Déploiement sur Render.com
1. Connectez-vous sur [Render](https://render.com/) et liez votre compte GitHub.
2. Cliquez sur **New > Web Service**.
3. Sélectionnez votre dépôt `block_e`.
4. **Configuration** :
   - **Runtime** : Python
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `gunicorn app:app`
5. **Variables d'environnement (Environment Variables)** :
   - Ajoutez `DATABASE_URL` : (La chaîne de connexion Supabase que vous avez copiée).
   - Ajoutez `FLASK_ENV` : `production`

## Étape 4 : Migration des données (Optionnel)
Si vous voulez transférer vos données locales vers Supabase :
1. Modifiez temporairement votre `.env` local avec l'URL Supabase.
2. Exécutez : `python migrate_to_postgres.py`.

---

### Points d'attention
- **Uploads** : Render utilise un système de fichiers éphémère. Vos PDFs uploadés via l'admin disparaîtront au redémarrage du serveur. Pour une solution durable, il faudra utiliser Supabase Storage ou AWS S3 (non inclus dans cette version simple).
- **Sécurité** : Ne partagez jamais votre mot de passe de DB Supabase publiquement.
