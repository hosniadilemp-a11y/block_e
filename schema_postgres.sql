-- PostgreSQL Schema for GesImmeuble

DROP TABLE IF EXISTS logs CASCADE;
DROP TABLE IF EXISTS votes CASCADE;
DROP TABLE IF EXISTS poll_options CASCADE;
DROP TABLE IF EXISTS polls CASCADE;
DROP TABLE IF EXISTS annonces CASCADE;
DROP TABLE IF EXISTS depenses CASCADE;
DROP TABLE IF EXISTS cotisations CASCADE;
DROP TABLE IF EXISTS suggestions_votes CASCADE;
DROP TABLE IF EXISTS suggestions CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS users CASCADE;

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'resident',
    appartement_numero INTEGER,
    nom_complet TEXT,
    telephone TEXT DEFAULT '',
    statut TEXT DEFAULT 'inconnu'
);

CREATE TABLE cotisations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    montant DECIMAL(12, 2) NOT NULL,
    annee INTEGER NOT NULL DEFAULT 2026,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    titre TEXT NOT NULL,
    chemin TEXT NOT NULL,
    categorie TEXT NOT NULL,
    annee INTEGER NOT NULL,
    date_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE depenses (
    id SERIAL PRIMARY KEY,
    description TEXT NOT NULL,
    montant DECIMAL(12, 2) NOT NULL,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    categorie TEXT NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    soldeApres DECIMAL(12, 2) NOT NULL DEFAULT 0,
    document TEXT
);

CREATE TABLE polls (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE poll_options (
    id SERIAL PRIMARY KEY,
    poll_id INTEGER NOT NULL REFERENCES polls(id) ON DELETE CASCADE,
    texte TEXT NOT NULL
);

CREATE TABLE votes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    option_id INTEGER NOT NULL REFERENCES poll_options(id) ON DELETE CASCADE,
    poll_id INTEGER NOT NULL REFERENCES polls(id) ON DELETE CASCADE,
    UNIQUE(user_id, poll_id)
);

CREATE TABLE suggestions (
    id SERIAL PRIMARY KEY,
    titre TEXT NOT NULL,
    description TEXT NOT NULL,
    auteur_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    statut TEXT DEFAULT 'En attente', -- En attente / Approuvee / Rejetee / En cours
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE suggestions_votes (
    id SERIAL PRIMARY KEY,
    suggestion_id INTEGER NOT NULL REFERENCES suggestions(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type_vote TEXT NOT NULL, -- 'up' or 'down'
    UNIQUE(suggestion_id, user_id)
);

CREATE TABLE annonces (
    id SERIAL PRIMARY KEY,
    titre TEXT NOT NULL,
    contenu TEXT NOT NULL,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    chemin_document TEXT,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    details TEXT,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_cotisations_user_id ON cotisations(user_id);
CREATE INDEX IF NOT EXISTS idx_cotisations_annee    ON cotisations(annee);
CREATE INDEX IF NOT EXISTS idx_depenses_date ON depenses(date);
CREATE INDEX IF NOT EXISTS idx_annonces_date ON annonces(date DESC);
CREATE INDEX IF NOT EXISTS idx_logs_date    ON logs(date DESC);
CREATE INDEX IF NOT EXISTS idx_logs_user_id ON logs(user_id);
CREATE INDEX IF NOT EXISTS idx_votes_user_id ON votes(user_id);
CREATE INDEX IF NOT EXISTS idx_votes_poll_id ON votes(poll_id);
CREATE INDEX IF NOT EXISTS idx_suggestions_statut ON suggestions(statut);
CREATE INDEX IF NOT EXISTS idx_poll_options_poll_id ON poll_options(poll_id);
CREATE INDEX IF NOT EXISTS idx_sv_suggestion_id ON suggestions_votes(suggestion_id);
CREATE INDEX IF NOT EXISTS idx_sv_user_id        ON suggestions_votes(user_id);
